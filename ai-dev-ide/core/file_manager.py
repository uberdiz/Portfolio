"""
File Management Utilities
"""
import os
import json
import hashlib

class FileManager:
    def __init__(self):
        self.file_cache = {}
        self.file_hashes = {}

    def read_file(self, file_path):
        """Read file with caching"""
        if file_path in self.file_cache:
            return self.file_cache[file_path]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.file_cache[file_path] = content
                self.file_hashes[file_path] = self.calculate_hash(content)
                return content
        except:
            return ""

    def write_file(self, file_path, content):
        """Write file and update cache"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.file_cache[file_path] = content
            self.file_hashes[file_path] = self.calculate_hash(content)
            return True
        except Exception as e:
            return False

    def calculate_hash(self, content):
        """Calculate content hash"""
        return hashlib.md5(content.encode()).hexdigest()

    def has_changed(self, file_path):
        """Check if file has changed"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
                current_hash = self.calculate_hash(current_content)
                return self.file_hashes.get(file_path) != current_hash
        except:
            return True

    def find_files(self, directory, extensions=None):
        """Find files with specific extensions"""
        files = []
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                if extensions:
                    if any(filename.endswith(ext) for ext in extensions):
                        files.append(os.path.join(root, filename))
                else:
                    files.append(os.path.join(root, filename))
        return files

    def create_project_structure(self, base_path, structure):
        """Create project directory structure"""
        for item in structure:
            if item.endswith('/'):
                # It's a directory
                os.makedirs(os.path.join(base_path, item), exist_ok=True)
            else:
                # It's a file
                file_path = os.path.join(base_path, item)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                if not os.path.exists(file_path):
                    with open(file_path, 'w') as f:
                        f.write('')