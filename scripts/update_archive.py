#!/usr/bin/env python3
"""
更新归档索引
Update archive index
"""
import json
from pathlib import Path
from datetime import datetime
import io
import sys
import os

# Set UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Category keywords for categorization
CATEGORY_KEYWORDS = {
    "global": ["openai", "gpt", "claude", "anthropic", "google", "gemini", "microsoft", "meta", "llama", "deepseek"],
    "tech": ["github", "rust", "python", "javascript", "react", "typescript", "api", "framework", "library", "code"],
    "china": ["36kr", "腾讯", "阿里", "百度", "字节", "小米", "华为", "中国", "国内"],
    "product": ["launch", "release", "product", "app", "tool", "platform", "service"],
}

CATEGORIES = [
    {"id": "global", "name": "全球头条"},
    {"id": "tech", "name": "科技与开发"},
    {"id": "china", "name": "中国科技圈"},
    {"id": "product", "name": "产品猎场"},
    {"id": "other", "name": "其他"},
]

def categorize_item(item):
    """Categorize a news item based on keywords"""
    title = item.get("title", "").lower()
    source = item.get("source", "").lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in title or keyword in source:
                return category
    return "other"

def update_archive():
    """Update the archive index"""
    # Change to project directory
    script_dir = Path(__file__).parent.parent
    os.chdir(script_dir)

    news_dir = Path("docs/news")
    data_dir = Path("docs/data")
    archive_file = data_dir / "archive-index.json"

    # Create data directory if not exists
    data_dir.mkdir(parents=True, exist_ok=True)

    # Scan all news files
    archives = []
    for json_file in sorted(news_dir.glob("*.json"), reverse=True):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                items = json.load(f)

            date_str = json_file.stem
            try:
                date_obj = datetime.strptime(date_str, "%Y%m%d")
                formatted = f"{date_obj.year}年{date_obj.month}月{date_obj.day}日"
                weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date_obj.weekday()]
                year = date_obj.year
                month = date_obj.month
            except:
                formatted = date_str
                weekday = ""
                year = int(date_str[:4]) if date_str[:4].isdigit() else 2024
                month = int(date_str[4:6]) if len(date_str) >= 6 and date_str[4:6].isdigit() else 1

            top_news = items[0]["title"] if items else "暂无新闻"

            # Count by category
            cat_counts = {}
            for item in items:
                cat = categorize_item(item)
                cat_counts[cat] = cat_counts.get(cat, 0) + 1

            # Format categories for display
            categories_formatted = {}
            for cat_id, count in cat_counts.items():
                cat_config = next((c for c in CATEGORIES if c["id"] == cat_id), None)
                if cat_config:
                    categories_formatted[cat_config["name"]] = count

            archives.append({
                "date": date_str,
                "formatted": formatted,
                "weekday": weekday,
                "count": len(items),
                "top_news": top_news,
                "categories": cat_counts,
                "categories_formatted": categories_formatted,
                "year": year,
                "month": month
            })
        except Exception as e:
            print(f"Error processing {json_file}: {e}", file=sys.stderr)
            continue

    # Group by month for older entries (last 30 days detailed, older grouped)
    from datetime import timedelta
    cutoff_date = datetime.now() - timedelta(days=30)

    detailed = []
    grouped = {}

    for arch in archives:
        arch_date = datetime.strptime(arch["date"], "%Y%m%d")
        if arch_date >= cutoff_date:
            detailed.append(arch)
        else:
            key = f"{arch['year']}年{arch['month']}月"
            if key not in grouped:
                grouped[key] = {
                    "year": arch["year"],
                    "month": arch["month"],
                    "formatted": key,
                    "count": 0,
                    "items": []
                }
            grouped[key]["count"] += arch["count"]
            grouped[key]["items"].append(arch)

    # Combine results
    result = {
        "detailed": detailed,
        "grouped": list(grouped.values()),
        "last_updated": datetime.now().isoformat(),
        "total_days": len(archives),
        "total_news": sum(a["count"] for a in archives)
    }

    # Write to archive index
    with open(archive_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Updated archive index: {len(archives)} days, {result['total_news']} total news", file=sys.stderr)
    return result

if __name__ == "__main__":
    result = update_archive()
    print(json.dumps(result, ensure_ascii=False, indent=2))
