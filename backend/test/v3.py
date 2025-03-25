# import os
# from openai import OpenAI
#
# # 初始化 OpenAI 客户端
# client = OpenAI(
#     # 如果没有配置环境变量，请直接替换为您的 API Key，例如：api_key="sk-xxx"
#     api_key=os.getenv("DASHSCOPE_API_KEY"),
#     base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # 阿里云 OpenAI 兼容接口地址
# )
#
# # 调用模型生成文案
# completion = client.chat.completions.create(
#     model="qwen-max-0125 ",  # 使用的模型名称，可根据需求更换    qwen-turbo-0211
#     messages=[
#         {'role': 'system', 'content': '你是一位创意十足的社交文案专家，专门为社交应用创作拟人化的打招呼文案。'},
#         {'role': 'user', 'content': '请帮我生成1段大约50-100字，风格要温暖、有趣且有吸引力，文案内容尽可能千人千变'}
#     ],
# )
#
# # 打印生成的文案
# print(completion.choices[0].message.content)
import os
from openai import OpenAI

client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

completion = client.chat.completions.create(
    model="qwen-max-0125",  # 此处以qwen-plus为例，您可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
    messages=[
        {'role': 'system', 'content': '你是一位创意十足的社交文案专家，专门为社交应用创作拟人化的打招呼文案。'},
        {'role': 'user', 'content': '请帮我生成1段大约50-100字，风格要温暖、有趣且有吸引力，文案内容尽可能千人千变'}
    ],
    stream=True
)

full_content = ""
print("流式输出内容为：")
for chunk in completion:
    # 如果stream_options.include_usage为True，则最后一个chunk的choices字段为空列表，需要跳过（可以通过chunk.usage获取 Token 使用量）
    if chunk.choices:
        full_content += chunk.choices[0].delta.content
        print(chunk.choices[0].delta.content)
print(f"完整内容为：{full_content}")