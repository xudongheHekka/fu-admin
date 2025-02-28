import json
import random
import time
import hashlib
import base64
import requests
import threading
from concurrent.futures import ThreadPoolExecutor
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class BottleAPI:
    AES_CBC_ALGORITHM = 'AES/CBC/PKCS5PADDING'
    TOKEN_KEY = b'1ea5784f54e4fade7a83ddae369b35f9'
    TOKEN_IV = b'91kdSke72h6naM2F'
    CONTENT_KEY = b'75fa6cf7300033b477f5644110b8fcd7'
    CONTENT_IV = b'907AcdEf2fCb17fb'

    def __init__(self):
        # 添加计数器和锁，用于统计请求
        self.success_count = 0
        self.fail_count = 0
        self.lock = threading.Lock()

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
            token = '{"uid":"9880947"}'
            encrypted_token = self.encrypt(token, self.TOKEN_KEY, self.TOKEN_IV)
            #盐
            salt = "a920b7226ea0dac52158deca9baa0a5f"
            timestamp = int(time.time() * 1000)

            # request_body = {
            #     "is_pirated": 0,
            #     "idfa": "F7A12724-15EC-4A03-9379-13DED3C85DAC",
            #     "is_nim": 1,
            #     "req_rand": 7861,
            #     "stid": "jdCqgB7AYoABoiKVzEw9yg==",
            #     "is_simulator": 0,
            #     "app_id": "1",
            #     "timet": 1725706987,
            #     "os": "ios",
            #     "os_ver": "15.5",
            #     "udid": "1e5bdf3a353f3f21d8aa9320631fea970418821f",
            #     "appname": "bottle",
            #     "ver": "7.9.9",
            #     "token": encrypted_token,
            #     "ts": timestamp,
            #     "idfv": "0CEB3504-7A47-43F7-97E2-636508B2BF87",
            #     "is_jailbroken": 0,
            #     "app_type": "1",
            #     "p_model": "iPhone8,1",
            #     "device_jb": 0,
            #     "timew": 1725706987,
            #     "umid": "bd9e85cdb1b1d1e2eb32c276bd16879f"
            # }
            request_body = {
                              "fid": "3898",
                              "nonce": 4243881,
                              "type": 2,
                              "aid": "89836472497cd350",
                              "app_id": 1,
                              "app_type": 1,
                              "de_type": 0,
                              "dr_type": 0,
                              "is_nim": 1,
                              "market": "xiaomi",
                              "oaid": "8d050f19b7630311",
                              "os": "android",
                              "os_ver": "15",
                              "p_mftr": "xiaomi",
                              "p_model": "23113RKC6C",
                              "screen_height": 2310,
                              "screen_width": 1080,
                              "timet": 1740738309290,
                              "timew": 1740738309290,
                              "token": encrypted_token,
                              "ts": timestamp,
                              "umid": "07281c4b93d7c2d036f762828862f951od",
                              "ver": "9.13.2",
                              "yace": False,
                              "ip": "182.118.238.81"
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
            url = "https://api-meeting.weizhiyanchina.com/family/chat"
            response = requests.post(url, json=request_body, headers=headers, timeout=10)

            with self.lock:
                if response.status_code == 200:
                    self.success_count += 1
                    # 解密响应数据
                    decrypted_response = self.decrypt(response.text, self.CONTENT_KEY, self.CONTENT_IV)
                    print(f"Thread {threading.current_thread().name} - Success",decrypted_response)
                    return decrypted_response
                else:
                    self.fail_count += 1
                    print(f"Thread {threading.current_thread().name} - Failed with status code: {response.status_code}")
                    return None

        except Exception as e:
            with self.lock:
                self.fail_count += 1
            print(f"Thread {threading.current_thread().name} - Error: {e}")
            return None

    def pressure_test(self, num_threads=1, duration=1):
        """
        进行压力测试
        :param num_threads: 并发线程数
        :param duration: 测试持续时间(秒)
        """
        print(f"开始压力测试 - 线程数: {num_threads}, 持续时间: {duration}秒")
        start_time = time.time()

        def worker():
            while time.time() - start_time < duration:
                self.send_message()
                time.sleep(0.1)  # 添加少许延迟，避免请求过于密集

        # 创建线程池
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            # 提交任务
            futures = [executor.submit(worker) for _ in range(num_threads)]

        # 等待所有任务完成
        for future in futures:
            future.result()

        # 输出测试结果
        total_requests = self.success_count + self.fail_count
        test_duration = time.time() - start_time
        qps = total_requests / test_duration

        print("\n压测结果统计:")
        print(f"总请求数: {total_requests}")
        print(f"成功请求: {self.success_count}")
        print(f"失败请求: {self.fail_count}")
        print(f"实际测试时长: {test_duration:.2f}秒")
        print(f"平均QPS: {qps:.2f}")
        print(f"成功率: {(self.success_count / total_requests * 100):.2f}%")


if __name__ == "__main__":
    api = BottleAPI()
    # 设置并发线程数和测试时间
    api.pressure_test(num_threads=1, duration=5)
