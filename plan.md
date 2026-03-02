# AI News Daily - 项目设计计划

## 项目概述

创建一个基于 `news-aggregator-skill` 的 AI 新闻展示网站，每天自动抓取 AI 相关重大新闻并提供优雅的阅读体验。

**项目名称**: `ai-news-daily`

**核心功能**:
- 每日自动抓取 AI 相关新闻
- 按天展示历史新闻
- 优雅的阅读体验
- 完全免费运行（GitHub Pages + GitHub Actions）

---

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub 仓库                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐      ┌──────────────────────────────┐   │
│  │ GitHub Pages │ ◄─── │  docs/ (前端静态站点)        │   │
│  │  (前端展示)  │      │  - index.html (今日新闻)     │   │
│  └──────────────┘      │  - archive.html (历史归档)   │   │
│         │              │  - news/YYYYMMDD.json        │   │
│         │              │  - assets/css/style.css      │   │
│         │              │  - assets/js/main.js         │   │
│         │              └──────────────────────────────┘   │
│         ▲                                                     │
│         │                                                     │
│  ┌──────┴──────────────────────────────────────────────┐    │
│  │  GitHub Actions (定时任务)                           │    │
│  │  ┌─────────────────────────────────────────────┐    │    │
│  │  │ .github/workflows/daily-fetch.yml            │    │    │
│  │  │  - 每天 UTC 00:00 触发                       │    │    │
│  │  │  - 运行 fetch_news.py                        │    │    │
│  │  │  - 生成 news/YYYYMMDD.json                   │    │    │
│  │  │  - 更新 index.html 和归档列表                │    │    │
│  │  └─────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  scripts/ (复用现有代码)                            │    │
│  │  └── fetch_news.py (从 skill 复制)                 │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 项目目录结构

```
ai-news-daily/
├── .github/
│   └── workflows/
│       └── daily-fetch.yml          # GitHub Actions 定时任务
├── docs/                             # GitHub Pages 网站根目录
│   ├── index.html                    # 首页（今日新闻）
│   ├── archive.html                  # 历史归档页
│   ├── news/                         # 新闻数据 JSON
│   │   ├── 20260302.json
│   │   ├── 20260301.json
│   │   └── ...
│   ├── assets/
│   │   ├── css/
│   │   │   └── style.css             # 样式文件
│   │   └── js/
│   │       └── main.js               # 前端交互逻辑
│   └── data/
│       └── archive-index.json        # 归档索引
├── scripts/
│   ├── fetch_news.py                 # 从 skill 复制
│   ├── generate_daily.py             # 生成每日新闻页面
│   └── update_archive.py             # 更新归档索引
├── requirements.txt                  # Python 依赖
├── README.md
├── plan.md                           # 本文件
└── todolist.md                       # 任务清单
```

---

## 核心组件设计

### 1. GitHub Actions 工作流 (.github/workflows/daily-fetch.yml)

```yaml
name: Daily News Fetch

on:
  schedule:
    - cron: '0 0 * * *'  # 每天 UTC 00:00 执行
  workflow_dispatch:      # 支持手动触发

permissions:
  contents: write

jobs:
  fetch-news:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Fetch today's news
        run: |
          DATE=$(date +%Y%m%d)
          python scripts/fetch_news.py \
            --source all \
            --limit 10 \
            --keyword "AI,LLM,GPT,Claude,DeepSeek,Agent,大模型,人工智能" \
            --deep \
            > "docs/news/${DATE}.json"

      - name: Generate index page
        run: python scripts/generate_daily.py

      - name: Update archive
        run: python scripts/update_archive.py

      - name: Commit changes
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add docs/
          git diff --staged --quiet || git commit -m "Update daily news $(date +%Y-%m-%d)"

      - name: Push changes
        uses: ad-m/github-push-action@master
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          branch: main
```

### 2. 前端页面设计

**设计风格**: ✅ 简洁杂志风 (Magazine Style)

**CSS 核心样式**:
```css
/* 字体 */
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=Inter:wght@400;500;600&display=swap');

/* 配色 */
:root {
    --bg-primary: #faf9f7;
    --bg-card: #ffffff;
    --text-primary: #1a1a1a;
    --text-secondary: #6b6b6b;
    --accent-red: #c41e3a;      /* 全球头条 */
    --accent-blue: #1e40af;     /* 科技开发 */
    --accent-green: #047857;    /* 中国科技 */
    --accent-amber: #b45309;    /* 产品猎场 */
    --border: #e5e5e5;
    --shadow: 0 1px 3px rgba(0,0,0,0.04);
}
```

**新闻展开功能**:
- 默认收起状态，显示标题 + 1行摘要
- 点击展开后显示详细摘要（100-500字）
- 【查看原文】按钮跳转到原链接
- 优雅的展开/收起动画

### 3. 历史归档页面 (docs/archive.html) - 混合模式

**归档策略**:
- 最近 30 天：按天展示，每天可展开查看详情
- 更早日期：按月折叠归档

