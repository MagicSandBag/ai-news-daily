/**
 * AI News Daily - Main JavaScript
 * Frontend交互逻辑
 */

// 新闻展开/收起功能
function toggleNews(cardId) {
    const card = document.getElementById('news-' + cardId);
    const btn = document.getElementById('btn-' + cardId);

    if (!card || !btn) return;

    if (card.classList.contains('collapsed')) {
        card.classList.remove('collapsed');
        card.classList.add('expanded');
        btn.textContent = '收起 ▲';
    } else {
        card.classList.remove('expanded');
        card.classList.add('collapsed');
        btn.textContent = '展开详情 ▼';
    }
}

// 加载指定日期的新闻归档
async function loadArchiveDate(dateStr) {
    console.log('Loading archive for:', dateStr);

    // Hide archive list and show news display
    document.getElementById('archive-list').style.display = 'none';
    const newsDisplay = document.getElementById('news-display');
    newsDisplay.style.display = 'block';

    // Set title
    const titleEl = document.getElementById('display-date-title');
    try {
        const dateObj = parseDateStr(dateStr);
        titleEl.textContent = formatDateTitle(dateObj);
    } catch {
        titleEl.textContent = dateStr;
    }

    // Show loading
    const newsContent = document.getElementById('news-content');
    newsContent.innerHTML = '<div style="text-align: center; padding: 3rem; color: var(--text-secondary);">正在加载新闻...</div>';

    try {
        // Fetch the JSON file
        const response = await fetch('news/' + dateStr + '.json');
        if (!response.ok) {
            throw new Error('Failed to load news');
        }
        const newsItems = await response.json();

        // Categorize items (same logic as generate_daily.py)
        const categories = categorizeNewsItems(newsItems);

        // Render news sections
        let html = '';
        for (const cat of categories) {
            if (cat.items.length > 0) {
                html += renderCategorySection(cat);
            }
        }

        newsContent.innerHTML = html || '<div style="text-align: center; padding: 3rem;">该日期暂无新闻</div>';

        // Initialize cards as collapsed
        newsContent.querySelectorAll('.news-card').forEach(card => {
            card.classList.add('collapsed');
        });

    } catch (error) {
        console.error('Error loading archive:', error);
        newsContent.innerHTML = '<div style="text-align: center; padding: 3rem; color: var(--error-color);">加载失败，请返回重试</div>';
    }
}

// Close archive news and return to list
function closeArchiveNews() {
    document.getElementById('news-display').style.display = 'none';
    document.getElementById('archive-list').style.display = 'block';
    document.getElementById('news-content').innerHTML = '';
}

// Parse date string (YYYYMMDD) to Date object
function parseDateStr(dateStr) {
    const year = parseInt(dateStr.substring(0, 4));
    const month = parseInt(dateStr.substring(4, 6)) - 1;
    const day = parseInt(dateStr.substring(6, 8));
    return new Date(year, month, day);
}

// Format date for title display
function formatDateTitle(dateObj) {
    const year = dateObj.getFullYear();
    const month = dateObj.getMonth() + 1;
    const day = dateObj.getDate();
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    const weekday = weekdays[dateObj.getDay()];
    return `${year}年${month}月${day}日 ${weekday}`;
}

// Category configuration (same as generate_daily.py)
const NEWS_CATEGORIES = [
    {id: "global", name: "全球头条", emoji: "🔥", badge: "Headlines", color: "red"},
    {id: "tech", name: "科技与开发", emoji: "💻", badge: "Tech & Dev", color: "blue"},
    {id: "china", name: "中国科技圈", emoji: "🇨🇳", badge: "China Tech", color: "green"},
    {id: "product", name: "产品猎场", emoji: "🚀", badge: "Product Hunt", color: "amber"},
    {id: "other", name: "其他", emoji: "📰", badge: "Other", color: "gray"},
];

const CATEGORY_KEYWORDS = {
    "global": ["openai", "gpt", "claude", "anthropic", "google", "gemini", "microsoft", "meta", "llama", "deepseek"],
    "tech": ["github", "rust", "python", "javascript", "react", "typescript", "api", "framework", "library", "code"],
    "china": ["36kr", "腾讯", "阿里", "百度", "字节", "小米", "华为", "中国", "国内"],
    "product": ["launch", "release", "product", "app", "tool", "platform", "service"],
};

