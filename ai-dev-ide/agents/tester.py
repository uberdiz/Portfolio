"""
Tester Agent - Generates tests
"""
import os
import json
from core.llm import call_llm

def tester_agent(project_path, api_url, model):
    """
    Generate tests for project
    
    Args:
        project_path: Path to project
        api_url: LLM API URL
        model: LLM model name
    """
    # Find Python files
    python_files = []
    for root, dirs, files in os.walk(project_path):
        for file in files:
            if file.endswith('.py') and not file.startswith('test_'):
                python_files.append(os.path.join(root, file))
    
    for py_file in python_files:
        generate_tests_for_file(py_file, project_path, api_url, model)

def generate_tests_for_file(file_path, project_path, api_url, model):
    """Generate tests for a specific file"""
    # Read the file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
    except:
        return
    
    prompt = f"""Generate comprehensive pytest tests for this Python code:

{code_content}

Requirements:
1. Create test file with name test_{os.path.basename(file_path)}
2. Test all functions and classes
3. Include edge cases
4. Use pytest fixtures where appropriate
5. Add setup and teardown if needed
6. Include docstrings for test functions

Return only the test code, no explanations."""
    
    tests = call_llm(prompt, api_url, model)
    
    # Save test file
    test_file_name = f"test_{os.path.basename(file_path)}"
    test_file_path = os.path.join(os.path.dirname(file_path), test_file_name)
    
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(tests)