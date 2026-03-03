import argparse
import json
import requests
from bs4 import BeautifulSoup
import sys
import time
import re
import concurrent.futures
from datetime import datetime
import io
import os

# Set UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add scripts directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Import translator
from translator import translate_batch

# Headers for scraping to avoid basic bot detection
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def filter_items(items, keyword=None):
    if not keyword:
        return items
    keywords = [k.strip() for k in keyword.split(',') if k.strip()]
    pattern = '|'.join([r'\b' + re.escape(k) + r'\b' for k in keywords])
    regex = r'(?i)(' + pattern + r')'
    return [item for item in items if re.search(regex, item['title'])]

# 内容质量过滤 - 过滤广告和低质量内容
AD_KEYWORDS = [
    # 广告相关
    'sponsored', 'advertisement', 'ad:', 'promoted', 'partner content',
    'promo', 'deal', 'discount', 'offer', 'coupon', 'sale', 'buy now',
    'limited time', 'exclusive offer', 'free trial', 'sign up now',
    'click here', 'order now', 'get yours', 'shop now', 'don\'t miss',
    # 低质量内容
    'clickbait', 'you won\'t believe', 'shocking', 'mind-blowing',
    'this will blow your mind', 'secret trick', 'hack they don\'t want you to know',
    # 纯推广
    r'best.*product.*20\d{2}', 'top.*rated.*product', 'we recommend',
    # 营销文案
    'transform your', 'revolutionary.*solution', 'game-changing.*results',
]

LOW_QUALITY_PATTERNS = [
    r'^\d+\s+ways?\s+to\b',  # "10 ways to" 通常是标题党
    r'^\d+\s+things?\s+',     # "5 things" 通常是标题党
    r'^why\s+every\b',        # "why everyone" 通常是标题党
    r'this\s+is\s+why\s+',    # "this is why" 通常是标题党
    r'best.*product.*20\\d{2}', 'top.*rated.*product', 'we recommend',  # 修复转义
]

def is_high_quality(item):
    """
    检查新闻条目是否为高质量内容
    返回 True 表示保留，False 表示过滤
    """
    title = item.get('title', '').lower()
    source = item.get('source', '')

    # 1. 检查是否包含广告关键词
    for ad_keyword in AD_KEYWORDS:
        if re.search(ad_keyword, title):
            return False

    # 2. 检查低质量模式
    for pattern in LOW_QUALITY_PATTERNS:
        if re.search(pattern, title):
            return False

    # 3. 检查标题长度（太短或太长可能是低质量）
    title_len = len(item.get('title', ''))
    if title_len < 10 or title_len > 300:
        return False

    # 4. 检查是否为纯数字或符号
    if not re.search(r'[a-zA-Z\u4e00-\u9fff]', title):
        return False

    # 5. 特殊来源的额外过滤
    if source == 'Product Hunt':
        # Product Hunt 的内容需要更严格的过滤
        product_hunt_ads = ['agency', 'services', 'marketing', 'seo', 'growth hack']
        for keyword in product_hunt_ads:
            if keyword in title:
                return False

    return True

def filter_quality(items):
    """
    过滤低质量和广告内容
    """
    high_quality = []
    filtered_count = 0

    for item in items:
        if is_high_quality(item):
            high_quality.append(item)
        else:
            filtered_count += 1

    if filtered_count > 0:
        print(f"Filtered out {filtered_count} low-quality/ad items", file=sys.stderr)

    return high_quality


def is_today_news(item):
    """
    检查新闻是否为今天的新闻
    返回 True 表示是今天的新闻，False 表示不是
    """
    from datetime import datetime, timedelta, timezone

    time_str = item.get('time', '')
    today = datetime.now()

    # 如果时间字段为空，假设是今天的
    if not time_str or time_str.lower() in ['today', 'hot', 'real-time']:
        return True

    # 处理 ISO 8601 格式 (如 2026-03-01T20:08:17-08:00)
    if 'T' in time_str and re.search(r'\d{4}-\d{2}-\d{2}T', time_str):
        try:
            # 解析 ISO 8601 格式，自动处理时区
            # 清理时间字符串（可能包含毫秒）
            clean_time = time_str.split('.')[0] if '.' in time_str else time_str
            item_date = datetime.fromisoformat(clean_time)

            # 如果没有时区信息，假设是 UTC
            if item_date.tzinfo is None:
                item_date = item_date.replace(tzinfo=timezone.utc)

            # 转换为本地时区进行比较
            local_date = item_date.astimezone().date()
            return local_date == today.date()
        except Exception as e:
            # 如果解析失败，继续尝试其他格式
            pass

    # 如果已经包含日期格式 (YYYY-MM-DD)，检查是否是今天
    if re.search(r'\d{4}-\d{2}-\d{2}', time_str):
        try:
            date_match = re.search(r'\d{4}-\d{2}-\d{2}', time_str).group()
            item_date = datetime.strptime(date_match, '%Y-%m-%d')
            return item_date.date() == today.date()
        except:
            pass

    # 处理相对时间
    time_lower = time_str.lower()
    if 'hour ago' in time_lower or 'hours ago' in time_lower:
        return True
    elif 'day ago' in time_lower or 'yesterday' in time_lower:
        return False
    elif 'days ago' in time_lower:
        days = int(re.search(r'\d+', time_str).group(0))
        return days == 0

    # 默认认为是今天的
    return True


