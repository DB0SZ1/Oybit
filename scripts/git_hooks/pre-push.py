#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
import subprocess
from datetime import datetime

# Path resolution to load the .env from the linkedin backend folder
repo_root = subprocess.check_output(['git', 'rev-parse', '--show-toplevel']).strip().decode('utf-8')
env_path = os.path.join(repo_root, "linkedin", ".env")
build_log_path = os.path.join(repo_root, "linkedin", "BUILD_LOG.md")

def load_env():
    if not os.path.exists(env_path):
        return {}
    env_vars = {}
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, _, value = line.partition("=")
                env_vars[key.strip()] = value.strip()
    return env_vars

def get_git_diff():
    """Gets the diff of the commits about to be pushed."""
    try:
        # Get diff between current HEAD and origin tracking branch
        diff = subprocess.check_output(['git', 'diff', '@{u}..HEAD']).strip().decode('utf-8')
        return diff
    except Exception:
        # Fallback if no upstream is set or error
        return subprocess.check_output(['git', 'show', 'HEAD']).strip().decode('utf-8')

def summarize_diff_with_llm(diff: str, api_key: str, model: str) -> str:
    """Uses LLM to summarize the code diff."""
    if not diff:
        return "No significant changes."
        
    # Truncate diff if it's too massive
    diff = diff[:4000]

    system_prompt = """You are a senior engineer's assistant. 
Your job is to read a git diff and summarize the technical progress in 2-4 plain-English bullet points.
Focus on WHAT was built and the PROBLEM it solved, not the exact line-by-line syntax.
Do not use markdown bolding. Just plain bullet points."""

    user_prompt = f"Summarize this git diff:\n\n{diff}"

    data = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 300,
        "temperature": 0.5
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://oybit.nyvora.com",
            "Content-Type": "application/json",
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode())
            return res_data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"⚠️ [Git Hook] Failed to summarize diff: {e}")
        return "Refactored code and shipped latest commits."

def append_to_build_log(summary: str):
    if not os.path.exists(build_log_path):
        print(f"⚠️ [Git Hook] BUILD_LOG.md not found at {build_log_path}")
        return

    with open(build_log_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Create the new entry
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = f"### [{timestamp}] - Automated Push Summary\n{summary}\n\n"

    # Insert it right below the UNPOSTED PROGRESS heading
    target_heading = "## UNPOSTED PROGRESS"
    if target_heading in content:
        parts = content.split(target_heading, 1)
        new_content = parts[0] + target_heading + "\n" + new_entry + parts[1].lstrip()
        
        with open(build_log_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"✅ [Git Hook] Code summarized and appended to BUILD_LOG.md!")
    else:
        print("⚠️ [Git Hook] '## UNPOSTED PROGRESS' section not found in BUILD_LOG.md")


if __name__ == "__main__":
    print("🤖 [Git Hook] Intercepting push to generate Build Log summary...")
    
    env = load_env()
    api_key = env.get("OPENROUTER_API_KEY")
    model = env.get("OPENROUTER_DEFAULT_MODEL", "google/gemini-2.5-flash")
    
    if not api_key:
        print("⚠️ [Git Hook] OPENROUTER_API_KEY not found. Skipping auto-summary.")
        sys.exit(0)
        
    diff = get_git_diff()
    if diff:
        summary = summarize_diff_with_llm(diff, api_key, model)
        append_to_build_log(summary)
    
    # We exit 0 so the push continues successfully!
    sys.exit(0)
