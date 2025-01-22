import json
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64


# 用户登录类型枚举
class UserLoginTypeEnum(Enum):
    PHONE = 1
    QQ = 2
    WX = 3

    def get_code(self):
        return self.value


# Token数据类
@dataclass
class Token:
    uid: int
    login_type: int
    login_time: datetime

    def to_dict(self):
        return {
            'uid': self.uid,
            'loginType': self.login_type,
            'loginTime': self.login_time.isoformat()
        }


# AES工具类
class AESUtil:
    @staticmethod
    def encrypt(text: str, key: str, iv: str) -> str:
        # 确保key和iv是16字节
        key_bytes = key.encode('utf-8').ljust(16, b'\0')[:16]
        iv_bytes = iv.encode('utf-8').ljust(16, b'\0')[:16]

        cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
        padded_data = pad(text.encode(), AES.block_size)
        encrypted = cipher.encrypt(padded_data)
        return base64.b64encode(encrypted).decode()

    @staticmethod
    def decrypt(encrypted: str, key: str, iv: str) -> str:
        # 确保key和iv是16字节
        key_bytes = key.encode('utf-8').ljust(16, b'\0')[:16]
        iv_bytes = iv.encode('utf-8').ljust(16, b'\0')[:16]

        cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
        encrypted_data = base64.b64decode(encrypted)
        decrypted_padded = cipher.decrypt(encrypted_data)
        decrypted = unpad(decrypted_padded, AES.block_size)
        return decrypted.decode()


# Token编解码类
class TokenCodec:
    @staticmethod
    def encrypt(src: str, yace: bool = False) -> str:
        return AESUtil.encrypt(src, "1ea5784f54e4fade7a83ddae369b35f9", "91kdSke72h6naM2F")

    @staticmethod
    def decrypt(encrypted: str, yace: bool = False) -> str:
        return AESUtil.decrypt(encrypted, "1ea5784f54e4fade7a83ddae369b35f9", "91kdSke72h6naM2F")


# Token生成器类
class TokenGenerator:
    def __init__(self):
        self.object_mapper = json

    def generate_token(self, uid: int, login_type: UserLoginTypeEnum, yace: bool = False) -> str:
        token = Token(
            uid=uid,
            login_type=login_type.get_code(),
            login_time=datetime.now()
        )
        token_str = self.object_mapper.dumps(token.to_dict())
        return TokenCodec.encrypt(token_str, yace)


# 使用示例
def main():
    try:
        # 创建token生成器
        generator = TokenGenerator()

        # 生成token
        token = generator.generate_token(
            uid=12345,
            login_type=UserLoginTypeEnum.PHONE,
            yace=False
        )
        print(f"Generated token: {token}")

        # 解密token
        decrypted = TokenCodec.decrypt(token, False)
        print(f"Decrypted token: {decrypted}")

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