def filter_today_only(items):
    """
    只保留今天的新闻
    用于日报功能
    """
    today_items = []
    filtered_count = 0

    for item in items:
        if is_today_news(item):
            today_items.append(item)
        else:
            filtered_count += 1

    if filtered_count > 0:
        print(f"Filtered out {filtered_count} non-today items for daily report", file=sys.stderr)

    return today_items


def filter_ai_related_by_deepseek(items):
    """
    使用 DeepSeek API 批量判断新闻是否与 AI 相关
    返回只保留 AI 相关新闻的列表
    """
    if not items:
        return []

    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key:
        print("Warning: DEEPSEEK_API_KEY not set, skipping AI filter", file=sys.stderr)
        return items

    try:
        import requests

        # 批量处理，每次最多 15 条
        batch_size = 15
        ai_related_items = []
        filtered_count = 0

        # 跟踪已判断的新闻标题
        judged_titles = set()

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]

            # 构建输入文本 - 包含序号和标题
            titles_text = "\n".join(
                f"{j + i}. {item.get('title', '')}"
                for j, item in enumerate(batch)
            )

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": """你是AI新闻分类专家。判断新闻是否与AI技术直接相关。

✅ 算是AI相关（返回true）：
- 大语言模型：GPT/Claude/ChatGPT/DeepSeek/Gemini/Llama等
- AI公司：OpenAI/Anthropic/Google DeepMind/Hugging Face等
- AI技术：机器学习/深度学习/神经网络/PyTorch/TensorFlow
- AI应用：生成式AI/AI Agent/RAG/提示工程/微调/计算机视觉/NLP
- AI编程：Copilot/Cursor/代码助手/AI编码工具
- AI芯片/硬件：NPU/神经引擎/TPU/H100等AI芯片
- AI框架/工具：LangChain/向量数据库/AI平台

❌ 不算AI相关（返回false）：
- 纯金融/股市：股票涨跌、IPO、财报、市场分析
- 纯军事/政治：战争、冲突、核武器、外交、选举
- 纯硬件：手机/电脑/平板发布（除非提到AI功能）
- 纯航天：火箭/卫星/空间站（除非提到AI应用）
- 纯经济数据：PMI、GDP、通胀、就业数据
- 一般公司新闻：融资、合作、收购（与AI无关）

⚠️ 特别注意：
- 标题只提到"AI"但实际不是AI技术新闻，应返回false
- 严格标准：新闻必须主要讨论AI技术、产品或应用

返回格式要求：
1. 只返回JSON，不要任何其他文字
2. JSON格式：{"判断结果":[{"序号":1,"标题":"原标题","是否AI相关":true/false},...]}
3. 必须包含所有输入的序号和标题
4. "是否AI相关"必须是布尔值true或false"""
                    },
                    {
                        "role": "user",
                        "content": f"""判断以下{len(batch)}条新闻是否与AI相关：

{titles_text}

