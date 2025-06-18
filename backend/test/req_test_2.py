import requests
import time

url = "https://stage-api-meeting.weizhiyanchina.com/web/act/award/open"
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-cn",
    "Accept-Encoding": "br, gzip, deflate",
    "Token": "3RkN8lf24ODCwAAsfZssfdxapnBaWLGTsT3fppoaCd4=",
    "X-Request-Id": "1cc6eefe-b4c7-4c6e-b88c-6ff67d391d2f",
    "Origin": "https://stage-activity.weizhiyanchina.com",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 12_5_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
    "Referer": "https://stage-activity.weizhiyanchina.com/duanwu-fest/"
}

data = {
    "act_code": "DUANWU2025",
    "group_module": 3,
    "amount": 1
}


response = requests.post(url, headers=headers, json=data)
print(f"Status Code: {response.status_code}")

# 设置编码为 UTF-8（或其他合适的编码）
response.encoding = 'utf-8'  # 根据实际情况调整编码
print(f"Response Text: {response.text}")

try:
    json_response = response.json()
    print(f"Response JSON: {json_response}")
except ValueError as e:
    print(f"JSON decode error: {e}")

time.sleep(1)  # 等待 1 秒钟再发送下一个请求
