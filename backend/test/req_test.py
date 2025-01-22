import hashlib
import json
import requests
import time


# 常量
class Constant:
    HEADER_SIGN_KEY = "your_sign_key"  # 替换为实际的签名密钥


# 公共工具类
class CommonUtil:
    header = {
        "APP_VER": "1.0.0",
        "APP_USER_AGENT": "YourApp/1.0.0",
        "MARKET": "GooglePlay",
        "AD_ID": "ad_id_value",
        "AID": "aid_value",
        "OA_ID": "oa_id_value"
    }

    @staticmethod
    def log(message):
        print(message)


# 签名生成函数
def _build_sign(data):
    """
    构建签名
    :param data: 请求数据
    :return: 签名字符串
    """
    body = json.dumps(data) + Constant.HEADER_SIGN_KEY
    digest = hashlib.md5(body.encode('utf-8')).hexdigest()
    return digest


# 请求拦截器
def on_request(data):
    """
    在请求之前添加必要的头部信息
    :param data: 请求数据
    :return: headers
    """
    headers = {
        "token": "j3uKGGKPxBizjXBC7HSNGONAo+qEhXvi+7NGiOyyEbCEFV8wvhpKDmXnV5rqlt/X1qJHzal14ml3Scgcqg834aGTOWZkRKKLna/8mrsi0s8=",
        "content-type": "application/json",
        "ver": "1.0.0",  # 替换为版本号
        "User-Agent": CommonUtil.header.get("APP_USER_AGENT", "null"),  # 如果为空则设置为null
        "market": "HUAWEI",  # 替换为市场信息
        "sign": _build_sign(data),  # 签名
        "adid": "1a62ed4a114a4f269178c2d618f23656",  # 替换为广告ID
        "aid": "46166ee15da1c069",  # 替换为AID
        "oaid": CommonUtil.header.get("OA_ID", "null"),  # 如果为空则设置为null
        "ts": str(int(time.time() * 1000)),  # 当前系统时间戳（毫秒级，13位）
        "os": "2"  # 操作系统标识
    }

    return headers


# chatBanCall函数
def chat_ban_call(uid, enable):
    """
    调用chatBanCall接口
    :param uid: 用户ID
    :param enable: 是否禁用（True/False）
    :return: 接口响应
    """
    url = "https://api-meeting.weizhiyanchina.com/chat/ban_call"  # 替换为实际的API地址
    data = {
        "os": "harmony",
        "country_code": "86",
        "aid": "46166ee15da1c069",
        "app_id": 1,
        "app_type": 1,
        "de_type": 0,
        "dr_type": 0,
        "is_nim": 1,
        "umid": "3a249b464a071ca1bb6500b2ccc5c630od",
        "ver": "1.0.0",
        "stid": "CQKG64fbV5S3gDtwRxIXJg==",
        "adid": "1a62ed4a114a4f269178c2d618f23656",
        "market": "HUAWEI",
        "p_mftr": "HUAWEI",
        "p_model": "HUAWEI Mate 60 Pro",
        "os_ver": "13",
        "screen_height": 1260,
        "screen_width": 2720,
        "ts": "1737509184258",
        "act_type": 0
    }

    # 添加拦截器处理后的headers
    headers = on_request(data)

    # 发送POST请求
    response = requests.post(url, json=data, headers=headers)

    # 打印日志
    CommonUtil.log(f"chatBanCall()...uid={uid}, enable={enable}, data={response.json()}")

    return response.json()


# 测试代码
if __name__ == "__main__":
    # 调用接口测试
    uid = "12345"
    enable = True
    response = chat_ban_call(uid, enable)
    print("接口响应:", response)
