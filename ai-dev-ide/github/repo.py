"""
GitHub Repository Operations
"""
import os
from github import Github
from github import Auth

def create_github_repo(token, repo_name, description="", private=False):
    """Create a new GitHub repository"""
    try:
        auth = Auth.Token(token)
        g = Github(auth=auth)
        user = g.get_user()
        repo = user.create_repo(repo_name, description=description, private=private)
        return repo.clone_url
    except Exception as e:
        raise Exception(f"Failed to create repo: {e}")

def get_user_repos(token):
    """Get user's repositories"""
    try:
        auth = Auth.Token(token)
        g = Github(auth=auth)
        user = g.get_user()
        return [repo.name for repo in user.get_repos()]
    except Exception as e:
        return []

def delete_github_repo(token, repo_name):
    """Delete a GitHub repository"""
    try:
        auth = Auth.Token(token)
        g = Github(auth=auth)
        user = g.get_user()
        repo = user.get_repo(repo_name)
        repo.delete()
        return True
    except:
        return False