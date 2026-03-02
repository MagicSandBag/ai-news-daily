#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

# 设置 API Key
os.environ['DEEPSEEK_API_KEY'] = 'sk-00ed249fa4ac4552a5a8729690fc6f9b'

sys.path.insert(0, 'scripts')
from translator import translate_title, translate_summary

# 测试标题翻译
test_titles = [
    'If AI writes code, should the session be part of the commit?',
    'Right-sizes LLM models to your system RAM, CPU, and GPU',
    'I built a demo of what AI chat will look like when it is free and ad-supported',
]

print('=== DeepSeek API 翻译测试 ===\n')

for i, title in enumerate(test_titles, 1):
    print(f'{i}. 原文: {title}')
    translated = translate_title(title)
    print(f'   译文: {translated}')
    print()

# 测试摘要翻译
test_content = '''
GitHub - mandel-macaque/memento: Keep track of you codex sessions per commit.
git memento is a Git extension that records the AI coding session used to produce a commit.
It runs a commit and then stores a cleaned markdown conversation as a git note on the new commit.
'''

print('=== 摘要翻译测试 ===')
print(f'原文内容: {test_content[:100]}...')
summary = translate_summary(test_content, test_titles[0])
print(f'中文摘要: {summary}')
