import os
# 升级方舟 SDK 到最新版本 pip install -U 'volcengine-python-sdk[ark]'
from volcenginesdkarkruntime import Ark

client = Ark(
    # 从环境变量中读取您的方舟API Key
    api_key=os.environ.get("ARK_API_KEY"),

    #  key  e1648dc9-9639-4cab-8364-2164e5ceac05
    # 深度推理模型耗费时间会较长，建议您设置一个较长的超时时间，推荐为30分钟
    timeout=1800,
)

# 用户可选择的风格类型
style = "活泼友善"  # 可以是：可爱萌系、活泼友善、暖心治愈、幽默逗趣、神秘奇幻等

response = client.chat.completions.create(
    # 使用 deepseek-r1 模型
    model="doubao-1-5-lite-32k-250115",
    messages=[
        {"role": "system", "content": f"""
        你是一位创意十足的社交文案专家，专门为漂流瓶社交应用创作拟人化的打招呼文案。

        请以"{style}"的风格，创作3条拟人化的打招呼文案。这些文案将被用作漂流瓶中的第一句话，
        用来吸引陌生人的注意并开启愉快的对话。

        文案要求：
        1. 每条30-50字左右
        2. 使用拟人化的语气，仿佛文字本身是有生命的
        3. 活泼有趣，富有个性
        4. 适合陌生人之间初次打招呼
        5. 内容健康积极
        6. 不要出现漂流瓶的字样
        7. 结尾可以带有简单的互动引导

        直接输出文案内容，每条文案用两个换行符分隔，无需编号。
        """},
        {"role": "user", "content": "请生成漂流瓶打招呼文案"},
    ],
    temperature=0.8,
    max_tokens=500
)

# 如果有推理内容，则打印出来
# if hasattr(response.choices[0].message, 'reasoning_content'):
#     print("思考过程：")
#     print(response.choices[0].message.reasoning_content)

# 打印最终生成的文案
print("\n生成的漂流瓶文案：")
print(response.choices[0].message.content)
