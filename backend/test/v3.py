import os
from openai import OpenAI

client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key=os.getenv("DASHSCOPE_API_KEY"),

# sk-4f66bb55e47848c4b43c9cc2c61346fe
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
completion = client.chat.completions.create(
    model="qwen-turbo-0211",
    messages=[
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': '请帮我生成1段关于陌生交友和漂流瓶的文案，每段大约50-100字，风格要温暖、有趣且有吸引力。'}],
)

print(completion.choices[0].message.content)