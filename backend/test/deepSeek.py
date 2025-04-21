import re
import requests
import mysql.connector
import random
from datetime import datetime
from typing import List
from contextlib import contextmanager


class DeepSeek:
    def __init__(self):
        # 数据库配置
        self.db_config = {
            'host': 'rm-2ze2gje6no17082up.mysql.rds.aliyuncs.com',
            'user': 'user',
            'password': 'gMpg4gnVJ+c',
            'database': 'user'
        }

    @contextmanager
    def db_connection(self):
        """上下文管理器，用于管理数据库连接"""
        conn = None
        try:
            conn = mysql.connector.connect(**self.db_config)
            yield conn
        except mysql.connector.Error as err:
            print(f"数据库连接错误: {err}")
            raise
        finally:
            if conn and conn.is_connected():
                conn.close()

    def generate_nicknames(self, num_nicknames=2):
        """生成昵称"""
        nicknames = self.fetch_nicknames_from_api(num_nicknames)
        self.save_to_database(nicknames, "使用API生成")
        return nicknames

    def fetch_nicknames_from_api(self, num_nicknames):
        """从API获取昵称"""
        url = "http://192.168.0.128:11434/api/generate"
        prompt = (
            f"请生成{num_nicknames}条文案，以下是要求："
            "- 使用漂流瓶社交app，性别男，目标是吸引女性回复。"
            "- 文案需简短（20字以内），避免使用字母。"
            "- 不约见面，无性暗示，不涉及政治，不引用歌曲或影视作品。"
            "示例文案风格："
            "1. 想找个搭子，分享日常琐碎小事～"
            "2. 今日份趣事超多，缺个倾听的你。"
            "3. 好奇女生此刻，都在做什么呀？"
            "4. 分享一首歌，开启奇妙聊天之旅。"
            "5. 找个聊天搭子，治愈平淡小生活"
        )

        models = ["deepseek-r1:32b"]
        selected_model = random.choice(models)
        payload = {
            "model": selected_model,
            "prompt": prompt,
            "stream": False
        }

        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=1000)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"请求API时发生错误: {e}")
            return []

        result = response.json()
        text_response = result.get('response', '')
        cleaned_response = re.sub(r'<think>.*?</think>', '', text_response, flags=re.DOTALL)
        cleaned_response = cleaned_response.replace('好的!以下是 50 个符合您要求的中文昵称:', '').strip()

        pattern = r'\d+\.\s+([\u4e00-\u9fa5]+)'
        return re.findall(pattern, cleaned_response)

    def save_to_database(self, nicknames: List[str], model: str = "llama2") -> None:
        """保存昵称到数据库"""
        current_time = datetime.now()
        insert_query = """
        INSERT INTO bottle_template_text_test (body, created_at, gender, deleted)
        VALUES (%s, %s, %s, %s)
        """
        successful_count = 0
        failed_count = 0

        for nickname in nicknames:
            # if self.get_nickname(nickname):
            #     print(f"昵称 '{nickname}' 已存在，跳过")
            #     failed_count += 1
            #     continue

            if self.is_nickname_valid(nickname):
                gender_value = 1  # 假设性别值为1
                values = (nickname, current_time, gender_value, 0)
                with self.db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(insert_query, values)
                    conn.commit()
                successful_count += 1
            else:
                print(f"昵称 '{nickname}' 不合法，跳过")
                failed_count += 1

        print(f"处理完成：成功插入 {successful_count} 个昵称，失败 {failed_count} 个")

    def is_nickname_valid(self, nickname: str) -> bool:
        """检查昵称是否合法"""
        url = "http://172.17.163.138:8081/internal/text/check"
        payload = {
            "body": nickname,
            "replace": False,
            "without_ai": True,
            "without_keyword": False,
            "service": 2
        }
        try:
            response = requests.post(url, json=payload, timeout=5)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"校验昵称 '{nickname}' 时发生错误: {e}")
            return False

        result = response.json()
        category = result.get("data", {}).get("category", -1)
        return category == 0

    # def get_nickname(self, name: str) -> bool:
    #     """通过 name 查询 user 表，判断是否存在匹配的记录"""
    #     try:
    #         with self.db_connection() as conn:
    #             cursor = conn.cursor()
    #             query = "SELECT COUNT(*) FROM user WHERE name = %s"
    #             cursor.execute(query, (name,))
    #             count = cursor.fetchone()[0]
    #             return count > 0
    #     except mysql.connector.Error as err:
    #         print(f"查询 user 表时发生错误: {err}")
    #         return False

    # def generate_fallback_nicknames(self, num_nicknames=2):
    #     """生成备选昵称的方法"""
    #     return ["备选昵称1", "备选昵称2"][:num_nicknames]


def main():
    """主函数：演示使用示例"""
    generator = DeepSeek()
    nicknames = generator.generate_nicknames(5)
    for nickname in nicknames:
        print(nickname)


if __name__ == "__main__":
    while True:
        main()
