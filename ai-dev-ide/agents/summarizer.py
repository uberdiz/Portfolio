"""
Summarizer Agent - Creates project summaries and updates documentation
"""
import os
import json
from core.llm import call_llm

def summarizer_agent(project_path, api_url, model):
    """
    Create a project summary and update documentation files
    
    Args:
        project_path: Path to the project
        api_url: LLM API URL
        model: LLM model name
    """
    # Gather project information
    project_info = gather_project_info(project_path)
    
    # Generate summaries using AI
    readme_content = generate_readme(project_info, api_url, model)
    portfolio_content = generate_portfolio(project_info, api_url, model)
    
    # Save the files
    save_summary_files(project_path, readme_content, portfolio_content)
    
    return {
        "readme_updated": True,
        "portfolio_updated": True,
        "project_info": project_info
    }

def gather_project_info(project_path):
    """Gather information about the project"""
    info = {
        "name": os.path.basename(project_path),
        "files": [],
        "python_files": [],
        "total_lines": 0,
        "main_technologies": [],
        "dependencies": []
    }
    
    # Walk through project directory
    for root, dirs, files in os.walk(project_path):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, project_path)
            
            info["files"].append(rel_path)
            
            if file.endswith('.py'):
                info["python_files"].append(rel_path)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        info["total_lines"] += len(lines)
                        
                        # Extract imports for dependencies
                        for line in lines[:50]:  # Check first 50 lines for imports
                            line = line.strip()
                            if line.startswith('import ') or line.startswith('from '):
                                info["dependencies"].append(line)
                except:
                    pass
    
    # Get unique dependencies
    info["dependencies"] = list(set(info["dependencies"]))
    
    # Try to detect main technologies
    detect_technologies(info, project_path)
    
    return info

def detect_technologies(info, project_path):
    """Detect main technologies used in the project"""
    tech_indicators = {
        'web': ['flask', 'django', 'fastapi', 'streamlit'],
        'data': ['pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch'],
        'database': ['sqlalchemy', 'psycopg2', 'mysql', 'sqlite'],
        'testing': ['pytest', 'unittest', 'nose'],
        'async': ['asyncio', 'aiohttp', 'asyncpg']
    }
    
    detected = set()
    
    # Check file names and content for technology indicators
    for file in info["files"]:
        file_lower = file.lower()
        for tech, indicators in tech_indicators.items():
            for indicator in indicators:
                if indicator in file_lower:
                    detected.add(tech)
                    break
    
    info["main_technologies"] = list(detected)

def generate_readme(project_info, api_url, model):
    """Generate README.md content"""
    prompt = f"""Create a comprehensive README.md for the project: {project_info['name']}

Project Information:
- Files: {len(project_info['files'])} total, {len(project_info['python_files'])} Python files
- Total lines of code: {project_info['total_lines']}
- Main technologies: {', '.join(project_info['main_technologies'])}
- Key dependencies: {', '.join(project_info['dependencies'][:10])}

Structure the README with:
1. Project title and brief description
2. Features
3. Installation instructions
4. Usage examples
5. Project structure overview
6. Contributing guidelines
7. License information

Make it professional and suitable for GitHub."""
    
    return call_llm(prompt, api_url, model)

def generate_portfolio(project_info, api_url, model):
    """Generate PORTFOLIO.md content"""
    prompt = f"""Create a portfolio-style documentation for the project: {project_info['name']}

Project Information:
- Files: {len(project_info['files'])} total, {len(project_info['python_files'])} Python files
- Main technologies: {', '.join(project_info['main_technologies'])}
- Key features: {', '.join(project_info['dependencies'][:5])}

Structure the portfolio with:
1. Project overview and business value
2. Technical architecture
3. Key challenges and solutions
4. Performance metrics
5. Lessons learned
6. Future improvements
7. Screenshots/code snippets (use markdown placeholders)

Make it showcase-worthy for developer portfolios."""
    
    return call_llm(prompt, api_url, model)

def save_summary_files(project_path, readme_content, portfolio_content):
    """Save the generated summary files"""
    # Save README.md
    readme_path = os.path.join(project_path, "README.md")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    # Save PORTFOLIO.md
    portfolio_path = os.path.join(project_path, "PORTFOLIO.md")
    with open(portfolio_path, 'w', encoding='utf-8') as f:
        f.write(portfolio_content)
    
    return {
        "readme_path": readme_path,
        "portfolio_path": portfolio_path
    }