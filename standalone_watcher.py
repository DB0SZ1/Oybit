import os
import time
import json
import subprocess
import datetime
import requests
# ==========================================
# CONFIGURATION
# ==========================================

# Replace this with your separate API key so it's fully standalone
OPENROUTER_API_KEY = "your_openrouter_api_key_here"  
MODEL = "meta-llama/llama-3.3-70b-instruct:free"

# Git Configuration
GIT_REMOTE = "origin"
GIT_BRANCH = "main"

# Remote Oybit Webhook Configuration (For pushing to your Build-in-Public bot)
# Example: https://db0sz1-oybit.hf.space/api/webhooks/build-log or http://localhost:7860/api/webhooks/build-log
OYBIT_WEBHOOK_URL = "" 
OYBIT_WEBHOOK_SECRET = ""

# Where to append the public log locally (if you don't use the webhook)
BUILD_LOG_PATHS = [
    os.path.join(os.getcwd(), "BUILD_LOG.md")
]
# ==========================================

if not OPENROUTER_API_KEY or OPENROUTER_API_KEY.startswith("your_openrouter_api_key_here"):
    print("Error: Please set your OPENROUTER_API_KEY inside the script.")
    exit(1)

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT).strip()
    except subprocess.CalledProcessError as e:
        return e.output.strip()

def has_changes():
    status = run_cmd("git status --porcelain")
    return len(status) > 0

def get_full_diff():
    # Get both unstaged and staged diffs
    unstaged = run_cmd("git diff")
    staged = run_cmd("git diff --staged")
    return f"STAGED CHANGES:\n{staged}\n\nUNSTAGED CHANGES:\n{unstaged}"

def evaluate_diff(diff_text):
    prompt = f"""You are an expert developer assistant evaluating a git diff. Your job is to decide if the code changes are complete and ready to be committed, or if the developer is still in the middle of typing.

Look for syntax errors, half-finished statements, or hanging trailing commas that indicate incomplete work.
If it IS ready, you must generate a professional commit message and a sanitized, high-level summary for a public 'Build in Public' log.
CRITICAL: The public_log_summary MUST NOT contain any sensitive endpoints, secret keys, specific IP addresses, database columns, or proprietary logic. Describe it functionally (e.g. 'Added user authentication endpoints' instead of 'Added POST /api/v1/auth/login').

Return EXACTLY and ONLY valid JSON matching this schema:
{{
  "is_ready": true or false,
  "reasoning": "Short explanation of why it's ready or not.",
  "commit_message": "Short, clear commit message",
  "public_log_summary": "High-level, sanitized summary of what was built (safe for public eyes)."
}}

DIFF:
{diff_text}
"""
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"}
    }
    
    print(f"[*] Asking LLM ({MODEL}) to evaluate changes...")
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
        if response.status_code != 200:
            print(f"[!] API Error: {response.status_code} - {response.text}")
            return None
            
        result_text = response.json()['choices'][0]['message']['content']
        # Clean up in case of markdown wrapping
        if result_text.startswith("```json"):
            result_text = result_text[7:-3]
        elif result_text.startswith("```"):
            result_text = result_text[3:-3]
            
        return json.loads(result_text.strip())
    except Exception as e:
        print(f"[!] Error calling LLM: {e}")
        return None

def append_to_build_log(summary):
    if OYBIT_WEBHOOK_URL and OYBIT_WEBHOOK_SECRET:
        print(f"[*] Pushing log to Oybit remote webhook at {OYBIT_WEBHOOK_URL}...")
        try:
            resp = requests.post(
                OYBIT_WEBHOOK_URL,
                json={"summary": summary},
                headers={"Authorization": f"Bearer {OYBIT_WEBHOOK_SECRET}"},
                timeout=15
            )
            if resp.status_code == 200:
                print("[+] Remote push successful!")
            else:
                print(f"[!] Remote push failed: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"[!] Remote push error: {e}")
        return

    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"## [{date_str}] - Auto Commit\n"
    entry += "**Tags**: #BuildInPublic #Engineering\n"
    entry += "**Details**:\n"
    entry += f"{summary}\n\n"

    for path in BUILD_LOG_PATHS:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            marker = "## UNPOSTED PROGRESS\n*(New entries will be automatically appended here by the Git Hook)*\n"
            if marker in content:
                content = content.replace(marker, marker + "\n" + entry)
            else:
                marker_alt = "## UNPOSTED PROGRESS"
                content = content.replace(marker_alt, marker_alt + "\n\n" + entry)
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[*] Updated local build log at {path}")

def main():
    print(f"=== Auto Watcher Started ({datetime.datetime.now()}) ===")
    print("Watching for changes every 60 seconds...")
    
    while True:
        try:
            if has_changes():
                print("\n[*] Detected changes. Waiting 10s to ensure you're done typing...")
                time.sleep(10)
                
                diff = get_full_diff()
                if not diff.strip() or diff.strip() == "STAGED CHANGES:\n\n\nUNSTAGED CHANGES:":
                    print("[-] False alarm. No actual diff content.")
                    time.sleep(50)
                    continue
                    
                # Evaluate with LLM
                decision = evaluate_diff(diff)
                
                if decision:
                    if decision.get("is_ready"):
                        print(f"[+] LLM Decision: READY ({decision.get('reasoning')})")
                        print(f"[*] Commit Message: {decision.get('commit_message')}")
                        
                        # Execute Git Commands
                        print("[*] Running git add .")
                        run_cmd("git add .")
                        
                        # Need to escape quotes in commit message
                        msg = decision.get('commit_message').replace('"', '\\"')
                        print(f"[*] Running git commit -m \"{msg}\"")
                        run_cmd(f'git commit -m "{msg}"')
                        
                        print(f"[*] Running git push {GIT_REMOTE} {GIT_BRANCH}")
                        run_cmd(f"git push {GIT_REMOTE} {GIT_BRANCH}")
                        
                        # Log it securely
                        append_to_build_log(decision.get('public_log_summary'))
                        print("[+] Finished committing and logging successfully!")
                    else:
                        print(f"[-] LLM Decision: NOT READY ({decision.get('reasoning')})")
                        print("[-] Skipping commit.")
                else:
                    print("[!] Failed to get valid decision from LLM. Skipping.")
                
                # Wait longer after processing to avoid spamming
                print("\n[*] Sleeping for 60 seconds...")
                time.sleep(60)
            else:
                time.sleep(10) # check more frequently if no changes
                
        except KeyboardInterrupt:
            print("\n[*] Shutting down Auto Watcher.")
            break
        except Exception as e:
            print(f"\n[!] Unexpected Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
