import os
import requests
import json
from typing import Dict, Any, List

NOTION_TOKEN = os.getenv("NOTION_TOKEN") or os.getenv("NOTION_API_KEY")
AGENDA_DB_ID = os.getenv("AGENDA_DATABASE_ID")
JOURNAL_DB_ID = os.getenv("JOURNAL_DATABASE_ID")

BASE_URL = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

if not NOTION_TOKEN:
    raise ValueError("NOTION_API_KEY is not set")

def create_event(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a page in the Agenda database.
    data expected keys: title, start_time, end_time (optional), description (optional)
    """
    if not AGENDA_DB_ID:
        raise ValueError("AGENDA_DATABASE_ID is not set")
        
    properties = {
        "Name": {
            "title": [
                {
                    "text": {
                        "content": data.get("title", "New Event")
                    }
                }
            ]
        },
        "Date": {
            "date": {
                "start": data.get("start_time")
            }
        }
    }
    
    if data.get("end_time"):
        properties["Date"]["date"]["end"] = data.get("end_time")
        
    children = []
    if data.get("description"):
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": data.get("description")
                        }
                    }
                ]
            }
        })
        
    payload = {
        "parent": {"database_id": AGENDA_DB_ID},
        "properties": properties,
        "children": children
    }
    
    return _create_page(payload)

def create_journal(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a page in the Journal database.
    data expected keys: title, content (markdown string)
    """
    if not JOURNAL_DB_ID:
        raise ValueError("JOURNAL_DATABASE_ID is not set")
        
    properties = {
        "Name": {
            "title": [
                {
                    "text": {
                        "content": data.get("title", "New Idea")
                    }
                }
            ]
        }
    }
    
    # We need to convert the content string (which might be markdown-like) into blocks.
    # For simplicity, we'll split by newlines and create paragraphs, 
    # but a real implementation might want a markdown-to-blocks parser.
    # Here we will just dump the content as one or more paragraphs.
    
    content_text = data.get("content", "")
    children = []
    
    # Simple markdown-ish parsing
    lines = content_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith("- "):
            children.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                }
            })
        elif line.startswith("# "):
             children.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                }
            })
        elif line.startswith("## "):
             children.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": line[3:]}}]
                }
            })
        else:
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": line}}]
                }
            })

    payload = {
        "parent": {"database_id": JOURNAL_DB_ID},
        "properties": properties,
        "children": children
    }
    
    return _create_page(payload)

def _create_page(payload: Dict[str, Any]) -> Dict[str, Any]:
    response = requests.post(f"{BASE_URL}/pages", headers=HEADERS, json=payload)
    
    if response.status_code != 200:
        raise Exception(f"Notion API Error: {response.text}")
        
    return response.json()
