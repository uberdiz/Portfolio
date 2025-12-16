"""
Dependency Management
"""
import subprocess
import sys
import pkg_resources
import os

def check_dependency(package_name):
    """Check if package is installed"""
    try:
        pkg_resources.get_distribution(package_name)
        return True
    except:
        return False

def install_dependency(package_name):
    """Install a package"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except:
        return False

def get_installed_packages():
    """Get list of installed packages"""
    installed = []
    for dist in pkg_resources.working_set:
        installed.append(dist.key)
    return installed

def check_project_dependencies(project_path):
    """Check project dependencies from requirements.txt"""
    req_file = os.path.join(project_path, "requirements.txt")
    missing = []
    
    if os.path.exists(req_file):
        with open(req_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Parse package name (remove version specifiers)
                    package_name = line.split('==')[0].split('>=')[0].split('<=')[0].strip()
                    if not check_dependency(package_name):
                        missing.append(package_name)
    
    return missing

def generate_requirements(project_path, packages):
    """Generate requirements.txt file"""
    req_file = os.path.join(project_path, "requirements.txt")
    with open(req_file, 'w') as f:
        for package in packages:
            f.write(f"{package}\n")