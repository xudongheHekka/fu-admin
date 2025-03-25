import os
from openai import OpenAI

client = OpenAI(
    api_key="sk-fjnWvbJyVJp5twfKcA31jRnZOd060DlgzBwMdZFZbgTxuZ23",
    base_url="https://api.lkeap.cloud.tencent.com/v1",
)

# 用户可选择的风格类型
style = "可爱萌系"  # 可以是：可爱萌系、活泼友善、暖心治愈、幽默逗趣、神秘奇幻等

completion = client.chat.completions.create(
    model="hunyuan-turbo",
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
        6. 结尾可以带有简单的互动引导

        直接输出文案内容，无需编号或其他格式。
        """},

        {"role": "user", "content": "请生成漂流瓶打招呼文案"}
    ],
    temperature=0.8,
    max_tokens=500
)

print("生成的漂流瓶文案：")
print(completion.choices[0].message.content)
