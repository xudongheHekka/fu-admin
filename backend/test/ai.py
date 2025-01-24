import requests
import re
import mysql.connector
import json
import random
from datetime import datetime
from typing import List, Dict


class NicknameGenerator:
    def __init__(self):
        # 数据库配置
        self.db_config = {
            'host': 'rm-2ze2gje6no17082up.mysql.rds.aliyuncs.com',
            'user': 'user',
            'password': 'gMpg4gnVJ+c',
            'database': 'user'
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
            CREATE TABLE IF NOT EXISTS nicknames_ai (
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
            CREATE TABLE IF NOT EXISTS forbidden_words_ai (
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

    def init_forbidden_words(self, cursor):
        """初始化基础禁用词"""
        try:
            # 检查是否已经有数据
            cursor.execute("SELECT COUNT(*) FROM forbidden_words_ai")
            count = cursor.fetchone()[0]

            if count == 0:
                # 基础禁用词列表
                basic_forbidden_words = [
                    ('小姐', '敏感词', '涉及不当内容'),
                    ('天安门', '政治敏感', '政治敏感词'),
                    ('色情', '敏感词', '涉及不当内容'),
                    ('赌博', '敏感词', '涉及不当内容'),
                    ('毒品', '敏感词', '涉及不当内容')
                ]

                insert_query = """
                INSERT INTO forbidden_words_ai 
                (word, category, description, create_time, update_time, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                """

                current_time = datetime.now()

                for word, category, description in basic_forbidden_words:
                    values = (
                        word,
                        category,
                        description,
                        current_time,
                        current_time,
                        1
                    )
                    cursor.execute(insert_query, values)

        except mysql.connector.Error as err:
            print(f"初始化禁用词错误: {err}")

    def load_forbidden_words(self) -> List[Dict]:
        """从数据库加载禁用词列表"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor(dictionary=True)

            query = """
            SELECT word, category, description 
            FROM forbidden_words_ai 
            WHERE status = 1
            """

            cursor.execute(query)
            return cursor.fetchall()

        except mysql.connector.Error as err:
            print(f"加载禁用词错误: {err}")
            return []
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

    def validate_nickname(self, nickname: str) -> bool:
        """验证昵称是否合法"""
        if not nickname:
            return False

        # 检查长度
        if len(nickname) > 12:
            return False

        # 检查是否包含英文
        if re.search(r'[a-zA-Z]', nickname):
            return False

        # 检查禁用词
        for word in self.forbidden_words:
            if word['word'] in nickname:
                return False

        return True

    def generate_fallback_nicknames(self, num_nicknames=10) -> List[str]:
        """备选的昵称生成方法"""
        adjectives = ['快乐', '阳光', '可爱', '温柔', '智慧', '勇敢', '善良', '开心', '活力', '文艺',
                      '清新', '淡雅', '俏皮', '调皮', '萌萌', '甜甜', '暖暖', '安静', '优雅', '灵动']
        nouns = ['小猫', '花儿', '星星', '月亮', '彩虹', '蝴蝶', '小鸟', '微风', '海浪', '云朵',
                 '糖果', '奶茶', '小熊', '兔子', '年华', '精灵', '童话', '蒲公英', '向日葵', '樱花']
        emojis = ['🌟', '🌈', '🌺', '🎵', '💫', '🌸', '✨', '💕', '🍀', '🌙',
                  '🎨', '🌹', '🎭', '🎪', '🎠', '🎡', '🎢', '🎣', '🎮', '🎯']

        nicknames = []
        while len(nicknames) < num_nicknames:
            adj = random.choice(adjectives)
            noun = random.choice(nouns)
            emoji = random.choice(emojis)

            # 随机组合方式
            patterns = [
                f"{adj}{noun}",
                f"{adj}{noun}{emoji}",
                f"{emoji}{adj}{noun}",
                f"{noun}{emoji}",
                f"{adj}{emoji}"
            ]

            nickname = random.choice(patterns)
            if self.validate_nickname(nickname):
                nicknames.append(nickname)

        return nicknames

    def generate_nicknames(self, num_nicknames=10):
        """生成昵称"""
        try:
            # 获取最新的违禁词列表
            self.forbidden_words = self.load_forbidden_words()

            # 将违禁词转换为字符串列表
            forbidden_words_list = [word['word'] for word in self.forbidden_words]
            forbidden_words_str = '、'.join(forbidden_words_list)

            url = "http://10.8.0.46:11434/api/generate"
            prompt = f"""请生成{num_nicknames}个社交APP用户昵称，每个昵称独占一行，要求：
            1. 每个昵称长度不超过12个字符
            2. 可以包含表情符号
            3. 必须是中文，不能包含英文
            4. 可以使用王者荣耀、吃鸡等热门游戏昵称
            5. 不能生成空内容
            6. 严禁使用以下词语（包括同音字或谐音）：{forbidden_words_str}

            请直接生成昵称列表，每行一个昵称，不要使用JSON格式。"""

            payload = {
                "model": "qwen2",
                "prompt": prompt,
                "stream": False
            }

            headers = {
                'Content-Type': 'application/json'
            }

            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()

            result = response.json()
            if result.get('response'):
                # 清理响应文本
                response_text = result['response']
                # 移除可能的JSON格式符号
                response_text = response_text.replace('{', '').replace('}', '')
                response_text = response_text.replace('"', '')
                response_text = response_text.replace(':', '\n')
                response_text = response_text.replace(',', '\n')

                # 分割成行并清理
                nicknames = [line.strip() for line in response_text.split('\n')]
                # 过滤掉空行和无效行
                valid_nicknames = [n for n in nicknames if n and self.validate_nickname(n)]

                if valid_nicknames:
                    self.save_to_database(valid_nicknames, prompt)
                    return valid_nicknames

            # 如果没有有效昵称，使用备选方法
            print("API返回结果无效，使用备选方法生成昵称...")
            nicknames = self.generate_fallback_nicknames(num_nicknames)
            if nicknames:
                self.save_to_database(nicknames, "使用备选方法生成")
            return nicknames

        except Exception as e:
            print(f"生成昵称时发生错误: {e}")
            print(f"错误类型: {type(e)}")
            print(f"错误详情: {str(e)}")
            # 使用备选方法
            nicknames = self.generate_fallback_nicknames(num_nicknames)
            if nicknames:
                self.save_to_database(nicknames, "使用备选方法生成")
            return nicknames


    def save_to_database(self, nicknames: List[str], prompt: str, model: str = "llama2"):
        """保存昵称到数据库"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()

            insert_query = """
            INSERT INTO nicknames_ai (nickname, create_time, model, prompt, status)
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
            SELECT * FROM nicknames_ai 
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
            UPDATE nicknames_ai 
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

    def get_forbidden_words(self) -> List[Dict]:
        """获取禁用词列表"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor(dictionary=True)

            query = """
            SELECT * FROM forbidden_words_ai 
            WHERE status = 1 
            ORDER BY create_time DESC
            """

            cursor.execute(query)
            return cursor.fetchall()

        except mysql.connector.Error as err:
            print(f"获取禁用词列表错误: {err}")
            return []
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
