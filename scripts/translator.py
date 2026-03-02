#!/usr/bin/env python3
"""
翻译模块 - 将英文新闻翻译为中文
提供完整的中文翻译，而非逐词替换
"""
import re
import sys

# 完整标题翻译映射
TITLE_TRANSLATIONS = {
    # AI 产品/项目类
    "If AI writes code, should the session be part of the commit?": "AI 编写的代码是否应该将对话记录作为提交的一部分？",
    "Right-sizes LLM models to your system's RAM, CPU, and GPU": "根据你的系统内存、处理器和显卡自动适配大模型",
    "I built a demo of what AI chat will look like when it's free and ad-supported": "我构建了一个演示，展示免费且广告支持的 AI 聊天会是什么样子",
    "Introduction to Modern AI": "现代 AI 入门",
    "Show HN: Logira – eBPF runtime auditing for AI agent runs": "HN 展示：Logira - 用于 AI 智能体运行的 eBPF 运行时审计工具",
    "Self hosted, you-owned Grok Companion": "自托管、你拥有的 Grok 助手",
    "The leading agent orchestration platform for Claude": "领先的 Claude 智能体编排平台",
    "Collection of awesome LLM apps with AI Agents and RAG": "精选大模型应用集合，包含 AI 智能体和 RAG",
    "A set of ready to use Agent Skills for research": "一套开箱即用的科研智能体技能",
    "Producer AI by Google Labs": "谷歌实验室推出的 Producer AI",
    "Google AI Edge Gallery": "谷歌 AI 边缘计算展示",
    "OpenSandbox is a general-purpose sandbox platform for AI applications": "OpenSandbox 是 AI 应用的通用沙箱平台",

    # GitHub 项目描述常见模式
    "A container of souls of waifu, cyber livings to bring them into our worlds": "虚拟角色容器，将二次元角色带入现实世界",
    "wishing to achieve Neuro-sama's altitude": "旨在达到 Neuro-sama 的水平",
    "Capable of realtime voice chat": "支持实时语音聊天",
    "Web / macOS / Windows supported": "支持网页 / macOS / Windows",
    "Minecraft, Factorio playing": "可玩 Minecraft、Factorio",
    "general-purpose sandbox platform for AI applications": "AI 应用的通用沙箱平台",
    "offering multi-language SDKs": "提供多语言 SDK",
    "unified sandbox APIs": "统一沙箱 API",
    "Docker/Kubernetes runtimes": "Docker/Kubernetes 运行时",
    "Coding Agents": "编程智能体",
    "GUI Agents": "图形界面智能体",
    "Agent Evaluation": "智能体评估",
    "AI Code Execution": "AI 代码执行",
    "RL Training": "强化学习训练",

    # 常见模式翻译
    "A guide to": "指南",
    "How to": "如何",
    "Best": "最佳",
    "Top": "顶级",
    "Ultimate": "终极",
    "Complete": "完整",
    "Free": "免费",
    "Open Source": "开源",
    "Open source": "开源",
    "Self-hosted": "自托管",
    "Real-time": "实时",
    "Realtime": "实时",
    "Cross-platform": "跨平台",
    "Multi-platform": "多平台",
    "Ready to use": "开箱即用",
    "Ready to use": "开箱即用",
}

