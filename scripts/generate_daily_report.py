#!/usr/bin/env python3
"""AI 资讯日报生成器 - 读取 latest-24h.json，用 Gemini 生成智能摘要日报。"""

import json
import os
import sys
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    print("请先安装依赖: pip install requests")
    sys.exit(1)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_BASE_URL = os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")

def load_news_data(data_dir="data"):
    """加载最新24小时新闻数据。"""
    latest_file = os.path.join(data_dir, "latest-24h.json")
    if not os.path.exists(latest_file):
        print(f"❌ 数据文件不存在: {latest_file}")
        return None
    
    with open(latest_file, "r", encoding="utf-8") as f:
        return json.load(f)

def summarize_with_gemini(news_data, api_key):
    """用 Gemini 生成智能摘要。"""
    if not api_key:
        print("❌ 未设置 GEMINI_API_KEY")
        return None
    
    items = news_data.get("items", [])[:50]
    
    news_text = ""
    for i, item in enumerate(items, 1):
        title = item.get("title_zh", item.get("title", ""))
        source = item.get("source", "")
        site = item.get("site_name", "")
        news_text += f"{i}. [{site}] {source}: {title}\n"
    
    prompt = f"""
你是一个专业的 AI 资讯编辑。请根据以下今日 AI 领域新闻，生成一份结构化的日报：

【今日新闻列表】
{news_text}

【日报结构要求】
1. 📌 今日头条（3条最重要的）
2. 🚀 技术突破（模型更新、算法进展）
3. 💼 产业动态（公司新闻、融资、合作）
4. 📝 论文速递（学术论文、研究成果）
5. 🎯 工具推荐（新工具、新功能）
6. 💬 热门讨论（社交媒体热点）

【写作风格】
- 简洁专业，每条不超过200字
- 中文输出，适合公众号发布
- 每条新闻注明来源
- 使用 emoji 增加可读性

请直接输出日报内容，不要包含其他说明。
"""
    
    try:
        r = requests.post(
            f"{GEMINI_BASE_URL}/models/gemini-1.5-flash:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            },
            timeout=60
        )
        
        if r.status_code != 200:
            print(f"❌ Gemini API 错误: {r.status_code}")
            print(r.text[:500])
            return None
        
        result = r.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
    
    except Exception as e:
        print(f"❌ 调用 Gemini 失败: {e}")
        return None

def generate_daily_report(data_dir="data", output_dir="data"):
    """生成日报并保存。"""
    news_data = load_news_data(data_dir)
    if not news_data:
        return None
    
    print(f"📊 加载了 {news_data.get('total_items', 0)} 条新闻")
    
    summary = summarize_with_gemini(news_data, GEMINI_API_KEY)
    if not summary:
        print("⚠️ 无法生成智能摘要，使用简单汇总")
        summary = generate_simple_report(news_data)
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report = {
        "date": today,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_news": news_data.get("total_items", 0),
        "summary": summary
    }
    
    output_file = os.path.join(output_dir, f"daily-report-{today}.md")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# AI 资讯日报 {today}\n\n")
        f.write(summary)
    
    print(f"✅ 日报已保存: {output_file}")
    return output_file

def generate_simple_report(news_data):
    """生成简单汇总（无 Gemini 时使用）。"""
    items = news_data.get("items", [])[:20]
    report = "## 今日 AI 资讯汇总\n\n"
    for i, item in enumerate(items, 1):
        title = item.get("title_zh", item.get("title", ""))
        source = item.get("source", "")
        url = item.get("url", "")
        report += f"{i}. [{title}]({url}) - {source}\n\n"
    return report

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--simple":
        news_data = load_news_data()
        if news_data:
            print(generate_simple_report(news_data))
    else:
        generate_daily_report()
