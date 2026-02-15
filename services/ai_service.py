import os
import requests
import json
from typing import Optional, Dict, Any

# Load environment variables (assuming they are loaded in main.py or automatically by python-dotenv)
API_KEY = os.getenv("SUPER_MIND_API_KEY")
BASE_URL = "https://space.ai-builders.com/backend/v1"

if not API_KEY:
    raise ValueError("SUPER_MIND_API_KEY is not set in environment variables")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}

def transcribe_audio(file_path: str) -> str:
    """
    Transcribes audio file using AI-builders API.
    """
    url = f"{BASE_URL}/audio/transcriptions"
    
    with open(file_path, "rb") as f:
        files = {"audio_file": (os.path.basename(file_path), f)}
        # Optional: Add language hint if needed, e.g. "zh" for Chinese
        # data = {"language": "zh"} 
        response = requests.post(url, headers=HEADERS, files=files)
    
    if response.status_code != 200:
        raise Exception(f"Transcription failed: {response.text}")
    
    return response.json().get("text", "")

def process_event_text(text: str) -> Dict[str, Any]:
    """
    Extracts event details (title, start_time, end_time) from text.
    Returns a JSON object.
    """
    prompt = f"""
    Analyze the following text and extract event details.
    Text: "{text}"
    
    Return a JSON object with the following keys:
    - title: A concise title for the event.
    - start_time: The start time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS). If the year is not specified, assume the current year (2026).
    - end_time: The end time in ISO 8601 format, or null if not specified.
    - description: Any additional details found in the text.
    
    If the text contains relative dates (e.g., "tomorrow", "next Friday"), calculate the date assuming today is {os.getenv("TODAY_DATE", "2026-01-18")}.
    If the majority of the text is in Chinese, the content and title should be in Chinese.
    Return ONLY the JSON object, no markdown formatting.
    """
    
    return _get_chat_completion(prompt)

def process_idea_text(text: str) -> Dict[str, Any]:
    """
    Summarizes an idea and structures it.
    Returns a JSON object.
    """
    prompt = f"""
    Analyze the following text which is a raw idea or thought.
    Text: "{text}"
    
    Return a JSON object with the following keys:
    - title: A very concise summary (3-5 words) to be used as a page title.
    - content: A well-structured description/narrative of the idea. Use markdown formatting (bullet points, bold text) within this string to make it readable. Organize the chaotic thoughts into logical blocks.
    - If the majority of the text is in Chinese, the content and title should be in Chinese.
    - tags: A list of 1-3 relevant keywords/tags.
    
    Return ONLY the JSON object, no markdown formatting.
    """
    
    return _get_chat_completion(prompt)

def _get_chat_completion(prompt: str) -> Dict[str, Any]:
    url = f"{BASE_URL}/chat/completions"
    
    payload = {
        "model": "supermind-agent-v1",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that processes text into structured JSON data. You must always return valid JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        # Remove response_format for gemini-3-flash-preview as it might be causing empty responses if strict mode fails
        # "response_format": {"type": "json_object"} 
    }
    
    response = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=payload)
    
    if response.status_code != 200:
        # Fallback to standard request if json_object format is not supported by the proxy or model specifically
        del payload["response_format"]
        response = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"AI processing failed: {response.text}")

    result = response.json()
    print(f"DEBUG: AI Response: {json.dumps(result, indent=2)}")
    
    if not result.get("choices") or not result["choices"][0].get("message"):
        raise Exception(f"Invalid AI response structure: {result}")

    content = result["choices"][0]["message"].get("content")
    
    if not content:
        raise Exception(f"AI returned empty content. Full response: {result}")
    
    print(f"DEBUG: Raw content: {content!r}")

    # Clean up potential markdown code blocks
    clean_content = content.strip()
    if clean_content.startswith("```json"):
        clean_content = clean_content[7:]
    elif clean_content.startswith("```"):
        clean_content = clean_content[3:]
    
    if clean_content.endswith("```"):
        clean_content = clean_content[:-3]
        
    clean_content = clean_content.strip()
    
    try:
        return json.loads(clean_content)
    except json.JSONDecodeError:
        print(f"ERROR: Failed to parse JSON. Content was: {clean_content!r}")
        raise Exception(f"Failed to parse JSON response: {content}")
