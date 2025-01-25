import time
import requests
import re
import mysql.connector
import json
import random
from datetime import datetime
from typing import List, Dict
from functools import lru_cache


class NicknameGenerator:
    def __init__(self):
        # 数据库配置
        self.db_config = {
            'host': 'rm-2ze2gje6no17082up.mysql.rds.aliyuncs.com',
            'user': 'user',
            'password': 'gMpg4gnVJ+c',
            'database': 'user'
        }

        # 缓存相关配置
        self._cache_time = {}  # 用于记录缓存时间
        self.CACHE_TTL = 1800  # 缓存过期时间（秒），默认30分钟

        # self.init_database()
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

    @lru_cache(maxsize=1)
    def load_forbidden_words(self, cache_key: float = None) -> List[Dict]:
        """从数据库加载禁用词列表（带缓存）"""
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

    def clear_forbidden_words_cache(self):
        """清除禁用词缓存"""
        self.load_forbidden_words.cache_clear()

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

        # 获取最新的禁用词列表（使用缓存）
        cache_key = int(time.time() / self.CACHE_TTL)
        forbidden_words = self.load_forbidden_words(cache_key)

        # 检查禁用词
        for word in forbidden_words:
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
            # 获取最新的违禁词列表（使用缓存）
            cache_key = int(time.time() / self.CACHE_TTL)
            self.forbidden_words = self.load_forbidden_words(cache_key)

            # 将违禁词转换为字符串列表
            forbidden_words_list = [word['word'] for word in self.forbidden_words]
            forbidden_words_str = '、'.join(forbidden_words_list)

            url = "http://10.8.0.48:11434/api/generate"
            prompt = f"""请生成{num_nicknames}个中文昵称，要求：
            1. 字数限制：3-8个字
            2. 风格要求：简洁优雅，富有创意
            3. 可选装饰：适当使用emoji表情
            4. 禁止内容：
               - 不使用英文字母和数字
               - 不使用任何标点符号
               - 不使用以下词语及谐音：{forbidden_words_str}

            请直接输出昵称，每行一个，确保：
            - 不加序号
            - 不加任何分类标签
            - 不加任何标点符号
            - 不加任何额外修饰
            """

            models = ["qwen2", "nezahatkorkmaz/deepseek-v3"]
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
            if result.get('response'):
                nicknames = result['response'].strip().split('\n')
                valid_nicknames = []
                for nickname in nicknames:
                    cleaned_nickname = nickname.strip()
                    cleaned_nickname = re.sub(r'[-.,。，、\s]', '', cleaned_nickname)
                    cleaned_nickname = re.sub(r'^\d+[.、]?\s*', '', cleaned_nickname)

                    if cleaned_nickname and self.validate_nickname(cleaned_nickname):
                        valid_nicknames.append(cleaned_nickname)

                if valid_nicknames:
                    self.save_to_database(valid_nicknames, selected_model)
                    return valid_nicknames

            print("API返回结果无效，使用备选方法生成昵称...")
            nicknames = self.generate_fallback_nicknames(num_nicknames)
            if nicknames:
                self.save_to_database(nicknames, "使用备选方法生成")
            return nicknames

        except Exception as e:
            print(f"生成昵称时发生错误: {e}")
            print(f"错误类型: {type(e)}")
            print(f"错误详情: {str(e)}")
            nicknames = self.generate_fallback_nicknames(num_nicknames)
            if nicknames:
                self.save_to_database(nicknames, "使用备选方法生成")
            return nicknames

    @lru_cache(maxsize=1)
    def _get_nicknames_cached(self, cache_key: float) -> List[Dict]:
        """带缓存的数据库查询"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor(dictionary=True)

            query = """
            SELECT * FROM nicknames_ai 
            WHERE status = 1 
            ORDER BY create_time DESC
            """

            cursor.execute(query)
            return cursor.fetchall()

        except mysql.connector.Error as err:
            print(f"获取昵称列表错误: {err}")
            return []
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

    def get_generated_nicknames(self, limit: int = 100) -> List[Dict]:
        """获取已生成的昵称列表（带缓存）"""
        # 使用时间戳作为缓存key，每30分钟更新一次
        cache_key = int(time.time() / self.CACHE_TTL)

        # 获取缓存的完整结果
        results = self._get_nicknames_cached(cache_key)

        # 返回限制数量的结果
        return results[:limit]

    def clear_nicknames_cache(self):
        """清除昵称缓存"""
        self._get_nicknames_cached.cache_clear()

    def save_to_database(self, nicknames: List[str], model: str = "llama2"):
        """保存昵称到数据库并清除缓存"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()

            insert_query = """
            INSERT INTO config_nickname (nickname, create_time, model, status, gender)
            VALUES (%s, %s, %s, %s, %s)
            """

            current_time = datetime.now()
            successful_count = 0
            failed_count = 0

            for nickname in nicknames:
                try:
                    values = (
                        nickname,
                        current_time,
                        model,
                        0,
                        1
                    )
                    cursor.execute(insert_query, values)
                    conn.commit()
                    successful_count += 1
                except mysql.connector.Error as insert_err:
                    if insert_err.errno == 1062:
                        failed_count += 1
                        print(f"昵称 '{nickname}' 已存在，跳过")
                        continue
                    else:
                        print(f"插入昵称 '{nickname}' 时发生错误: {insert_err}")
                        failed_count += 1
                        continue

            print(f"处理完成：成功插入 {successful_count} 个昵称，失败 {failed_count} 个")

            # 清除缓存
            self.clear_nicknames_cache()

        except mysql.connector.Error as err:
            print(f"数据库连接错误: {err}")
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

    def delete_nickname(self, nickname_id: int):
        """删除（软删除）指定昵称并清除缓存"""
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

            # 清除缓存
            self.clear_nicknames_cache()

            print(f"成功删除昵称 ID: {nickname_id}")

        except mysql.connector.Error as err:
            print(f"删除昵称错误: {err}")
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

    @lru_cache(maxsize=1)
    def get_forbidden_words(self, cache_key: float = None) -> List[Dict]:
        """获取禁用词列表（带缓存）"""
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
    nicknames = generator.generate_nicknames(50)
    print("生成的昵称：")
    for nickname in nicknames:
        print(nickname)

    # 获取历史生成的昵称（使用缓存）
    print("\n获取历史昵称...")
    historical_nicknames = generator.get_generated_nicknames(10)
    print("最近生成的10个昵称：")
    for record in historical_nicknames:
        print(f"ID: {record['id']}, 昵称: {record['nickname']}, 生成时间: {record['create_time']}")

    # 获取禁用词列表（使用缓存）
    print("\n获取禁用词列表...")
    cache_key = int(time.time() / generator.CACHE_TTL)
    forbidden_words = generator.get_forbidden_words(cache_key)
    print("当前禁用词：")
    for word in forbidden_words:
        print(f"词: {word['word']}, 分类: {word['category']}")


if __name__ == "__main__":
    while True:
        try:
            print("\n" + "=" * 50)
            print(f"开始执行 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 50)

            main()

            # 添加间隔时间
            print("\n等待1秒后重新开始...")
            time.sleep(1)

        except KeyboardInterrupt:
            print("\n检测到 Ctrl+C，程序退出...")
            break
        except Exception as e:
            print(f"\n发生错误: {type(e).__name__}")
            print(f"错误详情: {str(e)}")
            print("等待3秒后重试...")
            time.sleep(3)
            continue
