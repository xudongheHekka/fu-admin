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

    def send_message(self, np=None):
        try:
            start_time = time.time()  # 记录开始时间
            # 加密token
            token = '{"uid":"10876444"}'
            encrypted_token = self.encrypt(token, self.TOKEN_KEY, self.TOKEN_IV)
            # 盐
            salt = "a920b7226ea0dac52158deca9baa0a5f"
            timestamp = int(time.time() * 1000)

            request_body = {
                "is_pirated": 0,
                "idfa": "CA4A7CA6-A71D-43D2-8D7A-52DC12934722",
                "ts": timestamp,
                "is_nim": 1,
                "req_rand": 5457,
                "stid": "1jpOS1YvXWXjjc0Xzqi1+w==",
                "is_simulator": 0,
                "app_id": "1",
                "timet": 1750224874,
                "os": "ios",
                "os_ver": "17.3.1",
                "udid": "c5e2def58cb6b3d3b2d28bdc9bce3936689acfcd",
                "appname": "bottle",
                "ver": "7.11.0",
                "token": encrypted_token,
                "idfv": "85DDD03F-02FA-4B7B-A8F9-D25EA785C6A0",
                "is_jailbroken": 0,
                "app_type": "1",
                "p_model": "iPhone16,1",
                "device_jb": 0,
                "timew": 1750224874,
                "umid": "401b7b2769e32f6283bf05f996a69"
            }
            # 如果传入np参数，则添加到请求体中
            if np:
                request_body["np"] = np

            # 生成签名
            body_str = json.dumps(request_body)
            sign = hashlib.md5((body_str + salt).encode('utf-8')).hexdigest()

            # 准备请求头
            headers = {
                'Content-Type': 'application/json',
                'Sign': sign
            }

            # 发送请求
            url = "http://10.221.0.201:9999/post/recommend/hot"
            response = requests.post(url, json=request_body, headers=headers, timeout=10)
            end_time = time.time()  # 记录结束时间
            duration_ms = (end_time - start_time) * 1000
            print(f"接口调用耗时: {duration_ms:.2f} ms")
            if response.status_code == 200:
                # 解密响应数据
                decrypted_response = self.decrypt(response.text, self.CONTENT_KEY, self.CONTENT_IV)
                print(f"请求成功: {decrypted_response}")
                return decrypted_response
            else:
                print(f"请求失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            end_time = time.time()  # 异常时也记录结束时间
            duration_ms = (end_time - start_time) * 1000
            print(f"接口调用耗时: {duration_ms:.2f} ms")
            print(f"请求出错: {e}")
            return None

    def fetch_all_pages(self):
        """流式分页请求，通过检查返回结果中是否存在np字段来判断是否继续获取下一页"""
        page_num = 1
        all_data = []
        np = None

        while True:
            print(f"\n正在获取第 {page_num} 页数据...")
            response = self.send_message(np)
            
            if not response:
                print("请求失败，停止获取数据")
                break

            try:
                response_data = json.loads(response)
                print(f"当前页返回数据: {response_data}")
                all_data.append(response_data)
                
                # 检查返回数据中是否存在np字段
                if isinstance(response_data, dict):
                    # 检查data字段中是否存在np
                    if "data" in response_data and isinstance(response_data["data"], dict):
                        data = response_data["data"]
                        if "np" in data:
                            next_np = data["np"]
                            print(f"获取到下一页参数: {next_np}")
                            np = next_np
                            page_num += 1
                            continue
                    
                    print("返回数据中没有np字段，分页结束")
                    break
                else:
                    print("返回数据格式不正确，分页结束")
                    break

            except json.JSONDecodeError as e:
                print(f"解析响应数据失败: {e}")
                print(f"原始响应数据: {response}")
                break

        print(f"\n总共获取了 {page_num} 页数据")
        return all_data

def test_api_calls(api_instance, num_calls):
    success_count = 0

    for _ in range(num_calls):
        if api_instance.send_message():
            success_count += 1

    success_rate = (success_count / num_calls) * 100
    print(f"成功率: {success_rate:.2f}%")

def thread_task(thread_id):
    """线程任务函数"""
    print(f"线程 {thread_id} 开始执行")
    api = BottleAPI()
    try:
        all_pages_data = api.fetch_all_pages()
        print(f"线程 {thread_id} 执行完成，获取到 {len(all_pages_data)} 页数据")
    except Exception as e:
        print(f"线程 {thread_id} 执行出错: {e}")

def run_multi_thread_test(num_threads=20):
    """运行多线程压测"""
    print(f"开始 {num_threads} 个线程的压测...")
    threads = []
    
    # 创建并启动线程
    for i in range(num_threads):
        thread = threading.Thread(target=thread_task, args=(i+1,))
        threads.append(thread)
        thread.start()
        print(f"线程 {i+1} 已启动")
    
    # 等待所有线程完成
    for i, thread in enumerate(threads):
        thread.join()
        print(f"线程 {i+1} 已结束")
    
    print("所有线程执行完成")

if __name__ == "__main__":
    # 运行20个线程的压测
    while True:
     run_multi_thread_test(1)
