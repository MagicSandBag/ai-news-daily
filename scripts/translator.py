#!/usr/bin/env python3
"""
翻译模块 - 使用 DeepSeek API 将英文新闻翻译为中文
"""
import os
import json
import re
import sys

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# 本地回退翻译（当 API 不可用时）
FALLBACK_TRANSLATIONS = {
    "If AI writes code, should the session be part of the commit?": "AI 编写的代码是否应该将对话记录作为提交的一部分？",
    "Right-sizes LLM models to your system's RAM, CPU, and GPU": "根据你的系统内存、处理器和显卡自动适配大模型",
    "I built a demo of what AI chat will look like when it's free and ad-supported": "我构建了一个演示，展示免费且广告支持的 AI 聊天会是什么样子",
    "Introduction to Modern AI": "现代 AI 入门",
    "Show HN: Logira – eBPF runtime auditing for AI agent runs": "HN 展示：Logira - 用于 AI 智能体运行的 eBPF 运行时审计工具",
    "Self hosted, you-owned Grok Companion": "自托管、你拥有的 Grok 助手",
    "Producer AI by Google Labs": "谷歌实验室推出的 Producer AI",
    "Google AI Edge Gallery": "谷歌 AI 边缘计算展示",
    "OpenSandbox is a general-purpose sandbox platform for AI applications": "OpenSandbox 是 AI 应用的通用沙箱平台",
    "A set of ready to use Agent Skills for research": "一套开箱即用的科研智能体技能",
}


def translate_with_deepseek(text, max_retries=2):
    """
    使用 DeepSeek API 翻译文本
    """
    api_key = os.getenv("DEEPSEEK_API_KEY") or DEEPSEEK_API_KEY
    if not api_key:
        print("Warning: DEEPSEEK_API_KEY not set", file=sys.stderr)
        return None

    try:
        import requests

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # 使用 deepseek-chat 模型
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的科技新闻翻译。请将英文新闻标题和内容翻译成简体中文。要求：1. 保持专业术语的准确性（如 AI、LLM、GPT、Claude、RAG 等）2. 翻译要自然流畅符合中文表达习惯 3. 直接返回翻译结果，不要添加任何解释 4. 对于专有名词（如人名、公司名、产品名）请保持原文或使用通用译名"
                },
                {
                    "role": "user",
                    "content": f"请将以下新闻标题翻译成简体中文（只返回翻译结果）:\n\n{text}"
                }
            ],
            "temperature": 0.3,
            "max_tokens": 500
        }

        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            result = response.json()
            translated = result["choices"][0]["message"]["content"].strip()
            # 移除可能的引号
            translated = translated.strip('"\'""''')
            return translated
        else:
            print(f"DeepSeek API error: {response.status_code}", file=sys.stderr)
            return None

    except Exception as e:
        print(f"DeepSeek API exception: {e}", file=sys.stderr)
        return None


def translate_title(title):
    """
    翻译新闻标题
    优先使用 DeepSeek API，失败时使用本地翻译
    """
    if not title:
        return "无标题"

    # 检查是否已经主要是中文
    chinese_chars = sum(1 for c in title if '\u4e00' <= c <= '\u9fff')
    if chinese_chars > len(title) * 0.4:
        return title

    # 尝试使用 DeepSeek API
    translated = translate_with_deepseek(title)

    if translated:
        return translated

    # API 失败，使用本地翻译
    for en, zh in FALLBACK_TRANSLATIONS.items():
        if en.lower() in title.lower():
            return zh

    # 无法翻译，返回原标题
    return title