只返回JSON格式：{{"判断结果":[{{"序号":1,"标题":"...","是否AI相关":true}},...]}}
不要添加任何解释或其他文字。"""
                    }
                ],
                "temperature": 0,
                "max_tokens": 2000
            }

            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()

                # 解析 JSON 结果
                try:
                    # 清理响应内容
                    content = content.strip()

                    # 移除 markdown 代码块标记
                    if "```" in content:
                        parts = content.split("```")
                        for part in parts:
                            if "{" in part or "判断" in part:
                                content = part
                                if content.startswith("json"):
                                    content = content[4:]
                                break
                        content = content.strip()

                    # 解析 JSON
                    judgment = json.loads(content)
                    judgments = judgment.get("判断结果", [])

                    if not judgments:
                        raise ValueError("No '判断结果' field in response")

                    # 根据标题匹配来过滤
                    batch_filtered = 0
                    for judge_item in judgments:
                        title_from_judge = judge_item.get("标题", "")
                        is_ai = judge_item.get("是否AI相关")

                        # 在原始批次中查找匹配的新闻
                        for item in batch:
                            original_title = item.get("title", "")
                            # 标题可能被截断，使用模糊匹配
                            if title_from_judge in original_title or original_title in title_from_judge or \
                               len(title_from_judge) > 0 and (title_from_judge[:50] in original_title or original_title[:50] in title_from_judge):
                                if is_ai:
                                    ai_related_items.append(item)
                                    judged_titles.add(original_title)
                                else:
                                    batch_filtered += 1
                                break

                    filtered_count += batch_filtered

                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    print(f"Warning: Failed to parse AI filter response: {e}", file=sys.stderr)
                    print(f"Debug: Response was: {content[:500]}", file=sys.stderr)
                    # 解析失败时，跳过这一批
                    continue
            else:
                print(f"DeepSeek API error in AI filter: {response.status_code}", file=sys.stderr)
                continue

            # 避免请求过快
            if i + batch_size < len(items):
                time.sleep(1)

        # 检查是否有未判断的新闻
        unjudged_items = [item for item in items if item.get('title', '') not in judged_titles]

        if unjudged_items and len(unjudged_items) <= 10:
            print(f"Re-judging {len(unjudged_items)} unmatched items", file=sys.stderr)
            # 对未匹配的新闻进行单独判断
            for item in unjudged_items:
                title = item.get('title', '')

                single_payload = {
                    "model": "deepseek-chat",
                    "messages": [
                        {
                            "role": "system",
                            "content": "判断新闻是否与AI相关。只返回JSON：{\"是否AI相关\":true/false}。不要其他文字。"
                        },
                        {
                            "role": "user",
                            "content": f"新闻标题：{title}\n\n是否与AI相关？只返回JSON。"
                        }
                    ],
                    "temperature": 0,
                    "max_tokens": 100
                }

                try:
                    response = requests.post(
                        "https://api.deepseek.com/v1/chat/completions",
                        headers=headers,
                        json=single_payload,
                        timeout=30
                    )

                    if response.status_code == 200:
                        result = response.json()
                        content = result["choices"][0]["message"]["content"].strip()

                        # 清理并解析
                        content = content.strip()
                        if "```" in content:
                            parts = content.split("```")
                            for part in parts:
                                if "{" in part:
                                    content = part
                                    if content.startswith("json"):
                                        content = content[4:]
                                    break

                        judgment = json.loads(content)
                        is_ai = judgment.get("是否AI相关", False)

                        if is_ai:
                            ai_related_items.append(item)
                        else:
                            filtered_count += 1

                except:
                    # 单条判断失败，保守处理：不保留
                    filtered_count += 1

                time.sleep(0.5)

        if filtered_count > 0:
            print(f"AI filter: removed {filtered_count} non-AI items, kept {len(ai_related_items)}", file=sys.stderr)
        else:
            print(f"AI filter: all {len(ai_related_items)} items are AI related", file=sys.stderr)

        return ai_related_items

    except Exception as e:
        print(f"AI filter exception: {e}", file=sys.stderr)
        # 出错时返回原始列表
        return items

def fetch_url_content(url):
    """
    Fetches the content of a URL and extracts text from paragraphs.
    Truncates to 3000 characters.
    """
    if not url or not url.startswith('http'):
        return ""
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
         # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
        # Get text
        text = soup.get_text(separator=' ', strip=True)
        # Simple cleanup
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text[:3000]
    except Exception:
        return ""

def enrich_items_with_content(items, max_workers=10):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_item = {executor.submit(fetch_url_content, item['url']): item for item in items}
        for future in concurrent.futures.as_completed(future_to_item):
            item = future_to_item[future]
            try:
                content = future.result()
                if content:
                    item['content'] = content
            except Exception:
                item['content'] = ""
    return items

# --- Source Fetchers ---

def fetch_hackernews(limit=10, keyword=None):
    base_url = "https://news.ycombinator.com"
    news_items = []
    page = 1
    max_pages = 5

    while len(news_items) < limit and page <= max_pages:
        url = f"{base_url}/news?p={page}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code != 200: break
        except: break

        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select('.athing')
        if not rows: break

        page_items = []
        for row in rows:
            try:
                id_ = row.get('id')
                title_line = row.select_one('.titleline a')
                if not title_line: continue
                title = title_line.get_text()
                link = title_line.get('href')

                # Metadata
                score_span = soup.select_one(f'#score_{id_}')
                score = score_span.get_text() if score_span else "0 points"

                # Age/Time
                age_span = soup.select_one(f'.age a[href="item?id={id_}"]')
                time_str = age_span.get_text() if age_span else ""

                if link and link.startswith('item?id='): link = f"{base_url}/{link}"

                page_items.append({
                    "source": "Hacker News",
                    "title": title,
                    "url": link,
                    "heat": score,
                    "time": time_str
                })
            except: continue

        news_items.extend(filter_items(page_items, keyword))
        if len(news_items) >= limit: break
        page += 1
        time.sleep(0.5)

    return news_items[:limit]

def fetch_weibo(limit=10, keyword=None):
    # Use the PC Ajax API which returns JSON directly and is less rate-limited than scraping s.weibo.com
    url = "https://weibo.com/ajax/side/hotSearch"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://weibo.com/"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        items = data.get('data', {}).get('realtime', [])

        all_items = []
        for item in items:
            # key 'note' is usually the title, sometimes 'word'
            title = item.get('note', '') or item.get('word', '')
            if not title: continue

            # 'num' is the heat value
            heat = item.get('num', 0)

            # Construct URL (usually search query)
            # Web UI uses: https://s.weibo.com/weibo?q=%23TITLE%23&Refer=top
            full_url = f"https://s.weibo.com/weibo?q={requests.utils.quote(title)}&Refer=top"

            all_items.append({
                "source": "Weibo Hot Search",
                "title": title,
                "url": full_url,
                "heat": f"{heat}",
                "time": "Real-time"
            })

        return filter_items(all_items, keyword)[:limit]
    except Exception:
        return []

def fetch_github(limit=10, keyword=None):
    try:
        response = requests.get("https://github.com/trending", headers=HEADERS, timeout=10)
    except: return []

    soup = BeautifulSoup(response.text, 'html.parser')
    items = []
    for article in soup.select('article.Box-row'):
        try:
            h2 = article.select_one('h2 a')
            if not h2: continue
            title = h2.get_text(strip=True).replace('\n', '').replace(' ', '')
            link = "https://github.com" + h2['href']

            desc = article.select_one('p')
            desc_text = desc.get_text(strip=True) if desc else ""

            # Stars (Heat)
            # usually the first 'Link--muted' with a SVG star
            stars_tag = article.select_one('a[href$="/stargazers"]')
            stars = stars_tag.get_text(strip=True) if stars_tag else ""

            items.append({
                "source": "GitHub Trending",
                "title": f"{title} - {desc_text}",
                "url": link,
                "heat": f"{stars} stars",
                "time": "Today"
            })
        except: continue
    return filter_items(items, keyword)[:limit]

def fetch_36kr(limit=10, keyword=None):
    try:
        response = requests.get("https://36kr.com/newsflashes", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = []
        for item in soup.select('.newsflash-item'):
            title = item.select_one('.item-title').get_text(strip=True)
            href = item.select_one('.item-title')['href']
            time_tag = item.select_one('.time')
            time_str = time_tag.get_text(strip=True) if time_tag else ""

            items.append({
                "source": "36Kr",
                "title": title,
                "url": f"https://36kr.com{href}" if not href.startswith('http') else href,
                "time": time_str,
                "heat": ""
            })
        return filter_items(items, keyword)[:limit]
    except: return []

def fetch_v2ex(limit=10, keyword=None):
    try:
        # Hot topics json
        data = requests.get("https://www.v2ex.com/api/topics/hot.json", headers=HEADERS, timeout=10).json()
        items = []
        for t in data:
            # V2EX API fields: created, replies (heat)
            replies = t.get('replies', 0)
            created = t.get('created', 0)
            # convert epoch to readable if possible, simpler to just leave as is or basic format
            # Let's keep it simple
            items.append({
                "source": "V2EX",
                "title": t['title'],
                "url": t['url'],
                "heat": f"{replies} replies",
                "time": "Hot"
            })
        return filter_items(items, keyword)[:limit]
    except: return []

def fetch_tencent(limit=10, keyword=None):
    try:
        url = "https://i.news.qq.com/web_backend/v2/getTagInfo?tagId=aEWqxLtdgmQ%3D"
        data = requests.get(url, headers={"Referer": "https://news.qq.com/"}, timeout=10).json()
        items = []
        for news in data['data']['tabs'][0]['articleList']:
            items.append({
                "source": "Tencent News",
                "title": news['title'],
                "url": news.get('url') or news.get('link_info', {}).get('url'),
                "time": news.get('pub_time', '') or news.get('publish_time', '')
            })
        return filter_items(items, keyword)[:limit]
    except: return []

def fetch_wallstreetcn(limit=10, keyword=None):
    try:
        url = "https://api-one.wallstcn.com/apiv1/content/information-flow?channel=global-channel&accept=article&limit=30"
        data = requests.get(url, timeout=10).json()
        items = []
        for item in data['data']['items']:
            res = item.get('resource')
            if res and (res.get('title') or res.get('content_short')):
                 ts = res.get('display_time', 0)
                 time_str = datetime.fromtimestamp(ts).strftime('%H:%M') if ts else ""
                 items.append({
                     "source": "Wall Street CN",
                     "title": res.get('title') or res.get('content_short'),
                     "url": res.get('uri'),
                     "time": time_str
                 })
        return filter_items(items, keyword)[:limit]
    except: return []

def fetch_producthunt(limit=10, keyword=None):
    try:
        # Using Atom feed for Product Hunt
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/atom+xml,application/xml,text/xml"
        }
        response = requests.get("https://www.producthunt.com/feed", headers=headers, timeout=10)

        # Parse as XML (Atom format)
        soup = BeautifulSoup(response.text, 'html.parser')

        items = []
        for entry in soup.find_all('entry'):
            try:
                # Title
                title_tag = entry.find('title')
                if not title_tag: continue
                title = title_tag.get_text(strip=True)

                # URL - Atom format uses href attribute
                link_tag = entry.find('link')
                url = ""
                if link_tag and link_tag.get('href'):
                    url = link_tag.get('href')
                elif link_tag:
                    url = link_tag.get_text(strip=True)

                # Published date
                pub_tag = entry.find('published')
                time_str = pub_tag.get_text(strip=True) if pub_tag else "Today"

                if title and url:
                    items.append({
                        "source": "Product Hunt",
                        "title": title,
                        "url": url,
                        "time": time_str,
                        "heat": "Top Product"
                    })
            except: continue

        return filter_items(items, keyword)[:limit]
    except Exception as e:
        import sys
        print(f"Product Hunt error: {e}", file=sys.stderr)
        return []

def main():
    parser = argparse.ArgumentParser()
    sources_map = {
        'hackernews': fetch_hackernews, 'weibo': fetch_weibo, 'github': fetch_github,
        '36kr': fetch_36kr, 'v2ex': fetch_v2ex, 'tencent': fetch_tencent,
        'wallstreetcn': fetch_wallstreetcn, 'producthunt': fetch_producthunt
    }

    # 默认启用的来源（排除 v2ex）
    default_sources = ['hackernews', 'weibo', 'github', '36kr', 'tencent', 'wallstreetcn', 'producthunt']

    parser.add_argument('--source', default='all', help='Source(s) to fetch from (comma-separated)')
    parser.add_argument('--limit', type=int, default=10, help='Limit per source. Default 10')
    parser.add_argument('--keyword', help='Comma-sep keyword filter')
    parser.add_argument('--deep', action='store_true', help='Download article content for detailed summarization')

    args = parser.parse_args()

    to_run = []
    if args.source == 'all':
        # 使用默认来源列表（排除 v2ex）
        for s in default_sources:
            if s in sources_map: to_run.append(sources_map[s])
    else:
        requested_sources = [s.strip() for s in args.source.split(',')]
        for s in requested_sources:
            if s in sources_map: to_run.append(sources_map[s])

    results = []
    for func in to_run:
        try:
            results.extend(func(args.limit, args.keyword))
        except: pass

    # 应用质量过滤，移除广告和低质量内容
    if results:
        original_count = len(results)
        results = filter_quality(results)
        filtered_count = original_count - len(results)
        if filtered_count > 0:
            sys.stderr.write(f"Quality filter: removed {filtered_count} items, kept {len(results)}\n")

    # 使用 DeepSeek API 判断新闻是否与 AI 相关
    if results:
        results = filter_ai_related_by_deepseek(results)

    # 应用日期过滤，只保留今天的新闻（日报功能）
    if results:
        original_count = len(results)
        results = filter_today_only(results)
        date_filtered = original_count - len(results)
        if date_filtered > 0:
            sys.stderr.write(f"Date filter: removed {date_filtered} non-today items, kept {len(results)}\n")

    if args.deep and results:
        sys.stderr.write(f"Deep fetching content for {len(results)} items...\n")
        results = enrich_items_with_content(results)

    # 翻译新闻标题和摘要（使用 DeepSeek API）
    if results:
        sys.stderr.write(f"Translating {len(results)} news items...\n")
        results = translate_batch(results)
        sys.stderr.write(f"Translation completed.\n")

    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
