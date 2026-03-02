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

# Set UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

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
    'best.*product.*20\d{2}', 'top.*rated.*product', 'we recommend',
    # 营销文案
    'transform your', 'revolutionary.*solution', 'game-changing.*results',
]

LOW_QUALITY_PATTERNS = [
    r'^\d+\s+ways?\s+to\b',  # "10 ways to" 通常是标题党
    r'^\d+\s+things?\s+',     # "5 things" 通常是标题党
    r'^why\s+every\b',        # "why everyone" 通常是标题党
    r'this\s+is\s+why\s+',    # "this is why" 通常是标题党
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
    from datetime import datetime, timedelta

    time_str = item.get('time', '').lower()
    today = datetime.now()

    # 如果时间字段为空，假设是今天的
    if not time_str or time_str == 'today' or time_str == 'hot' or time_str == 'real-time':
        return True

    # 如果已经包含日期格式，检查是否是今天
    if re.search(r'\d{4}-\d{2}-\d{2}', time_str):
        try:
            item_date = datetime.strptime(re.search(r'\d{4}-\d{2}-\d{2}', time_str).group(), '%Y-%m-%d')
            return item_date.date() == today.date()
        except:
            pass

    # 处理相对时间
    if 'hour ago' in time_str or 'hours ago' in time_str:
        # 几小时前，是今天的
        return True
    elif 'day ago' in time_str or 'yesterday' in time_str:
        # 昨天或更早，不是今天的
        return False
    elif 'days ago' in time_str:
        # 几天前
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

def fetch_hackernews(limit=5, keyword=None):
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

def fetch_weibo(limit=5, keyword=None):
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

def fetch_github(limit=5, keyword=None):
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

def fetch_36kr(limit=5, keyword=None):
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

def fetch_v2ex(limit=5, keyword=None):
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

def fetch_tencent(limit=5, keyword=None):
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

def fetch_wallstreetcn(limit=5, keyword=None):
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

def fetch_producthunt(limit=5, keyword=None):
    try:
        # Using RSS for speed and reliability without API key
        response = requests.get("https://www.producthunt.com/feed", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'xml')
        if not soup.find('item'): soup = BeautifulSoup(response.text, 'html.parser')

        items = []
        for entry in soup.find_all(['item', 'entry']):
            title = entry.find('title').get_text(strip=True)
            link_tag = entry.find('link')
            url = link_tag.get('href') or link_tag.get_text(strip=True) if link_tag else ""

            pubBox = entry.find('pubDate') or entry.find('published')
            pub = pubBox.get_text(strip=True) if pubBox else ""

            items.append({
                "source": "Product Hunt",
                "title": title,
                "url": url,
                "time": pub,
                "heat": "Top Product" # RSS implies top rank
            })
        return filter_items(items, keyword)[:limit]
    except: return []

def main():
    parser = argparse.ArgumentParser()
    sources_map = {
        'hackernews': fetch_hackernews, 'weibo': fetch_weibo, 'github': fetch_github,
        '36kr': fetch_36kr, 'v2ex': fetch_v2ex, 'tencent': fetch_tencent,
        'wallstreetcn': fetch_wallstreetcn, 'producthunt': fetch_producthunt
    }

    parser.add_argument('--source', default='all', help='Source(s) to fetch from (comma-separated)')
    parser.add_argument('--limit', type=int, default=10, help='Limit per source. Default 10')
    parser.add_argument('--keyword', help='Comma-sep keyword filter')
    parser.add_argument('--deep', action='store_true', help='Download article content for detailed summarization')

    args = parser.parse_args()

    to_run = []
    if args.source == 'all':
        to_run = list(sources_map.values())
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

    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
