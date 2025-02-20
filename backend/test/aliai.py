import os
from openai import OpenAI
from datetime import datetime  # 导入 datetime 模块

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),  # 从环境变量获取 API Key
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# 定义系统提示词，约束模型行为
system_prompt = """
你是一个专业的感情陪聊助手，专注于提供情感支持、倾听和安慰。
你的任务是：
1. 倾听用户的情感问题，给予温暖的回应。
2. 提供积极的情感建议，帮助用户缓解情绪。
3. 避免提供医学、法律等专业领域的建议。
4. 保持友好、耐心和同理心。
请始终围绕感情陪聊的主题进行回答。
"""

# 初始化对话上下文
messages = [
    {'role': 'system', 'content': system_prompt},  # 系统提示词
    {'role': 'user', 'content': '你好'}
]

# 第一轮对话
completion = client.chat.completions.create(
    model="deepseek-v3",  # 使用 deepseek-v3 模型
    messages=messages
)

# 打印第一轮对话结果
print("="*20+"第一轮对话"+"="*20)
print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ====================思考过程====================")
print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {completion.choices[0].message.reasoning_content}")
print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ====================最终答案====================")
print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {completion.choices[0].message.content}")

# 更新对话上下文
messages.append({'role': 'assistant', 'content': completion.choices[0].message.content})
messages.append({'role': 'user', 'content': '我最近心情很低落，怎么办？'})

# 第二轮对话
print("="*20+"第二轮对话"+"="*20)
completion = client.chat.completions.create(
    model="deepseek-v3",
    messages=messages
)

# 打印第二轮对话结果
print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ====================思考过程====================")
print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {completion.choices[0].message.reasoning_content}")
print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ====================最终答案====================")
print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {completion.choices[0].message.content}")