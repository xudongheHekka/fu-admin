import json
import random
import time
import hashlib
import base64
import requests
import threading
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class BottleAPI:
    AES_CBC_ALGORITHM = 'AES/CBC/PKCS5PADDING'
    # 正式环境
    # TOKEN_KEY = b'1ea5784f54e4fade7a83ddae369b35f9'
    # TOKEN_IV = b'91kdSke72h6naM2F'
    # 测试环境
    TOKEN_KEY = b'358d71c554ae78914fece40609aad77b'
    TOKEN_IV = b'F3a22EcceB2e0t13'
    CONTENT_KEY = b'75fa6cf7300033b477f5644110b8fcd7'
    CONTENT_IV = b'907AcdEf2fCb17fb'

    @staticmethod
    def encrypt(text: str, key: bytes, iv: bytes) -> str:
        """AES CBC 模式加密"""
        try:
            text = text.encode('utf-8')
            cipher = AES.new(key, AES.MODE_CBC, iv)
            encrypted = cipher.encrypt(pad(text, AES.block_size))
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            print(f"Encryption error: {e}")
            return None

    @staticmethod
    def decrypt(encrypted_text: str, key: bytes, iv: bytes) -> str:
        """AES CBC 模式解密"""
        try:
            encrypted = base64.b64decode(encrypted_text)
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted = unpad(cipher.decrypt(encrypted), AES.block_size)
            return decrypted.decode('utf-8')
        except Exception as e:
            print(f"Decryption error: {e}")
            return None

    def send_message(self):
        try:
            # 加密token
            token = '{"uid":"11006419"}'
            encrypted_token = self.encrypt(token, self.TOKEN_KEY, self.TOKEN_IV)
            # 盐
            salt = "a920b7226ea0dac52158deca9baa0a5f"
            timestamp = int(time.time() * 1000)
            request_body = {
                              "list": [
                                {
                                  "event_code": 10403,
                                  "event_time": "2025-07-21 14:28:00",
                                  "page": 1005,
                                  "uid": "11006419"
                                },
                                {
                                  "event_code": 10302,
                                  "event_time": "2025-07-21 14:28:00",
                                  "page": 1005,
                                  "uid": "11006419"
                                }
                              ],
                              "adid": "",
                              "aid": "c56cf7986c9571db",
                              "app_id": 1,
                              "app_type": 1,
                              "de_type": 0,
                              "dr_type": 0,
                              "is_nim": 1,
                              "market": "vivo",
                              "oaid": "cefac50fab7f22cb80c25daed0d8317d214acd475e30d0b19e756b03db8b28ee",
                              "os": "android",
                              "os_ver": "11",
                              "p_mftr": "vivo",
                              "p_model": "V2069BA",
                              "screen_height": 2342,
                              "screen_width": 1080,
                              "timet": 1753072080556,
                              "timew": 1753072080556,
                              "token": encrypted_token,
                              "ts": timestamp,
                              "umid": "d947bc496cd8fc230da473bb8e2e2563od",
                              "ver": "9.14.1"
                            }
                                        # 生成签名
            body_str = json.dumps(request_body)
            sign = hashlib.md5((body_str + salt).encode('utf-8')).hexdigest()

            # 准备请求头
            headers = {
                'Content-Type': 'application/json',
                'Sign': sign
            }

            # 发送请求
            url = "https://stage-api-meeting.weizhiyanchina.com/api/track/event"
            response = requests.post(url, json=request_body, headers=headers, timeout=10)

            if response.status_code == 200:
                # 解密响应数据
                decrypted_response = self.decrypt(response.text, self.CONTENT_KEY, self.CONTENT_IV)
                print(f"请求成功: {decrypted_response}")
                return decrypted_response
            else:
                print(f"请求失败，状态码: {response.status_code}")
                return None

        except Exception as e:
            print(f"请求出错: {e}")
            return None

def test_api_calls(api_instance, num_calls):
    success_count = 0

    for _ in range(num_calls):
        if api_instance.send_message():
            success_count += 1

    success_rate = (success_count / num_calls) * 100
    print(f"成功率: {success_rate:.2f}%")




if __name__ == "__main__":
    api = BottleAPI()
    # 只发送一次请求
    #  api.send_message()
    test_api_calls(api, 10)
