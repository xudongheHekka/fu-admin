import requests
import re
import mysql.connector
import json
from datetime import datetime
from typing import List, Dict


class NicknameGenerator:
    def __init__(self):
        # 数据库配置
        self.db_config = {
            'host': 'localhost',
            'user': 'your_username',
            'password': 'your_password',
            'database': 'your_database'
        }

        self.init_database()
        self.forbidden_words = self.load_forbidden_words()

    def init_database(self):
        """初始化数据库表"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()

            # 创建昵称表
            create_nicknames_table = """
            CREATE TABLE IF NOT EXISTS nicknames (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nickname VARCHAR(50) NOT NULL,
                create_time DATETIME NOT NULL,
                model VARCHAR(50) NOT NULL,
                prompt TEXT,
                status TINYINT DEFAULT 1 COMMENT '1:有效 0:无效'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """

            # 创建禁用词表
            create_forbidden_words_table = """
            CREATE TABLE IF NOT EXISTS forbidden_words (
                id INT AUTO_INCREMENT PRIMARY KEY,
                word VARCHAR(50) NOT NULL,
                category VARCHAR(20) COMMENT '禁用词分类',
                description TEXT COMMENT '说明',
                create_time DATETIME NOT NULL,
                update_time DATETIME NOT NULL,
                status TINYINT DEFAULT 1 COMMENT '1:有效 0:无效'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """

            cursor.execute(create_nicknames_table)
            cursor.execute(create_forbidden_words_table)

            self.init_forbidden_words(cursor)
            conn.commit()

        except mysql.connector.Error as err:
            print(f"数据库初始化错误: {err}")
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

    def generate_nicknames(self, num_nicknames=10):
        """生成昵称"""
        url = "http://localhost:11434/api/generate"

        prompt = f"""请生成{num_nicknames}个社交APP用户昵称，每个昵称独占一行，要求：
        1. 每个昵称长度不超过12个字符
        2. 可以包含表情符号
        3. 必须是中文，不能包含英文
        4. 不能生成空内容
        请直接生成昵称，不要包含序号或其他说明文字。"""

        payload = {
            "model": "llama2",
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()

            result = response.json()
            nicknames = result['response'].strip().split('\n')

            # 过滤和验证昵称
            valid_nicknames = []
            for nickname in nicknames:
                nickname = nickname.strip()
                if self.validate_nickname(nickname):
                    valid_nicknames.append(nickname)

            # 保存到数据库
            if valid_nicknames:
                self.save_to_database(valid_nicknames, prompt)

            return valid_nicknames

        except requests.exceptions.RequestException as e:
            print(f"API请求错误: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            return []

    def save_to_database(self, nicknames: List[str], prompt: str, model: str = "llama2"):
        """保存昵称到数据库"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()

            insert_query = """
            INSERT INTO nicknames (nickname, create_time, model, prompt, status)
            VALUES (%s, %s, %s, %s, %s)
            """

            current_time = datetime.now()

            for nickname in nicknames:
                values = (
                    nickname,
                    current_time,
                    model,
                    prompt,
                    1
                )
                cursor.execute(insert_query, values)

            conn.commit()
            print(f"成功保存 {len(nicknames)} 个昵称到数据库")

        except mysql.connector.Error as err:
            print(f"数据库操作错误: {err}")
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

    def get_generated_nicknames(self, limit: int = 100) -> List[Dict]:
        """获取已生成的昵称列表"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor(dictionary=True)

            query = """
            SELECT * FROM nicknames 
            WHERE status = 1 
            ORDER BY create_time DESC 
            LIMIT %s
            """

            cursor.execute(query, (limit,))
            return cursor.fetchall()

        except mysql.connector.Error as err:
            print(f"获取昵称列表错误: {err}")
            return []
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

    def delete_nickname(self, nickname_id: int):
        """删除（软删除）指定昵称"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()

            update_query = """
            UPDATE nicknames 
            SET status = 0 
            WHERE id = %s
            """

            cursor.execute(update_query, (nickname_id,))
            conn.commit()

            print(f"成功删除昵称 ID: {nickname_id}")

        except mysql.connector.Error as err:
            print(f"删除昵称错误: {err}")
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()


def main():
    """主函数：演示使用示例"""
    generator = NicknameGenerator()

    # 生成新昵称
    print("生成新昵称...")
    nicknames = generator.generate_nicknames(5)
    print("生成的昵称：")
    for nickname in nicknames:
        print(nickname)

    # 获取历史生成的昵称
    print("\n获取历史昵称...")
    historical_nicknames = generator.get_generated_nicknames(10)
    print("最近生成的10个昵称：")
    for record in historical_nicknames:
        print(f"ID: {record['id']}, 昵称: {record['nickname']}, 生成时间: {record['create_time']}")

    # 获取禁用词列表
    print("\n获取禁用词列表...")
    forbidden_words = generator.get_forbidden_words()
    print("当前禁用词：")
    for word in forbidden_words:
        print(f"词: {word['word']}, 分类: {word['category']}")


if __name__ == "__main__":
    main()