// Categorize news items
function categorizeNewsItems(items) {
    const categorized = NEWS_CATEGORIES.map(cat => ({...cat, items: []}));

    for (const item of items) {
        const title = (item.title || "").toLowerCase();
        const source = (item.source || "").toLowerCase();
        let catId = "other";

        for (const [categoryId, keywords] of Object.entries(CATEGORY_KEYWORDS)) {
            for (const keyword of keywords) {
                if (title.includes(keyword) || source.includes(keyword)) {
                    catId = categoryId;
                    break;
                }
            }
            if (catId !== "other") break;
        }

        const category = categorized.find(c => c.id === catId);
        if (category) {
            category.items.push(item);
        }
    }

    return categorized;
}

// Render a category section
function renderCategorySection(category) {
    const cardsHtml = category.items.map((item, index) => renderNewsCard(item, index, category.id)).join('\n');

    return `        <!-- ${category.name} -->
        <section class="section">
            <div class="section-header">
                <span class="emoji">${category.emoji}</span>
                <span class="title">${category.name}</span>
                <span class="badge ${category.color}">${category.badge}</span>
            </div>

${cardsHtml}
        </section>`;
}

// Render a single news card
function renderNewsCard(item, index, categoryId) {
    const cardId = categoryId + '-' + index;
    const title = item.title || '无标题';
    const url = item.url || '#';
    const source = item.source || '未知来源';
    const heat = item.heat || '';
    const timeStr = item.time || '';
    const content = item.content || '';

    // Format time display
    const formattedTime = formatTimeDisplay(timeStr, source);

    // Generate summary (use content or title)
    const summary = content || title;
    const summaryTruncated = summary.length > 150 ? summary.substring(0, 150) + '...' : summary;

    // Generate tags
    const tagKeywords = ["AI", "LLM", "GPT", "Claude", "OpenAI", "Rust", "Python", "JavaScript", "GitHub", "大模型", "人工智能", "智能体"];
    const searchText = (title + ' ' + summary).toLowerCase();
    const tags = [];
    for (const keyword of tagKeywords) {
        if (searchText.includes(keyword.toLowerCase())) {
            tags.push('#' + keyword);
        }
    }
    const tagsStr = tags.slice(0, 5).join(' ') || '#AI';

    return `            <article class="news-card collapsed" id="news-${cardId}">
                <div class="news-card-header">
                    <h3 class="news-card-title">
                        <a href="${url}" target="_blank" title="${title}">${title}</a>
                    </h3>
                    <button class="expand-btn" id="btn-${cardId}" onclick="toggleNews('${cardId}')">
                        展开详情 ▼
                    </button>
                </div>
                <div class="news-card-meta">
                    <span class="source-badge">${source}</span>
                    ${heat ? `<span>🔥 ${heat}</span>` : ''}
                    ${formattedTime ? `<span>🕐 ${formattedTime}</span>` : ''}
                </div>
                <p class="news-card-summary">${summaryTruncated}</p>

                <div class="news-details">
                    <div class="news-summary-full">
                        <div class="summary-content">${summary}</div>
                    </div>
                    <a href="${url}" class="original-link" target="_blank">
                        🔗 查看原文
                    </a>
                    <div class="news-meta-expanded">
                        <span>🏷️ ${tagsStr}</span>
                        ${heat || formattedTime ? `<span>📊 ${heat} · ${formattedTime}</span>` : ''}
                    </div>
                </div>
            </article>`;
}

// Format time display (simplified version)
function formatTimeDisplay(timeStr, source) {
    if (!timeStr) return new Date().toISOString().split('T')[0];

    // If already a date format, return as is
    if (/^\d{4}-\d{2}-\d{2}/.test(timeStr)) {
        return timeStr.split(' ')[0];
    }

    // For relative time, return today's date
    const now = new Date();
    const lower = timeStr.toLowerCase();

    if (lower.includes('hour ago') || lower.includes('hours ago') || lower === 'today' || lower === 'real-time' || lower === 'hot') {
        return now.toISOString().split('T')[0];
    } else if (lower.includes('day ago') || lower.includes('days ago') || lower.includes('yesterday')) {
        const yesterday = new Date(now);
        yesterday.setDate(yesterday.getDate() - 1);
        return yesterday.toISOString().split('T')[0];
    }

    return now.toISOString().split('T')[0];
}

