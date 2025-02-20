import os
# 升级方舟 SDK 到最新版本 pip install -U 'volcengine-python-sdk[ark]'
from volcenginesdkarkruntime import Ark

client = Ark(
    # 从环境变量中读取您的方舟API Key
    api_key=os.environ.get("ARK_API_KEY"),
    # 深度推理模型耗费时间会较长，建议您设置一个较长的超时时间，推荐为30分钟
    timeout=1800,
    )
response = client.chat.completions.create(
    # 替换 <Model> 为模型的Model ID
    model="deepseek-r1-250120",
    messages=[
        {"role": "user", "content": "研究推理模型与非推理模型区别"},
        {"role": "assistant", "content": "推理模型主要依靠逻辑、规则或概率等进行分析、推导和判断以得出结论或决策，非推理模型则是通过模式识别、统计分析或模拟等方式来实现数据描述、分类、聚类或生成等任务而不依赖显式逻辑推理。"},
        {"role": "user", "content": "我要有研究推理模型与非推理模型区别的课题，怎么体现我的专业性"},
    ],
)

if hasattr(response.choices[0].message, 'reasoning_content'):
    print(response.choices[0].message.reasoning_content)
print(response.choices[0].message.content)