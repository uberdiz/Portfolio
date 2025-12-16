"""
Git Operations
"""
import os
import subprocess

def git_init_and_push(project_path, remote_url, commit_message="Initial commit"):
    """Initialize git repo and push to remote"""
    try:
        # Initialize git
        subprocess.run(["git", "init"], cwd=project_path, check=True)
        subprocess.run(["git", "add", "."], cwd=project_path, check=True)
        subprocess.run(["git", "commit", "-m", commit_message], cwd=project_path, check=True)
        subprocess.run(["git", "branch", "-M", "main"], cwd=project_path, check=True)
        subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=project_path, check=True)
        subprocess.run(["git", "push", "-u", "origin", "main"], cwd=project_path, check=True)
        return True
    except subprocess.CalledProcessError as e:
        return False

def git_add_remote(project_path, remote_name, remote_url):
    """Add git remote"""
    try:
        subprocess.run(["git", "remote", "add", remote_name, remote_url], 
                      cwd=project_path, check=True)
        return True
    except:
        return False

def git_commit(project_path, message):
    """Commit changes"""
    try:
        subprocess.run(["git", "add", "."], cwd=project_path, check=True)
        subprocess.run(["git", "commit", "-m", message], cwd=project_path, check=True)
        return True
    except:
        return False

def git_pull(project_path):
    """Pull latest changes"""
    try:
        subprocess.run(["git", "pull"], cwd=project_path, check=True)
        return True
    except:
        return False

def git_status(project_path):
    """Get git status"""
    try:
        result = subprocess.run(["git", "status", "--porcelain"], 
                              cwd=project_path, capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return ""