**数据结构** (docs/data/archive-index.json):
```json
[
  {
    "date": "20260302",
    "formatted": "2026年3月2日",
    "count": 42,
    "top_news": "OpenAI 发布 GPT-5...",
    "categories": {
      "全球头条": 5,
      "科技与开发": 12,
      "中国科技圈": 8,
      "产品猎场": 6,
      "其他": 11
    }
  }
]
```

---

## 关键特性

### 1. 智能 AI 关键词扩展
```
用户输入: "AI"
扩展为: "AI,LLM,GPT,Claude,DeepSeek,Agent,大模型,人工智能,机器学习"
```

### 2. 新闻去重与合并
- 同一新闻多个源 → 合并显示来源
- 按热度/时间排序

### 3. 渐进式增强
- 基础版: 纯静态 HTML
- 增强版: JavaScript 加载历史、搜索功能

---

## 部署步骤

1. **创建 GitHub 仓库**
   ```bash
   git init ai-news-daily
   cd ai-news-daily
   ```

2. **复制文件**
   - 从 skill 复制 `fetch_news.py` 到 `scripts/`
   - 创建上述目录结构

3. **配置 GitHub Pages**
   - Settings → Pages → Source: `docs/` folder
   - 选择主题或使用自定义

4. **启用 GitHub Actions**
   - 推送代码后自动激活

5. **首次手动触发**
   - Actions → Daily News Fetch → Run workflow

---

## 成本与限制

| 项目 | 说明 |
|------|------|
| **托管费用** | 完全免费 |
| **域名** | `username.github.io` 免费，自定义域名需付费 |
| **执行频率** | GitHub Actions: 免费 2000 分钟/月 |
| **存储** | 仓库 1GB 免费，足够存储数年新闻 |
| **流量** | 100GB/月 免费带宽 |

---

## 技术栈总结

| 层级 | 技术 | 原因 |
|------|------|------|
| 前端 | HTML + CSS + Vanilla JS | 简单、无需构建、GitHub Pages 原生支持 |
| 后端 | Python + GitHub Actions | 复用 skill 代码，免费定时执行 |
| 存储 | Git 仓库 + JSON | 版本控制、免费、简单 |
| 部署 | GitHub Pages | 免费、HTTPS、CDN |

---

## 后续扩展选项

1. **评论系统** - 使用 GitHub Issues
2. **RSS 订阅** - 生成 RSS feed
3. **搜索功能** - 客户端 JavaScript 搜索
4. **邮件订阅** - 使用 Email Octopus 免费层
5. **Telegram Bot** - 推送每日新闻摘要

---

## ✅ 已确认选项

1. **页面设计风格**: ✅ 简洁杂志风 (Magazine Style)
2. **历史归档**: ✅ 混合模式 (最近30天按天，更早按月归档)
3. **订阅功能**: ✅ 暂不需要

---

## 实施状态

### 第一阶段：项目初始化 ✅
1. ✅ 创建 GitHub 仓库 `ai-news-daily`
2. ✅ 建立目录结构
3. ✅ 从 `news-aggregator-skill` 复制 `fetch_news.py` 到 `scripts/`

### 第二阶段：核心脚本开发 ✅
1. ✅ 复制 `scripts/fetch_news.py` - 新闻抓取脚本
2. ✅ 创建 `scripts/generate_daily.py` - 生成今日新闻页面
3. ✅ 创建 `scripts/update_archive.py` - 更新归档索引

### 第三阶段：前端开发 ✅
1. ✅ 创建 `docs/index.html` - 今日新闻首页
2. ✅ 创建 `docs/archive.html` - 混合模式归档页
3. ✅ 创建 `docs/assets/css/style.css` - 杂志风格样式
4. ✅ 创建 `docs/assets/js/main.js` - 前端交互

### 第四阶段：自动化配置 ✅
1. ✅ 创建 `.github/workflows/daily-fetch.yml`

### 第五阶段：测试与部署
1. ⏳ 本地测试所有脚本
    cd C:\Users\28412\Desktop\claude\news
    python -m http.server 8000 --directory docs
2. ⏳ 推送代码到 GitHub
3. ⏳ 验证 GitHub Actions 执行
4. ⏳ 验证 GitHub Pages 展示

---

## 关键文件清单

| 文件路径 | 说明 | 状态 |
|----------|------|------|
| `scripts/fetch_news.py` | 新闻抓取脚本 | ✅ 已创建 |
| `scripts/generate_daily.py` | 生成今日页面 | ✅ 已创建 |
| `scripts/update_archive.py` | 更新归档索引 | ✅ 已创建 |
| `docs/index.html` | 今日新闻首页 | ✅ 已创建 |
| `docs/archive.html` | 历史归档页 | ✅ 已创建 |
| `docs/assets/css/style.css` | 杂志风格样式 | ✅ 已创建 |
| `docs/assets/js/main.js` | 前端交互 | ✅ 已创建 |
| `.github/workflows/daily-fetch.yml` | 自动化工作流 | ✅ 已创建 |
| `requirements.txt` | Python 依赖 | ✅ 已创建 |
| `README.md` | 项目说明 | ✅ 已创建 |
| `plan.md` | 项目计划 | ✅ 已创建 |
| `todolist.md` | 任务清单 | ✅ 已创建 |
