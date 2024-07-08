# git_files_comparer.py
import subprocess
import os

def run_command(command, cwd):
    print(f"Running command: {command}")
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True, cwd=cwd)
    if result.returncode != 0:
        raise Exception(f"Command failed: {command}\n{result.stderr}")
    return result.stdout

def compare_files_between_commits(repo_path, commit=None, parent_commit=None):
    if parent_commit is None:
        parent_commit = "HEAD"

    # Create output filename with commit hashes
    output_file = os.path.join('issues', f"changes_{parent_commit}_{commit}.txt")
    
    # Get the list of changed files between the commits
    changed_files = run_command(f"git diff --name-only {parent_commit} {commit if commit else ''}", repo_path).splitlines()
    
    with open(output_file, "w") as f:
        for file in changed_files:
            f.write(f"File: {file}\n")
            
            # Get the file content before the changes
            before_content = run_command(f"git show {parent_commit}:{file}", repo_path)
            f.write("\n--- Before ---\n")
            f.write(before_content)
            
            if commit:
                # Get the file content after the changes
                after_content = run_command(f"git show {commit}:{file}", repo_path)
            else:
                with open(os.path.join(repo_path, file), "r") as file_content:
                 after_content = file_content.read()
            f.write("\n--- After ---\n")
            f.write(after_content)
    
            f.write("\n=============================\n")
    
    result = f"Output written to {output_file}"
    print(result)
    return result

