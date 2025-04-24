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
            'host': 'z9m47xvaakc3v9ayzldn-rw4rm.rwlb.rds.aliyuncs.com',
            'user': 'room',
            'password': '693HNamTj1k',
            'database': 'room'
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
            f" -你是一位创意十足的社交文案专家，专门为使用社交应用的年轻女性创作拟人化的打招呼文案，文案会被发给男性，请生成{num_nicknames}条文案，要求如下："
            "- 使用漂流瓶社交app，目标是吸引男性回复"
            "- 文案长度应在30字左右，避免使用字母。"
            "- 不涉及约见面、性暗示、政治话题，且不引用歌曲或影视作品。"
            "- 请尽可能贴近以下示例风格："
            "  1. 捡到请回复，证明地球是圆的"
            "  2. 漂流瓶里装着我的最后一丝清醒"
            "  3. 恭喜你获得今日份的随机聊天"
            "  4. 瓶子里是刚泡好的电子茶，趁热喝"
            "  5. 捞到这条说明你手气不错"
            "  6. 里面装着我对周末的渴望"
            "  7. 这是来自单身贵族的问候"
            "  8. 捞瓶子的你，一定很有趣吧"
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
        print(cleaned_response)
        cleaned_response = cleaned_response.replace('好的!以下是 50 个符合您要求的中文昵称:', '').strip()
        return [line.strip() for line in cleaned_response.splitlines() if line.strip()]

    def save_to_database(self, nicknames: List[str], model: str = "llama2") -> None:
        """保存昵称到数据库"""
        current_time = datetime.now()
        insert_query = """
        INSERT INTO bottle_template_text_man (body, created_at, gender, deleted)    
        VALUES (%s, %s, %s, %s)
        """
        successful_count = 0
        failed_count = 0

        for nickname in nicknames:
            nickname = re.sub(r'^\d+\.\s*|["“”]', '', nickname)
            if self.is_nickname_valid(nickname):
                gender_value = 2  # 假设性别值为1
                values = (nickname, current_time, gender_value, 0)
                try:
                    with self.db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(insert_query, values)
                        conn.commit()
                    successful_count += 1
                except mysql.connector.Error as err:
                    print(f"插入昵称 '{nickname}' 时发生错误: {err}")
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

def main():
    """主函数：演示使用示例"""
    generator = DeepSeek()
    nicknames = generator.generate_nicknames(5)
    for nickname in nicknames:
        print(nickname)


if __name__ == "__main__":
    while True:
        main()
