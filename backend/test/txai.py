import os
from openai import OpenAI

client = OpenAI(
    # 请用知识引擎原子能力API Key将下行替换为：api_key="sk-xxx",
    api_key="sk-fjnWvbJyVJp5twfKcA31jRnZOd060DlgzBwMdZFZbgTxuZ23", # 如何获取API Key：https://cloud.tencent.com/document/product/1772/115970
    base_url="https://api.lkeap.cloud.tencent.com/v1",
)

completion = client.chat.completions.create(
    model="deepseek-r1",  # 此处以 deepseek-r1 为例，可按需更换模型名称。
    messages=[
        {'role': 'user', 'content': '有哪些让你颠覆三观的社会真相?社会不教,精英不说,有些东西没人点拨,你未必知道,普通人如何破局。说直白一点,通透一点,可以说脏话!'}
        ]
)

# 通过reasoning_content字段打印思考过程
print("思考过程：")
print(completion.choices[0].message.reasoning_content)
# 通过content字段打印最终答案
print("最终答案：")
print(completion.choices[0].message.content)