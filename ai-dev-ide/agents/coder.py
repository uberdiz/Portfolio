"""
Coder Agent - Generates code files
"""
import os
import json
from core.llm import call_llm
from core.project_state import PROJECT_STATE

def coder_agent(project_path, api_url, model):
    """
    Generate code for planned project files
    
    Args:
        project_path: Path to project
        api_url: LLM API URL
        model: LLM model name
    """
    plan = PROJECT_STATE.get('plan', {})
    files_to_create = plan.get('files', ['main.py'])
    
    for file_name in files_to_create:
        # Skip if file already exists with content
        full_path = os.path.join(project_path, file_name)
        if os.path.exists(full_path) and os.path.getsize(full_path) > 100:
            continue
            
        # Generate code for this file
        code = generate_file_code(file_name, plan, api_url, model)
        
        # Save file
        save_code_file(project_path, file_name, code)

def generate_file_code(file_name, plan, api_url, model):
    """Generate code for a specific file"""
    prompt = f"""Generate code for file: {file_name}
    
Project Plan:
{json.dumps(plan, indent=2)}

Requirements:
1. Write complete, working code
2. Include proper imports
3. Add comments for complex logic
4. Follow PEP 8 style guide
5. Handle edge cases

Only return the code, no explanations."""
    
    return call_llm(prompt, api_url, model)

def save_code_file(project_path, file_name, code):
    """Save generated code to file"""
    full_path = os.path.join(project_path, file_name)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(code)