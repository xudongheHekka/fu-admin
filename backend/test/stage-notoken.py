import requests
import time  # 用于添加延迟（如果需要）

# 接口地址
url = "https://stage-api-meeting.weizhiyanchina.com/web/user/cola/engine"  # 替换为实际的接口地址

# 请求参数（Form Data）
data = {
    "uid": 10700301,
    "module_name": "h5recharge",
    "event_name": "h5recharge",
    "amount": 8,
    "os": "ios"
}

# 请求头（如果需要额外的头部信息，可以在这里添加）
headers = {
    "Content-Type": "application/x-www-form-urlencoded",  # 表单数据格式
    # 如果需要认证，可以添加以下内容
    # "Authorization": "Bearer your-token"
}

# 循环发送请求 100 次
for i in range(1, 101):  # 从 1 到 100
    try:
        # 发送 POST 请求
        response = requests.post(url, data=data, headers=headers)

        # 打印每次请求的结果
        print(f"第 {i} 次请求:")
        print("状态码:", response.status_code)
        print("响应内容:", response.text)

        # 如果需要延迟，可以取消注释以下代码
        # time.sleep(1)  # 延迟 1 秒，避免过于频繁的请求

    except requests.exceptions.RequestException as e:
        print(f"第 {i} 次请求失败:", e)
