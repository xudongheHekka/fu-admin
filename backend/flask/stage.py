from flask import Flask, request, render_template, jsonify
import json
import time
import hashlib
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import requests

app = Flask(__name__)

class BottleAPI:
    AES_CBC_ALGORITHM = 'AES/CBC/PKCS5PADDING'

    def __init__(self, environment):
        # 根据传递的环境参数加载不同的配置
        if environment == 'Production':  # 生产环境
            self.TOKEN_KEY = b'1ea5784f54e4fade7a83ddae369b35f9'
            self.TOKEN_IV = b'91kdSke72h6naM2F'
        elif environment == 'Staging':  # 测试环境
            self.TOKEN_KEY = b'358d71c554ae78914fece40609aad77b'
            self.TOKEN_IV = b'F3a22EcceB2e0t13'
        else:
            raise ValueError("Invalid environment. Only 'Staging' and 'Production' are supported.")

        self.CONTENT_KEY = b'75fa6cf7300033b477f5644110b8fcd7'
        self.CONTENT_IV = b'907AcdEf2fCb17fb'

    @staticmethod
    def encrypt(text: str, key: bytes, iv: bytes) -> str:
        try:
            text = text.encode('utf-8')
            cipher = AES.new(key, AES.MODE_CBC, iv)
            encrypted = cipher.encrypt(pad(text, AES.block_size))
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Encryption failed: {e}")

    @staticmethod
    def decrypt(encrypted_text: str, key: bytes, iv: bytes) -> str:
        try:
            encrypted = base64.b64decode(encrypted_text)
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted = unpad(cipher.decrypt(encrypted), AES.block_size)
            return decrypted.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")

    def send_message(self, api_url, request_body, uid):
        try:
            # 加密 token，动态使用前端传递的 uid
            token = json.dumps({"uid": uid})
            encrypted_token = self.encrypt(token, self.TOKEN_KEY, self.TOKEN_IV)
            salt = "a920b7226ea0dac52158deca9baa0a5f"
            timestamp = int(time.time() * 1000)

            # 填充额外字段
            request_body['token'] = encrypted_token
            request_body['ts'] = timestamp

            # 生成签名
            body_str = json.dumps(request_body)
            sign = hashlib.md5((body_str + salt).encode('utf-8')).hexdigest()

            # 准备请求头
            headers = {
                'Content-Type': 'application/json',
                'Sign': sign
            }

            # 发送请求到用户指定的接口地址
            response = requests.post(api_url, json=request_body, headers=headers, timeout=10)

            if response.status_code == 200:
                if response.text:  # 检查响应是否为空
                    try:
                        decrypted_response = self.decrypt(response.text, self.CONTENT_KEY, self.CONTENT_IV)
                        return {"status": "success", "data": decrypted_response}
                    except ValueError as e:
                        return {"status": "error", "message": f"Decryption failed: {str(e)}"}
                else:
                    return {"status": "fail", "message": "Empty response from server"}
            else:
                return {"status": "fail", "message": f"HTTP {response.status_code}"}
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": f"Request error: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

# Flask 路由
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send', methods=['POST'])
def send():
    try:
        # 获取用户输入的 request_body、API URL、UID 和环境参数
        data = request.json
        if not data or 'api_url' not in data or 'request_body' not in data or 'uid' not in data or 'environment' not in data:
            return jsonify({"status": "fail", "message": "API URL, request body, UID, and environment are required"}), 400

        api_url = data['api_url']
        request_body = data['request_body']
        uid = data['uid']  # 从前端获取 UID
        environment = data['environment']  # 从前端获取环境参数

        # 使用传递的环境参数初始化 BottleAPI
        api = BottleAPI(environment=environment)
        result = api.send_message(api_url, request_body, uid)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)