import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel # 新增：用于定义输入数据的格式
import httpx
import uvicorn

# 加载 .env
load_dotenv()

app = FastAPI()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("AGENDA_DATABASE_ID")

# 检查环境变量
if not NOTION_TOKEN or not DATABASE_ID:
    raise ValueError("❌ 错误：未找到 NOTION_TOKEN 或 DATABASE_ID。")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

# 1. 定义输入模型
# 这里定义了 API 期望接收的数据格式
class NoteItem(BaseModel):
    title: str          # 页面标题
    content: str        # 页面正文内容
    date: str           # 日期，格式推荐 "2023-10-27" (ISO 8601)

@app.post("/create-dynamic-page")
async def create_dynamic_page(item: NoteItem): # 接收 item 参数
    """
    接收 JSON 数据并在 Notion 创建页面。
    数据包含: title, content, date
    """
    
    # 2. 构建 Payload
    # 这里我们将接收到的 item 数据填入 Notion 的格式中
    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            # 设置标题 (Title 属性)
            "Name": {
                "title": [
                    {"text": {"content": item.title}}
                ]
            },
            # 设置日期 (Date 属性)
            # 注意：你的 Notion 数据库里必须有一个叫 "Date" 的列
            "Date": {
                "date": {
                    "start": item.date
                }
            }
        },
        "children": [
            # 设置正文内容
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "text": {"content": item.content}
                        }
                    ]
                }
            }
        ]
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.notion.com/v1/pages",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                # 打印错误详情，方便调试
                print(f"Notion Error: {response.text}")
                raise HTTPException(status_code=response.status_code, detail=f"Notion API Error: {response.text}")
                
            data = response.json()
            return {
                "status": "success",
                "message": f"页面 '{item.title}' 创建成功！",
                "page_url": data["url"]
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)