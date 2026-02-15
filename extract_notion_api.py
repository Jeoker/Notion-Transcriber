import requests
import json
import time
import os

# ================= 配置区域 =================
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"  # 使用稳定的 API 版本
}
# ===========================================

def get_all_authorized_pages():
    """
    使用 Search API 获取所有授权的页面（元数据）
    """
    url = "https://api.notion.com/v1/search"
    payload = {"filter": {"value": "page", "property": "object"}}
    results = []
    has_more = True
    next_cursor = None

    print("正在搜索授权页面...")
    
    while has_more:
        body = payload.copy()
        if next_cursor:
            body["start_cursor"] = next_cursor
            
        response = requests.post(url, json=body, headers=HEADERS)
        if response.status_code != 200:
            print(f"搜索失败: {response.text}")
            break
            
        data = response.json()
        results.extend(data["results"])
        has_more = data["has_more"]
        next_cursor = data["next_cursor"]
        
    print(f"找到 {len(results)} 个页面。")
    return results

def get_page_blocks(block_id):
    """
    获取某个页面或 Block 下的所有子 Block（即页面内容）
    """
    url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    results = []
    has_more = True
    next_cursor = None
    
    while has_more:
        params = {}
        if next_cursor:
            params["start_cursor"] = next_cursor
            
        response = requests.get(url, headers=HEADERS, params=params)
        
        # 处理速率限制或错误
        if response.status_code == 429:
            print("触发速率限制，暂停 5 秒...")
            time.sleep(5)
            continue
        elif response.status_code != 200:
            print(f"获取内容失败 (ID: {block_id}): {response.text}")
            break
            
        data = response.json()
        results.extend(data["results"])
        has_more = data["has_more"]
        next_cursor = data["next_cursor"]
    
    return results

def main():
    # 1. 获取所有页面
    pages = get_all_authorized_pages()
    
    full_data = []

    # 2. 遍历每个页面，获取详细内容
    print("开始下载页面内容（这可能需要一些时间）...")
    
    for i, page in enumerate(pages):
        page_id = page["id"]
        
        # 尝试获取标题（Notion 的标题存储结构比较深）
        title = "Untitled"
        try:
            props = page.get("properties", {})
            # 这里的 title 键名取决于你的数据库结构，普通页面通常叫 "title"
            for prop_name, prop_val in props.items():
                if prop_val["id"] == "title":
                    title_obj = prop_val.get("title", [])
                    if title_obj:
                        title = title_obj[0].get("plain_text", "Untitled")
        except Exception:
            pass

        print(f"[{i+1}/{len(pages)}] 正在抓取: {title}")
        
        # 获取该页面下的所有 Blocks
        blocks = get_page_blocks(page_id)
        
        # 组装数据结构
        page_data = {
            "meta": page,       # 页面的元数据（创建时间、URL、属性等）
            "content": blocks   # 页面的实际内容块
        }
        full_data.append(page_data)
        
        # 稍微暂停一下，避免触发 API 速率限制
        time.sleep(0.3)

    # 3. 保存为 JSON 文件
    output_filename = "notion_data.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(full_data, f, ensure_ascii=False, indent=2)
        
    print(f"\n成功！所有数据已保存到 {output_filename}")

def fetch_notion_openapi_spec():
    url = "https://api.apis.guru/v2/specs/notion.com/1.0.0/openapi.json"
    
    filename = "notion_openapi.json"

    print(f"正在尝试从 {url} 获取 Notion API 规范...")

    try:
        # 发送 GET 请求
        response = requests.get(url)
        
        # 检查请求是否成功 (状态码 200)
        response.raise_for_status()
        
        # 获取 JSON 数据
        data = response.json()
        
        # 将数据写入本地文件
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print(f"✅ 成功！Notion API 规范已保存为: {os.path.abspath(filename)}")
        print("你可以将此文件提供给 LLM，以便它理解如何构建具体的 API 请求。")

    except requests.exceptions.RequestException as e:
        print(f"❌ 下载失败: {e}")
    except json.JSONDecodeError:
        print("❌ 无法解析响应内容为 JSON。")
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")

if __name__ == "__main__":
    fetch_notion_openapi_spec()