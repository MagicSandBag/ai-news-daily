#!/usr/bin/env python3
"""
生成每日新闻首页
Generate daily news index page
"""
import json
import re
from datetime import datetime
from pathlib import Path
import io
import sys
import os

# Add scripts directory to path for imports
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

# Import translator
from translator import translate_title, translate_summary

# Set UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Template for index.html
INDEX_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI News Daily - {formatted_date}</title>
    <link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
    <header>
        <div class="header-inner">
            <div class="logo">AI News <span>Daily</span></div>
            <div class="header-meta">{formatted_date} · {weekday}</div>
            <nav class="nav-links">
                <a href="archive.html">📅 归档</a>
                <a href="#" onclick="location.reload(); return false;">🔄 刷新</a>
            </nav>
        </div>
    </header>

    <main>
        <div class="date-header">
            <div class="date">{formatted_date}</div>
            <div class="subtitle"><span class="emoji">☕</span> 早安，这是今天的 AI 每日速递</div>
        </div>

        {content_sections}

        <div class="empty-state" style="display: {empty_display};">
            <p>📭 今日暂无新闻</p>
            <p style="font-size: 0.85rem; color: var(--text-meta); margin-top: 0.5rem;">请稍后刷新或查看历史归档</p>
        </div>
    </main>

    <footer>
        <p>由 <a href="https://github.com">AI News Daily</a> 自动生成 · 数据来源于 Hacker News、GitHub Trending、36Kr 等</p>
        <p style="margin-top: 0.5rem; color: var(--text-meta);">每日更新 · 免费 · 开源</p>
    </footer>

    <script src="assets/js/main.js"></script>
</body>
</html>
'''

# Template for archive.html
ARCHIVE_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI News Daily - 历史归档</title>
    <link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
    <header>
        <div class="header-inner">
            <div class="logo">AI News <span>Daily</span></div>
            <div class="header-meta">历史归档</div>
            <nav class="nav-links">
                <a href="index.html">🏠 首页</a>
                <a href="#" onclick="location.reload(); return false;">🔄 刷新</a>
            </nav>
        </div>
    </header>

    <main>
        <div class="date-header">
            <div class="date">历史归档</div>
            <div class="subtitle"><span class="emoji">📚</span> 浏览过去的 AI 每日速递</div>
        </div>

        {archive_content}

        <div class="empty-state" style="display: {empty_display};">
            <p>📭 暂无历史记录</p>
        </div>
    </main>

    <footer>
        <p>由 <a href="https://github.com">AI News Daily</a> 自动生成</p>
    </footer>

    <script src="assets/js/main.js"></script>
</body>
</html>
'''

# Category configuration
CATEGORIES = [
    {"id": "global", "name": "全球头条", "emoji": "🔥", "badge": "Headlines", "color": "red"},
    {"id": "tech", "name": "科技与开发", "emoji": "💻", "badge": "Tech & Dev", "color": "blue"},
    {"id": "china", "name": "中国科技圈", "emoji": "🇨🇳", "badge": "China Tech", "color": "green"},
    {"id": "product", "name": "产品猎场", "emoji": "🚀", "badge": "Product Hunt", "color": "amber"},
    {"id": "other", "name": "其他", "emoji": "📰", "badge": "Other", "color": "gray"},
]

# Keywords for categorization
CATEGORY_KEYWORDS = {
    "global": ["openai", "gpt", "claude", "anthropic", "google", "gemini", "microsoft", "meta", "llama", "deepseek"],
    "tech": ["github", "rust", "python", "javascript", "react", "typescript", "api", "framework", "library", "code"],
    "china": ["36kr", "腾讯", "阿里", "百度", "字节", "小米", "华为", "中国", "国内"],
    "product": ["launch", "release", "product", "app", "tool", "platform", "service"],
}

def categorize_item(item):
    """Categorize a news item based on keywords"""
    title = item.get("title", "").lower()
    source = item.get("source", "").lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in title or keyword in source:
                return category
    return "other"

