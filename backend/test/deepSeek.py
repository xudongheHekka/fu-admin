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
        try:
            url = "http://192.168.0.128:11434/api/generate"
            prompt = f"""请生成 {num_nicknames} 个中文昵称，要求如下：
            ### 1. 基本规则
            - 字数限制：3-12 个字
            - 风格要求：简洁优雅，富有创意，昵称不要重复
            - 禁止内容：
              - 不使用英文字母和数字
              - 避免使用敏感词或不雅词汇
              - 不使用任何标点符号（`**`、`()`、`{'、'}` 等数学符号）
              - 不使用任何标点符号
            """

            models = ["deepseek-r1:32b"]
            selected_model = random.choice(models)
            payload = {
                "model": selected_model,
                "prompt": prompt,
                "stream": False
            }

            headers = {
                'Content-Type': 'application/json'
            }

            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()

            result = response.json()
            if 'response' in result:
                # 提取字符串内容
                text_response = result['response']

                # 移除 <think> 标签之间的内容
                cleaned_response = re.sub(r'<think>.*?</think>', '', text_response, flags=re.DOTALL)

                # 去除开头的多余文本
                cleaned_response = cleaned_response.replace('好的!以下是 50 个符合您要求的中文昵称:', '').strip()

                # 使用正则表达式匹配编号和昵称
                pattern = r'\d+\.\s+([\u4e00-\u9fa5]+)'
                nicknames = re.findall(pattern, cleaned_response)

                if nicknames:
                    self.save_to_database(nicknames, "使用API生成")

                return nicknames

            # 如果没有有效昵称，使用备选方法
            print("API返回结果无效，使用备选方法生成昵称...")
            return self.generate_fallback_nicknames(num_nicknames)

        except Exception as e:
            print(f"生成昵称时发生错误: {e}")
            print(f"错误类型: {type(e)}")
            print(f"错误详情: {str(e)}")
            # 使用备选方法
            return self.generate_fallback_nicknames(num_nicknames)

    def save_to_database(self, nicknames: List[str], model: str = "llama2") -> None:
        """保存昵称到数据库"""
        try:
            current_time = datetime.now()
            successful_count = 0
            failed_count = 0

            insert_query = """
            INSERT INTO config_nickname (nickname, create_time, model, status, gender)
            VALUES (%s, %s, %s, %s, %s)
            """

            for nickname in nicknames:
                try:
                    if self.get_nickname(nickname):
                        print(f"昵称 '{nickname}' 已存在，跳过")
                        failed_count += 1
                        continue

                    url = "http://172.17.163.138:8081/internal/text/check"
                    payload = {
                        "body": nickname,
                        "replace": False,
                        "without_ai": True,
                        "without_keyword": False,
                        "service": 2
                    }
                    response = requests.post(url, json=payload)
                    response.raise_for_status()

                    result = response.json()
                    category = result.get("data", {}).get("category", -1)

                    if category == 0:
                        values = (nickname, current_time, model, 0, 1)
                        with self.db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute(insert_query, values)
                            conn.commit()
                            successful_count += 1
                    else:
                        print(f"昵称 '{nickname}' 不合法，跳过 (category: {category})")
                        failed_count += 1

                except requests.RequestException as e:
                    print(f"检查昵称 '{nickname}' 时发生请求错误: {e}")
                    failed_count += 1
                except mysql.connector.Error as insert_err:
                    if insert_err.errno == 1062:
                        print(f"昵称 '{nickname}' 已存在，跳过")
                        failed_count += 1
                    else:
                        print(f"插入昵称 '{nickname}' 时发生数据库错误: {insert_err}")
                        failed_count += 1

            print(f"处理完成：成功插入 {successful_count} 个昵称，失败 {failed_count} 个")

        except Exception as e:
            print(f"保存昵称到数据库时发生未知错误: {e}")

    def get_nickname(self, name: str) -> bool:
        """通过 name 查询 user 表，判断是否存在匹配的记录"""
        try:
            with self.db_connection() as conn:
                cursor = conn.cursor()
                query = """
                SELECT COUNT(*) 
                FROM user 
                WHERE name = %s
                """
                cursor.execute(query, (name,))
                count = cursor.fetchone()[0]
                return count > 0

        except mysql.connector.Error as err:
            print(f"查询 user 表时发生错误: {err}")
            return False

    def generate_fallback_nicknames(self, num_nicknames=2):
        """生成备选昵称的方法"""
        # 实现备选昵称生成逻辑
        return ["备选昵称1", "备选昵称2"][:num_nicknames]

def main():
    """主函数：演示使用示例"""
    generator = DeepSeek()

    print("生成新昵称...")
    nicknames = generator.generate_nicknames(50)
    print("生成的昵称：")
    for nickname in nicknames:
        print(nickname)


if __name__ == "__main__":
    main()
