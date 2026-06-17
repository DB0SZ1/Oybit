import os
import sys
import shutil

HOOK_TEMPLATE = """#!/usr/bin/env python
import sys
import os
import subprocess

def main():
    # Read from stdin
    lines = sys.stdin.readlines()
    if not lines:
        return

    # Usually one line per ref pushed
    for line in lines:
        parts = line.strip().split()
        if len(parts) < 4:
            continue
        
        local_ref, local_sha, remote_ref, remote_sha = parts
        
        # If new branch, remote_sha is 0000000000000000000000000000000000000000
        if remote_sha.replace('0', '') == '':
            range_str = local_sha + " -n 1"  # just take the latest commit for a new branch
        else:
            range_str = f"{remote_sha}..{local_sha}"

        try:
            # Get the commit message
            log_output = subprocess.check_output(f"git log {range_str} --oneline", shell=True, text=True).strip()
            
            # Get the diff summary
            diff_output = subprocess.check_output(f"git diff {range_str} --stat", shell=True, text=True).strip()
            
            if not log_output:
                continue

            # Format the output
            import datetime
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            
            # Extract Repo name for context
            repo_name = os.path.basename(os.getcwd())

            entry = f"## [{date_str}] - Pushed Commits ({repo_name} Repo)\\n"
            entry += "**Tags**: #BuildInPublic #Engineering\\n"
            entry += "**Details**:\\n"
            entry += f"Commits:\\n{log_output}\\n\\n"
            entry += f"Diff Summary:\\n{diff_output}\\n\\n"

            # Absolute path to the central BUILD_LOG.md
            build_log_path = r"{central_log_path}"
            
            if os.path.exists(build_log_path):
                with open(build_log_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Insert right after ## UNPOSTED PROGRESS
                marker = "## UNPOSTED PROGRESS\\n*(New entries will be automatically appended here by the Git Hook)*\\n"
                if marker in content:
                    content = content.replace(marker, marker + "\\n" + entry)
                else:
                    marker_alt = "## UNPOSTED PROGRESS"
                    content = content.replace(marker_alt, marker_alt + "\\n\\n" + entry)
                
                with open(build_log_path, "w", encoding="utf-8") as f:
                    f.write(content)
                    
        except Exception as e:
            print(f"Error in Oybit pre-push hook: {e}")

if __name__ == "__main__":
    main()
"""

def install_hook():
    print("🚀 Welcome to the Oybit BIP Git Hook Installer")
    print("This will install the tracker so other repos sync with Oybit's BUILD_LOG.\\n")
    
    target_repo = input("Enter the absolute path to the target repository (e.g. C:\\Projects\\MyOtherApp): ").strip()
    
    if not os.path.exists(target_repo):
        print("❌ Error: That path does not exist.")
        return
        
    git_dir = os.path.join(target_repo, ".git")
    if not os.path.exists(git_dir):
        print("❌ Error: That folder is not a Git repository (missing .git folder).")
        return
        
    hooks_dir = os.path.join(git_dir, "hooks")
    if not os.path.exists(hooks_dir):
        os.makedirs(hooks_dir, exist_ok=True)
        
    hook_file = os.path.join(hooks_dir, "pre-push")
    
    central_log_path = r"C:\Users\IDRIS\Desktop\Oybit\linkedin\BUILD_LOG.md"
    hook_code = HOOK_TEMPLATE.replace("{central_log_path}", central_log_path)
    
    with open(hook_file, "w", encoding="utf-8") as f:
        f.write(hook_code)
        
    print(f"\\n✅ Successfully installed Git Hook at: {hook_file}")
    print(f"Whenever you 'git push' in '{target_repo}', the logs will go to Oybit's BUILD_LOG.md!")

if __name__ == "__main__":
    install_hook()