def translate_summary(content, title, max_length=600):
    """
    生成中文摘要
    使用 DeepSeek API 翻译和摘要
    """
    if not content:
        content = title

    # 检查是否已经主要是中文
    chinese_chars = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
    if chinese_chars > len(content) * 0.3:
        # 已经是中文，确保有足够长度
        if len(content) > max_length:
            return content[:max_length-3] + "..."
        return content if len(content) >= 100 else content[:max_length]

    # 对于英文内容，使用 DeepSeek API 翻译并生成摘要
    api_key = os.getenv("DEEPSEEK_API_KEY") or DEEPSEEK_API_KEY
    if api_key:
        try:
            import requests

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            # 准备内容（使用更多内容来生成更长的摘要）
            content_to_translate = content[:3000] if len(content) > 3000 else content

            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": f"你是一个科技新闻编辑。请将英文新闻内容翻译并整理成简体中文摘要。要求：1. 翻译准确自然 2. 提取关键信息和技术细节 3. 控制在 {max_length} 字以内 4. 不要只重复标题，要提供实质性的内容摘要 5. 保持专业术语原文（AI、LLM、GPT、Claude、RAG、GitHub、API等） 6. 包含项目的核心功能、特点或价值 7. 直接返回摘要，不要添加任何额外说明"
                    },
                    {
                        "role": "user",
                        "content": f"新闻标题：{title}\n\n新闻内容：{content_to_translate}\n\n请生成详细的中文摘要（{max_length}字以内）："
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 1000
            }

            response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)

            if response.status_code == 200:
                result = response.json()
                summary = result["choices"][0]["message"]["content"].strip()
                # 移除可能的引号和多余标记
                summary = summary.strip('"\'""''').strip()
                # 移除可能的 "摘要：" 前缀
                summary = re.sub(r'^摘要[:：]\s*', '', summary)
                # 移除可能重复的标题
                summary = re.sub(re.escape(title), '', summary, flags=re.IGNORECASE)
                # 清理
                summary = re.sub(r'^[、，。]\s*', '', summary.strip())
                if len(summary) < 50:
                    summary = f"{title}。{summary}"
                return summary

        except Exception as e:
            print(f"DeepSeek summary API exception: {e}", file=sys.stderr)

    # API 失败，生成本地摘要
    return generate_fallback_summary(content, title, max_length)


def generate_fallback_summary(content, title, max_length=600):
    """生成回退摘要（当 API 不可用时）"""
    # 提取标题翻译作为开头
    translated_title = translate_title(title)

    # 提取内容关键句子
    sentences = re.split(r'[.!?]+', content)
    key_sentences = []

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 15 and len(' '.join(key_sentences)) < max_length - 100:
            key_sentences.append(sentence)

    if key_sentences:
        # 组合摘要
        summary = translated_title + "。"
        for sent in key_sentences[:3]:
            if len(summary) + len(sent) < max_length - 20:
                summary += sent + "。"

        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."

        return summary

    return translated_title


# 批量翻译（用于批量处理，减少 API 调用）
def translate_batch(items, api_call_limit=10):
    """
    批量翻译新闻列表
    """
    import time
    translated_items = []

    for i, item in enumerate(items):
        # 设置 API Key（如果需要动态设置）
        api_key = os.getenv("DEEPSEEK_API_KEY") or DEEPSEEK_API_KEY
        if api_key:
            os.environ["DEEPSEEK_API_KEY"] = api_key

        translated_item = item.copy()
        translated_item["title_zh"] = translate_title(item.get("title", ""))
        translated_item["summary_zh"] = translate_summary(
            item.get("content", ""),
            item.get("title", "")
        )
        translated_items.append(translated_item)

        # API 调用间隔，避免超时
        if i < len(items) - 1:
            time.sleep(1)  # 增加到1秒间隔

    return translated_items


# 测试代码
if __name__ == "__main__":
    # 测试翻译
    test_title = "If AI writes code, should the session be part of the commit?"

    print("=== DeepSeek API 翻译测试 ===\n")
    print(f"原文: {test_title}")

    if DEEPSEEK_API_KEY:
        print("使用 DeepSeek API 翻译...")
    else:
        print("未设置 DEEPSEEK_API_KEY，使用本地翻译")

    translated = translate_title(test_title)
    print(f"译文: {translated}")
