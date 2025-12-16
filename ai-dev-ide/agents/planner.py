"""
Planner Agent - Creates project plans
"""
import json
from core.llm import call_llm

def planner_agent(prompt, api_url, model):
    """
    Create a project plan based on user prompt
    
    Args:
        prompt: User's project description
        api_url: LLM API URL
        model: LLM model name
    """
    system_prompt = """You are a senior software architect. Create a detailed project plan with:
1. Project structure
2. List of files needed
3. Dependencies required
4. Implementation steps
5. Testing strategy

Return as JSON with this structure:
{
  "project_name": "name",
  "description": "brief description",
  "files": ["main.py", "utils.py", ...],
  "dependencies": ["package1", "package2"],
  "architecture": "description",
  "steps": ["step1", "step2"]
}"""
    
    full_prompt = f"{system_prompt}\n\nUser request: {prompt}"
    
    response = call_llm(full_prompt, api_url, model)
    
    try:
        # Try to extract JSON from response
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            plan_json = response[start:end]
            plan = json.loads(plan_json)
        else:
            # Fallback to creating a basic plan
            plan = create_basic_plan(prompt)
    except:
        plan = create_basic_plan(prompt)
    
    return plan

def create_basic_plan(prompt):
    """Create a basic plan if LLM fails"""
    return {
        "project_name": prompt[:30],
        "description": f"Project based on: {prompt}",
        "files": ["main.py", "utils.py", "config.py", "README.md"],
        "dependencies": [],
        "architecture": "Modular Python application",
        "steps": ["Setup project structure", "Implement core logic", "Add tests", "Create documentation"]
    }