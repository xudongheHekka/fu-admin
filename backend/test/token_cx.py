import json
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64


# Token类
class Token:
    def __init__(self, uid, login_type, login_time=None):
        self.uid = uid
        self.login_type = login_type
        self.login_time = login_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        return {
            "Uid": self.uid,
            "LoginType": self.login_type,
            "LoginTime": self.login_time
        }


# AES工具类
class AESUtil:
    @staticmethod
    def encrypt(src: str, key: str, iv: str) -> str:
        """
        AES加密方法
        :param src: 需要加密的字符串
        :param key: 密钥（16字节）
        :param iv: 初始化向量（16字节）
        :return: 加密后的Base64字符串
        """
        if not all([src, key, iv]):
            return None

        try:
            # 转换为字节
            key_bytes = key.encode('utf-8')
            iv_bytes = iv.encode('utf-8')

            # 创建AES加密器，使用CBC模式
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)

            # 对数据进行填充并加密
            padded_data = pad(src.encode('utf-8'), AES.block_size)
            encrypted_bytes = cipher.encrypt(padded_data)

            # 将加密结果进行Base64编码
            return base64.b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            print(f"Encryption error: {e}")
            return None

    @staticmethod
    def decrypt(encrypted: str, key: str, iv: str) -> str:
        """
        AES解密方法
        :param encrypted: 加密后的Base64字符串
        :param key: 密钥（16字节）
        :param iv: 初始化向量（16字节）
        :return: 解密后的字符串
        """
        if not all([encrypted, key, iv]):
            return None

        try:
            # 转换为字节
            key_bytes = key.encode('utf-8')
            iv_bytes = iv.encode('utf-8')

            # 创建AES解密器，使用CBC模式
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)

            # Base64解码并解密
            encrypted_bytes = base64.b64decode(encrypted)
            decrypted_padded = cipher.decrypt(encrypted_bytes)

            # 去除填充并返回解密后的字符串
            return unpad(decrypted_padded, AES.block_size).decode('utf-8')
        except Exception as e:
            print(f"Decryption error: {e}")
            return None


# 测试代码
def test_generate_token():
    # 创建Token对象
    token = Token(uid=11809, login_type=1)

    # 将Token对象序列化为JSON字符串
    token_str = json.dumps(token.to_dict())
    print("Token JSON字符串:", token_str)

    # 加密
    encrypted = AESUtil.encrypt(token_str, "1ea5784f54e4fade7a83ddae369b35f9", "91kdSke72h6naM2F")
    print("加密后的数据:", encrypted)

    # 解密
    decrypted = AESUtil.decrypt(
        "YvcLja6yWBYrKPX54lKpFejwhMTMlz5BCR5JxmqIe5vx2/ltbb09h7qQobrrDzi7LftNxzWFFUZ5RrNIKXMratS84CldpMNnBppGg66+Ujo=",
        "1ea5784f54e4fade7a83ddae369b35f9",
        "91kdSke72h6naM2F"
    )
    print("解密后的数据:", decrypted)


if __name__ == "__main__":
    # test_generate_token()

    decrypted = AESUtil.decrypt(
        "VYPbs4tYrSv8Vgalq8NcNBBwwqPtugJf7xF4Rsr5Hrk2zRYd1xg9uUuMEO5/w71g/hy5W6gAdhs0wL37Vbge/qGDKpxTywoSAHpNaas3lSM9MvyUwmr4tTQPjBHQTYQA",
        "75fa6cf7300033b477f5644110b8fcd7",
        "907AcdEf2fCb17fb"
    )
    print("解密后的数据:", decrypted)