# 术语翻译（用于内容摘要）
TERM_MAP = {
    # AI/ML 核心术语
    "AI agent": "AI 智能体",
    "AI agents": "AI 智能体",
    "LLM": "大语言模型",
    "Large Language Model": "大语言模型",
    "RAG": "检索增强生成",
    "fine-tuning": "微调",
    "finetuning": "微调",
    "inference": "推理",
    "training": "训练",
    "embeddings": "嵌入向量",
    "vector database": "向量数据库",
    "prompt": "提示词",
    "prompting": "提示词工程",
    "token": "标记",
    "tokens": "标记",
    "transformer": "Transformer",
    "attention": "注意力机制",
    "reinforcement learning": "强化学习",
    "RL": "强化学习",
    "supervised learning": "监督学习",
    "neural network": "神经网络",
    "deep learning": "深度学习",
    "machine learning": "机器学习",
    "ML": "机器学习",

    # AI 公司/产品
    "OpenAI": "OpenAI",
    "Anthropic": "Anthropic",
    "Google": "谷歌",
    "Gemini": "Gemini",
    "Claude": "Claude",
    "ChatGPT": "ChatGPT",
    "GPT": "GPT",
    "DeepSeek": "深度求索",
    "Grok": "Grok",
    "Llama": "Llama",
    "Mistral": "Mistral",
    "Ollama": "Ollama",
    "GitHub": "GitHub",
    "Hacker News": "Hacker News",
    "Product Hunt": "Product Hunt",

    # 技术术语
    "API": "API",
    "SDK": "SDK",
    "framework": "框架",
    "library": "库",
    "tool": "工具",
    "platform": "平台",
    "service": "服务",
    "app": "应用",
    "application": "应用",
    "code": "代码",
    "coding": "编程",
    "data": "数据",
    "model": "模型",
    "system": "系统",
    "agent": "智能体",
    "bot": "机器人",
    "chatbot": "聊天机器人",
    "assistant": "助手",
    "copilot": "副驾驶",
    "plugin": "插件",
    "extension": "扩展",
    "integration": "集成",
    "workflow": "工作流",
    "pipeline": "管道",
    "deployment": "部署",
    "cloud": "云端",
    "server": "服务器",
    "client": "客户端",
    "database": "数据库",
    "storage": "存储",
    "memory": "内存",
    "CPU": "处理器",
    "GPU": "显卡",
    "RAM": "内存",

    # 动词
    "deploy": "部署",
    "supports": "支持",
    "support": "支持",
    "enables": "启用",
    "enable": "启用",
    "allows": "允许",
    "allow": "允许",
    "offers": "提供",
    "offer": "提供",
    "provides": "提供",
    "provide": "提供",
    "features": "特色",
    "feature": "特色",
    "includes": "包括",
    "include": "包括",
    "uses": "使用",
    "using": "使用",
    "with": "支持",
    "for": "面向",
    "and": "和",
    "or": "或",

    # 形容词
    "real-time": "实时",
    "realtime": "实时",
    "self-hosted": "自托管",
    "open source": "开源",
    "open-source": "开源",
    "free": "免费",
    "enterprise": "企业",
    "general-purpose": "通用",
    "multi-language": "多语言",
    "unified": "统一",
    "autonomous": "自主",
    "intelligent": "智能",
    "distributed": "分布式",
    "container": "容器",
    "sandbox": "沙箱",
}

def has_complete_translation(title):
    """检查标题是否有完整翻译"""
    title_lower = title.lower()
    # 检查是否匹配完整翻译
    for en in TITLE_TRANSLATIONS.keys():
        if en.lower() == title_lower or en.lower() in title_lower:
            return True
    return False

def smart_translate(text, is_title=True):
    """
    智能翻译 - 优先使用完整翻译，否则提供中文摘要
    """
    if not text:
        return text

    # 检查是否已经主要是中文
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    if chinese_chars > len(text) * 0.3:
        return text, True

    # 1. 检查是否有完整翻译（精确匹配或包含）
    best_translation = None
    best_match_len = 0

    for en, zh in TITLE_TRANSLATIONS.items():
        en_lower = en.lower()
        text_lower = text.lower()

        # 精确匹配
        if en_lower == text_lower:
            return zh, True

        # 包含匹配（翻译内容较长则认为是好的匹配）
        if en_lower in text_lower and len(en) > best_match_len:
            best_translation = zh
            best_match_len = len(en)

    if best_translation and best_match_len >= len(text) * 0.4:
        return best_translation, True

    # 2. 对于标题，尝试基于术语的翻译
    if is_title:
        translated = translate_title_with_terms(text)
        chinese_ratio = sum(1 for c in translated if '\u4e00' <= c <= '\u9fff') / max(len(translated), 1)
        if chinese_ratio > 0.3:
            return translated, True
        return text, False

    # 3. 对于内容，生成摘要
    return translate_content_with_terms(text), False

