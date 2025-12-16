"""
LLM Interface - Unified interface for multiple AI providers
"""
import requests
import json
import time

def call_llm(prompt, api_url, model, api_provider="ollama", **kwargs):
    """
    Call LLM with unified interface
    
    Args:
        prompt: The prompt to send
        api_url: API endpoint URL
        model: Model name
        api_provider: Provider type (ollama, huggingface, etc.)
        **kwargs: Provider-specific parameters
    """
    if api_provider == "ollama":
        return call_ollama(prompt, api_url, model)
    elif api_provider == "huggingface":
        return call_huggingface(prompt, api_url, model, **kwargs)
    else:
        raise ValueError(f"Unsupported provider: {api_provider}")

def call_ollama(prompt, api_url, model):
    """Call Ollama API"""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "num_predict": 4000
        }
    }
    
    try:
        response = requests.post(
            api_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "")
        else:
            return f"Ollama API error {response.status_code}: {response.text}"
            
    except Exception as e:
        return f"Ollama connection error: {str(e)}"

def call_huggingface(prompt, api_url, model, token=None):
    """Call Hugging Face Inference API"""
    if not token:
        return "Hugging Face token required"
    
    # Use router.huggingface.co for inference
    inference_url = "https://router.huggingface.co/hf-inference"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 2000,
            "temperature": 0.7,
            "top_p": 0.95,
            "return_full_text": False
        }
    }
    
    try:
        response = requests.post(
            f"{inference_url}/{model}",
            json=payload,
            headers=headers,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("generated_text", "")
            return str(result)
        else:
            return f"Hugging Face API error {response.status_code}: {response.text}"
            
    except Exception as e:
        return f"Hugging Face connection error: {str(e)}"

def test_llm_connection(api_provider, api_url, model, token=None):
    """Test LLM connection"""
    test_prompt = "Respond with 'Hello, world!' to confirm the connection is working."
    
    try:
        response = call_llm(
            test_prompt,
            api_url,
            model,
            api_provider=api_provider,
            token=token
        )
        
        if "Hello" in response or "hello" in response:
            return True, response
        else:
            return False, f"Unexpected response: {response[:100]}"
            
    except Exception as e:
        return False, str(e)