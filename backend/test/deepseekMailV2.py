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
        # 定义提示词列表
        prompts = [
            f"你是一位创意十足的社交文案专家，专门为使用社交应用的年轻女性创作拟人化的打招呼文案，文案会被发给男性。请生成{num_nicknames}条类似的打招呼文案，要求如下："
            "- 使用漂流瓶社交app，目标是吸引男性回复，性别设定为女。"
            "- 文案长度应在20到200字以内，避免使用字母。"
            "- 不涉及约见面、性暗示、政治话题，且不引用歌曲或影视作品。"
            "- 文案应充满想象力和趣味性，贴近年轻人的生活。"
            "- 文案可爱，有趣且充满想象力，20至 100 字之内。"
            "- 包含网络热梗。"
            "- 不要出现软件字眼信息。"
            "- 不要暴露自己的身份。"
            "- 不要出现英文字母和数字。"
            "- 只生成文案，不需要做解析。",
            "- 请尽可能贴近以下示例风格："
            "  1. 捡到请回复，证明地球是圆的 "
            "  2. 漂流瓶里装着我的最后一丝清醒 "
            "  3. 恭喜你获得今日份的随机聊天 "
            "  4. 分享一首歌，开启奇妙聊天之旅。"
            "  5. 找个聊天搭子，治愈平淡小生活。"


            f"我是一位无聊的女生，年龄20-30岁，喜欢聊活泼、年轻化的话题，不喜欢询问现实生活中的事。和陌生网友在社交app中初次聊天，文案会被发给男性。请生成{num_nicknames}条类似的打招呼文案，请生成5个问题，要求如下："
            "- 使用漂流瓶社交app，目标是吸引男性回复，性别设定为女。"
            "- 文案长度应在20到100字以内，避免使用字母。"
            "- 不涉及约见面、性暗示、政治话题，且不引用歌曲或影视作品。"
            "- 文案应充满想象力和趣味性，贴近年轻人的生活。"
            "- 不会令对方反感或尴尬。"
            "- 能拉近彼此的距离。"
            "- 不要出现任何app或者网站、平台的名字。"
            "- 不要提及歌曲电视剧明星。"
            "- 每个问题 20至 200 字以内。"
        ]

        # 随机选择一个提示词
        selected_prompt = random.choice(prompts)
        models = ["deepseek-r1:32b"]
        selected_model = random.choice(models)
        payload = {
            "model": selected_model,
            "prompt": selected_prompt,
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

            nickname = re.sub(r'^\d+\.\s*', '', nickname)
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