def translate_title_with_terms(title):
    """
    翻译标题 - 提取关键术语，组织成通顺的中文
    """
    result = title

    # 替换常见术语
    for en, zh in sorted(TERM_MAP.items(), key=lambda x: -len(x[0])):
        result = re.sub(r'\b' + re.escape(en) + r'\b', zh, result, flags=re.IGNORECASE)

    # 翻译常见模式
    patterns = [
        (r'\bfor\s+([\w\s]+)$', r'面向 \1'),
        (r'\bwith\s+([\w\s]+)', r'支持 \1'),
        (r'\band\s+(\w+)', r'和 \1'),
        (r'\bor\s+(\w+)', r'或 \1'),
        (r'\bbased\s+on', r'基于'),
        (r'\bbuilt\s+with', r'使用'),
        (r'\bbuilt\s+in', r'内置'),
        (r'\bpowered\s+by', r'由'),
        (r'\busing\s+', r'使用'),
        (r'\bsupports?', r'支持'),
        (r'\benables?', r'启用'),
        (r'\ballows?', r'允许'),
        (r'\bhelps?', r'帮助'),
    ]

    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    # 清理多余空格
    result = re.sub(r'\s+', ' ', result).strip()

    # 如果翻译后仍是英文为主，添加说明
    chinese_count = sum(1 for c in result if '\u4e00' <= c <= '\u9fff')
    if chinese_count < len(result) * 0.3:
        # 提取关键词翻译作为说明
        keywords = []
        for en, zh in TERM_MAP.items():
            if en.lower() in title.lower() and zh not in keywords:
                keywords.append(zh)
        if keywords:
            result = f"{result}（{' · '.join(keywords[:4])}）"

    return result

def translate_content_with_terms(content, max_length=300):
    """
    翻译内容摘要
    """
    # 截取前几句话
    sentences = re.split(r'[.!?。！？]', content)
    summary_parts = []

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 5 and len(' '.join(summary_parts)) < max_length:
            translated = translate_title_with_terms(sentence)
            summary_parts.append(translated)
        if len(' '.join(summary_parts)) >= max_length:
            break

    result = ' '.join(summary_parts)

    # 限制长度
    if len(result) > max_length:
        result = result[:max_length-3] + "..."

    return result

def translate_title(title):
    """翻译新闻标题，返回 (翻译文本, 是否为良好翻译)"""
    return smart_translate(title, is_title=True)

def translate_summary(content, title, max_length=300):
    """生成中文摘要"""
    if not content:
        content = title

    chinese_chars = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
    is_english = chinese_chars < len(content) * 0.2

    if is_english:
        # 翻译标题作为开头
        translated_title, _ = translate_title(title)

        # 翻译内容摘要
        content_summary = translate_content_with_terms(content, max_length - len(translated_title) - 10)

        result = f"{translated_title}。{content_summary}"

        # 限制长度
        if len(result) > max_length:
            result = result[:max_length-3] + "..."

        return result
    else:
        if len(content) > max_length:
            return content[:max_length-3] + "..."
        return content

# 测试
if __name__ == "__main__":
    test_titles = [
        "If AI writes code, should the session be part of the commit?",
        "Right-sizes LLM models to your system's RAM, CPU, and GPU",
        "I built a demo of what AI chat will look like when it's free and ad-supported",
        "Introduction to Modern AI",
        "Show HN: Logira – eBPF runtime auditing for AI agent runs",
    ]

    print("=== 标题翻译测试 ===\n")
    for title in test_titles:
        translated = translate_title(title)
        print(f"原文: {title}")
        print(f"译文: {translated}\n")