def expand_summary(content, title, target_length=300):
    """
    智能摘要扩展：根据内容量生成 100-500 字的摘要
    """
    # Use content if available, otherwise use title
    text = content or title

    if not text:
        return title

    # Remove extra whitespace
    text = ' '.join(text.split())

    # If content is short, return directly
    if len(text) <= target_length:
        return text

    # Split by sentences
    sentences = re.split(r'([。！？.!?])', text)
    sentences = [''.join(pair) for pair in zip(sentences[::2], sentences[1::2])]

    # Build summary progressively
    result = []
    current_length = 0

    for sentence in sentences:
        if current_length + len(sentence) > target_length * 1.2:
            break
        result.append(sentence)
        current_length += len(sentence)

        # At least one sentence, and target length reached
        if len(result) >= 1 and current_length >= 100:
            break

    summary = ''.join(result).strip()

    # Ensure not exceeding 500 chars
    if len(summary) > 500:
        summary = summary[:497] + "..."

    return summary if summary else title

def render_news_card(item, index, category_id):
    """Render a single news card"""
    card_id = f"{category_id}-{index}"
    title = item.get("title", "无标题")
    url = item.get("url", "#")
    source = item.get("source", "未知来源")
    heat = item.get("heat", "")
    time_str = item.get("time", "")
    content = item.get("content", "")

    # Translate title to Chinese - returns (translation, is_good_translation)
    translated_title, is_good_translation = translate_title(title)

    # If we have a good Chinese translation, use it; otherwise keep English
    if is_good_translation:
        display_title = translated_title
        show_original_title = True
    else:
        display_title = title
        show_original_title = False

    # Generate summary (Chinese)
    summary = translate_summary(content, title, max_length=200)

    # Generate tags
    tags = []
    tag_keywords = ["AI", "LLM", "GPT", "Claude", "OpenAI", "Rust", "Python", "JavaScript", "GitHub", "大模型", "人工智能", "智能体"]
    for keyword in tag_keywords:
        if keyword.lower() in title.lower() or keyword.lower() in summary.lower():
            tags.append(f"#{keyword}")

    tags_str = " ".join(tags[:5]) if tags else "#AI"

    # Short summary for collapsed view
    short_summary = summary[:120] + "..." if len(summary) > 120 else summary

    return f'''            <article class="news-card collapsed" id="news-{card_id}">
                <div class="news-card-header">
                    <h3 class="news-card-title">
                        <a href="{url}" target="_blank" title="{title}">{display_title}</a>
                    </h3>
                    <button class="expand-btn" id="btn-{card_id}" onclick="toggleNews('{card_id}')">
                        展开详情 ▼
                    </button>
                </div>
                <div class="news-card-meta">
                    <span class="source-badge">{source}</span>
                    {f'<span>🔥 {heat}</span>' if heat else ''}
                    {f'<span>🕐 {time_str}</span>' if time_str else ''}
                </div>
                <p class="news-card-summary">{short_summary}</p>

                <div class="news-details">
                    <div class="news-summary-full">
                        {f'<p><strong>中文标题：</strong>{translated_title}</p>' if show_original_title else ''}
                        <p><strong>内容摘要：</strong>{summary}</p>
                        {f'<p style="margin-top:0.5rem; color:var(--text-meta); font-size:0.85rem;"><strong>原标题：</strong>{title}</p>' if show_original_title else ''}
                    </div>
                    <a href="{url}" class="original-link" target="_blank">
                        🔗 查看原文
                    </a>
                    <div class="news-meta-expanded">
                        <span>🏷️ {tags_str}</span>
                        {f'<span>📊 {heat} · {time_str}</span>' if heat or time_str else ''}
                    </div>
                </div>
            </article>'''

def render_section(category, items):
    """Render a category section"""
    if not items:
        return ""

    cards_html = "\n".join([
        render_news_card(item, i, category["id"])
        for i, item in enumerate(items)
    ])

    return f'''        <!-- {category["name"]} -->
        <section class="section">
            <div class="section-header">
                <span class="emoji">{category["emoji"]}</span>
                <span class="title">{category["name"]}</span>
                <span class="badge {category["color"]}">{category["badge"]}</span>
            </div>

{cards_html}
        </section>'''

