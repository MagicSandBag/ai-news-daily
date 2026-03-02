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
function loadArchiveDate(dateStr) {
    // For now, just redirect to the specific date's JSON
    // In a full implementation, this would load the content dynamically
    console.log('Loading archive for:', dateStr);

    // Show loading state
    const archiveItems = document.querySelectorAll('.archive-item');
    archiveItems.forEach(item => {
        item.style.opacity = '0.5';
    });

    // In a real app, you would fetch the JSON and render the news
    // For now, we'll just show an alert
    setTimeout(() => {
        archiveItems.forEach(item => {
            item.style.opacity = '1';
        });
        alert('归档详情功能开发中...\n日期: ' + dateStr);
    }, 300);
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
