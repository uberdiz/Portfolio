"""
Fixer Agent - Analyzes errors and suggests fixes
"""
import os
import json
from core.llm import call_llm

def fixer_agent(project_path, file_paths, error_log, api_url, model):
    """
    Analyze errors and suggest fixes
    
    Args:
        project_path: Path to the project
        file_paths: List of files to analyze
        error_log: Error output from running the script
        api_url: LLM API URL
        model: LLM model name
    """
    # Read the files
    files_content = {}
    for file_path in file_paths:
        full_path = os.path.join(project_path, file_path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                files_content[file_path] = f.read()
        except:
            files_content[file_path] = ""
    
    # Create the prompt for fixing
    prompt = create_fix_prompt(files_content, error_log)
    
    # Get AI response
    response = call_llm(prompt, api_url, model)
    
    # Parse the response
    fixes = parse_fix_response(response)
    
    return fixes

def create_fix_prompt(files_content, error_log):
    """Create a prompt for fixing errors"""
    prompt = """Analyze these errors and suggest fixes:
    ERROR LOG:{error_log}
FILES TO FIX:
"""
    
    for file_path, content in files_content.items():
        prompt += f"\n--- {file_path} ---\n{content[:2000]}\n"
    
    prompt += """
INSTRUCTIONS:
1. Analyze each error and identify the root cause
2. For each file that needs changes, provide the corrected version
3. Return your response as JSON in this format:
{
  "analysis": "Brief explanation of the errors",
  "fixes": {
    "filename1.py": "full corrected content here",
    "filename2.py": "full corrected content here"
  }
}

IMPORTANT: Only return the JSON, no additional text."""
    
    return prompt.format(error_log=error_log)

def parse_fix_response(response):
    """Parse the AI response to extract fixes"""
    try:
        # Try to find JSON in the response
        start = response.find('{')
        end = response.rfind('}') + 1
        
        if start >= 0 and end > start:
            json_str = response[start:end]
            result = json.loads(json_str)
            return result.get("fixes", {})
    except:
        pass
    
    return {}