def generate_index():
    """Generate the index.html for today's news"""
    # Get today's date
    today = datetime.now()
    date_str = today.strftime("%Y%m%d")
    # Format: 2026年3月2日 (remove leading zeros)
    formatted_date = f"{today.year}年{today.month}月{today.day}日"
    weekday = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][today.weekday()]

    # Path to news file
    news_file = Path("docs/news") / f"{date_str}.json"

    # Read news data
    news_items = []
    if news_file.exists():
        with open(news_file, 'r', encoding='utf-8') as f:
            news_items = json.load(f)

    # Categorize items
    categorized = {cat["id"]: [] for cat in CATEGORIES}
    for item in news_items:
        cat_id = categorize_item(item)
        categorized[cat_id].append(item)

    # Render sections
    sections_html = ""
    total_count = 0
    for cat in CATEGORIES:
        items = categorized[cat["id"]]
        if items:
            sections_html += render_section(cat, items) + "\n"
            total_count += len(items)

    # Generate HTML
    html = INDEX_TEMPLATE.format(
        formatted_date=formatted_date,
        weekday=weekday,
        content_sections=sections_html,
        empty_display="none" if total_count > 0 else "block"
    )

    # Write to docs/index.html
    index_path = Path("docs/index.html")
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Generated index.html with {total_count} news items", file=sys.stderr)
    return total_count

def generate_archive():
    """Generate the archive.html page"""
    news_dir = Path("docs/news")

    # Scan all news files
    archives = []
    for json_file in sorted(news_dir.glob("*.json"), reverse=True):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                items = json.load(f)

            date_str = json_file.stem
            try:
                date_obj = datetime.strptime(date_str, "%Y%m%d")
                formatted = date_obj.strftime("%Y年%-m月%-d日")
                weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date_obj.weekday()]
            except:
                formatted = date_str
                weekday = ""

            top_news = items[0]["title"] if items else "暂无新闻"

            # Count by category
            cat_counts = {}
            for item in items:
                cat = categorize_item(item)
                cat_counts[cat] = cat_counts.get(cat, 0) + 1

            archives.append({
                "date": date_str,
                "formatted": formatted,
                "weekday": weekday,
                "count": len(items),
                "top_news": top_news[:60] + ("..." if len(top_news) > 60 else ""),
                "categories": cat_counts
            })
        except:
            continue

    # Render archive items
    archive_html = ""
    for arch in archives:
        # Format category badges
        cat_badges = ""
        for cat_id, count in arch["categories"].items():
            cat_config = next((c for c in CATEGORIES if c["id"] == cat_id), None)
            if cat_config and count > 0:
                cat_badges += f'<span class="source-badge">{cat_config["name"]} {count}</span> '

        archive_html += f'''        <div class="archive-item" onclick="loadArchiveDate('{arch["date"]}')" style="cursor: pointer;">
            <div class="archive-date">
                <span class="date-text">{arch["formatted"]}</span>
                <span class="weekday-text">{arch["weekday"]}</span>
            </div>
            <div class="archive-info">
                <div class="archive-count">{arch["count"]}条新闻</div>
                <div class="archive-top">🔥 {arch["top_news"]}</div>
                <div class="archive-cats">{cat_badges}</div>
            </div>
        </div>'''

    html = ARCHIVE_TEMPLATE.format(
        archive_content=archive_html,
        empty_display="none" if len(archives) > 0 else "block"
    )

    # Write to docs/archive.html
    archive_path = Path("docs/archive.html")
    with open(archive_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Generated archive.html with {len(archives)} days", file=sys.stderr)
    return len(archives)

if __name__ == "__main__":
    import os

    # Change to script directory
    script_dir = Path(__file__).parent.parent
    os.chdir(script_dir)

    # Generate both pages
    count = generate_index()
    archive_count = generate_archive()

    print(f"Done! Generated {count} news items and {archive_count} archive days.")
