# AI News Daily

> 每日自动抓取 AI 相关重大新闻并提供优雅的阅读体验

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub Actions](https://github.com/yourusername/ai-news-daily/workflows/Daily%20News%20Fetch/badge.svg)](.github/workflows/daily-fetch.yml)

## 项目简介

AI News Daily 是一个基于 GitHub Pages 和 GitHub Actions 的自动化新闻聚合网站，每天自动抓取 AI 相关的重大新闻，并以简洁杂志风格展示。

### 核心特性

- 🔔 **每日自动更新** - GitHub Actions 定时抓取，无需人工干预
- 📰 **多源聚合** - 整合 Hacker News、GitHub Trending、36Kr、Product Hunt 等多个来源
- 🎨 **杂志风格** - 简洁优雅的阅读体验，支持响应式和暗色模式
- 📚 **历史归档** - 按天/月归档，方便查找历史新闻
- 🆓 **完全免费** - 基于 GitHub 免费服务运行，无额外成本

## 在线访问

- **首页**: https://magicsandbag.github.io/ai-news-daily/

## 项目结构

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
│   │   └── ...
│   ├── data/
│   │   └── archive-index.json        # 归档索引
│   └── assets/
│       ├── css/
│       │   └── style.css             # 杂志风格样式
│       └── js/
│           └── main.js               # 前端交互
├── scripts/
│   ├── fetch_news.py                 # 新闻抓取脚本
│   ├── generate_daily.py             # 生成每日页面
│   └── update_archive.py             # 更新归档
├── requirements.txt                  # Python 依赖
└── README.md
```

## 本地开发

### 环境要求

- Python 3.12+
- pip

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行脚本

```bash
# 抓取今日新闻
python scripts/fetch_news.py --source all --limit 10 --keyword "AI,LLM,GPT" --deep

# 生成首页
python scripts/generate_daily.py

# 更新归档
python scripts/update_archive.py
```

### 本地预览

使用任何静态服务器预览 `docs/` 目录：

```bash
# 使用 Python
python -m http.server 8000 --directory docs

# 使用 npx
npx serve docs
```

然后访问 http://localhost:8000

## 部署到 GitHub

### 1. 创建仓库

点击 GitHub 上的 "Use this template" 或 Fork 本仓库。

### 2. 启用 GitHub Pages

1. 进入仓库 Settings
2. 选择 Pages
3. Source 选择 `docs/` folder
4. 选择分支（通常是 main 或 master）
5. 保存

### 3. 启用 GitHub Actions

推送代码后，GitHub Actions 会自动运行。你也可以手动触发：

1. 进入 Actions 页面
2. 选择 "Daily News Fetch" workflow
3. 点击 "Run workflow"

### 4. 配置定时任务

默认配置为每天 UTC 00:00 运行。可在 `.github/workflows/daily-fetch.yml` 中修改：

```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # 每天 UTC 00:00
    - cron: '0 8 * * *'  # 每天 UTC 08:00 (北京时间 16:00)
```

## 数据来源

- **Hacker News** - 全球科技新闻
- **GitHub Trending** - 开源项目趋势
- **36Kr** - 中国科技创业资讯
- **Product Hunt** - 产品发现平台
- **V2EX** - 中文技术社区
- **腾讯新闻** - 综合新闻
- **华尔街见闻** - 财经资讯
- **微博热搜** - 实时热点

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | HTML + CSS + Vanilla JS | 简单、无需构建、GitHub Pages 原生支持 |
| 后端 | Python + GitHub Actions | 复用 skill 代码，免费定时执行 |
| 存储 | Git 仓库 + JSON | 版本控制、免费、简单 |
| 部署 | GitHub Pages | 免费、HTTPS、CDN |

## 设计风格

项目采用 **简洁杂志风 (Magazine Style)** 设计，参考 The Economist 和 Morning Brew 的视觉风格：

- 衬线字体标题 (Noto Serif SC)
- 优雅的卡片式布局
- 柔和的阴影效果
- 颜色标签区分分类
- 干净的留白和行距
- 支持暗色模式

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 贡献

欢迎提交 Issue 和 Pull Request！

## 鸣谢

- 基于 [news-aggregator-skill](https://github.com/anthropics/anthropic-quickstarts) 构建
- 设计灵感来自 [The Economist](https://www.economist.com/) 和 [Morning Brew](https://www.morningbrew.com/)

---

**Made with ❤️ for AI enthusiasts**
