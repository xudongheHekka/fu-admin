import json
import time
import hashlib
import base64
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class BottleAPI:
    AES_CBC_ALGORITHM = 'AES/CBC/PKCS5PADDING'
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
        # 加密token
        token = '{"Uid":"11850"}'
        encrypted_token = self.encrypt(token, self.TOKEN_KEY, self.TOKEN_IV)

        # 准备请求数据
        salt = "a920b7226ea0dac52158deca9baa0a5f"
        timestamp = int(time.time() * 1000)

        request_body = {
            "is_pirated": 0,
            "idfa": "F7A12724-15EC-4A03-9379-13DED3C85DAC",
            "is_nim": 1,
            "req_rand": 7861,
            "stid": "jdCqgB7AYoABoiKVzEw9yg==",
            "is_simulator": 0,
            "app_id": "1",
            "timet": 1725706987,
            "os": "ios",
            "os_ver": "15.5",
            "udid": "1e5bdf3a353f3f21d8aa9320631fea970418821f",
            "appname": "bottle",
            "ver": "7.9.9",
            "token": encrypted_token,
            "ts": timestamp,
            "idfv": "0CEB3504-7A47-43F7-97E2-636508B2BF87",
            "is_jailbroken": 0,
            "app_type": "1",
            "p_model": "iPhone8,1",
            "device_jb": 0,
            "timew": 1725706987,
            "umid": "bd9e85cdb1b1d1e2eb32c276bd16879f"
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
        url = "https://stage-api-meeting.weizhiyanchina.com/post/wall/top"
        try:
            response = requests.post(url, json=request_body, headers=headers)

            if response.status_code == 200:
                # 解密响应数据
                decrypted_response = self.decrypt(response.text, self.CONTENT_KEY, self.CONTENT_IV)
                print("Decrypted response:", decrypted_response)
                return decrypted_response
            else:
                print(f"Request failed with status code: {response.status_code}")
                return None

        except Exception as e:
            print(f"Request error: {e}")
            return None


if __name__ == "__main__":
    api = BottleAPI()
    api.send_message()