// 展开月度归档
function toggleMonthGroup(monthKey) {
    const group = document.getElementById('month-group-' + monthKey);
    const btn = document.getElementById('month-btn-' + monthKey);

    if (!group || !btn) return;

    if (group.style.display === 'none') {
        group.style.display = 'block';
        btn.textContent = '收起 ▲';
    } else {
        group.style.display = 'none';
        btn.textContent = '展开 ▼';
    }
}

// 搜索功能
function searchNews(query) {
    if (!query || query.trim() === '') {
        // Show all sections
        document.querySelectorAll('.section').forEach(section => {
            section.style.display = 'block';
        });
        return;
    }

    query = query.toLowerCase();
    let foundCount = 0;

    // Search in news cards
    document.querySelectorAll('.news-card').forEach(card => {
        const title = card.querySelector('.news-card-title').textContent.toLowerCase();
        const summary = card.querySelector('.news-card-summary').textContent.toLowerCase();
        const section = card.closest('.section');

        if (title.includes(query) || summary.includes(query)) {
            card.style.display = 'block';
            if (section) section.style.display = 'block';
            foundCount++;
        } else {
            card.style.display = 'none';
        }
    });

    // Hide empty sections
    document.querySelectorAll('.section').forEach(section => {
        const visibleCards = section.querySelectorAll('.news-card[style="display: block;"], .news-card:not([style*="display: none"])');
        if (visibleCards.length === 0) {
            section.style.display = 'none';
        }
    });

    // Show search result count
    showSearchResult(foundCount, query);
}

function showSearchResult(count, query) {
    // Remove existing result indicator
    const existing = document.querySelector('.search-result');
    if (existing) existing.remove();

    if (query) {
        const resultDiv = document.createElement('div');
        resultDiv.className = 'search-result';
        resultDiv.style.cssText = `
            text-align: center;
            padding: 1rem;
            background: var(--bg-secondary);
            border-radius: 8px;
            margin-bottom: 2rem;
            font-size: 0.9rem;
            color: var(--text-secondary);
        `;
        resultDiv.innerHTML = `找到 ${count} 条关于 "<strong>${query}</strong>" 的新闻`;

        const main = document.querySelector('main');
        const dateHeader = document.querySelector('.date-header');
        main.insertBefore(resultDiv, dateHeader.nextSibling);
    }
}

// 按分类筛选
function filterByCategory(categoryId) {
    document.querySelectorAll('.section').forEach(section => {
        if (section.id === 'section-' + categoryId || categoryId === 'all') {
            section.style.display = 'block';
        } else {
            section.style.display = 'none';
        }
    });
}

// 初始化所有新闻卡片为收起状态
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all news cards as collapsed
    document.querySelectorAll('.news-card').forEach(card => {
        if (!card.classList.contains('collapsed') && !card.classList.contains('expanded')) {
            card.classList.add('collapsed');
        }
    });

    // Add smooth scroll behavior
    document.documentElement.style.scrollBehavior = 'smooth';

    // Initialize archive item click handlers
    document.querySelectorAll('.archive-item').forEach(item => {
        item.addEventListener('click', function() {
            const dateStr = this.dataset.date;
            if (dateStr) {
                loadArchiveDate(dateStr);
            }
        });
    });

    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Press '/' to focus search (if implemented)
        if (e.key === '/' && !e.target.matches('input, textarea')) {
            e.preventDefault();
            const searchInput = document.querySelector('#search-input');
            if (searchInput) searchInput.focus();
        }

        // Press 'Escape' to clear search
        if (e.key === 'Escape') {
            const searchInput = document.querySelector('#search-input');
            if (searchInput) {
                searchInput.value = '';
                searchNews('');
            }
        }
    });

    console.log('AI News Daily loaded successfully');
});

// 导出到全局作用域
window.AINewsDaily = {
    toggleNews,
    loadArchiveDate,
    toggleMonthGroup,
    searchNews,
    filterByCategory
};
