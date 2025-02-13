import time

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

            url = "http://127.0.0.1:11434/api/generate"
            prompt = f"""请生成{num_nicknames}个中文昵称，要求：
            1. 字数限制：3-12个字
            2. 风格要求：简洁优雅，富有创意,生成的昵称不要重复
            3. 生成的昵称不能全部都是emoji
            4. 可选装饰：适当使用emoji表情,颜文字等
            5. 禁止内容：
               - 不使用英文字母和数字
               - 避免使用敏感词或不雅词汇
               - 不使用任何标点符号
               - 不使用以下词语及谐音：{forbidden_words_str}

            参考示例：


            🔥 热门风格（结合当下流行元素）
            🏀 篮球巨星
            🎮 电竞王者
            📱 科技达人
            🍵 茶艺大师
            🎵 音乐狂人
            📚 知识博主
            📸 摄影大师
            🌍 旅行达人
            🍜 美食探店
            💰 理财高手

            🌟 社交平台风格
            🌸 甜心教主
            🎀 萌系少女
            💫 闪耀之星
            🦋 蝶舞翩翩
            ✨ 魅力超群
            💎 高冷女神
            👑 霸气小妞
            🌈 彩虹女孩
            🍀 幸运星
            🌙 月光少女

            🎭 个性标签风格
            💫 追梦人
            🌊 深海漫游
            ⭐ 闪耀之星
            🎪 马戏团长
            🌪️ 疾风少年
            🌌 星空旅者
            🎨 艺术狂人
            🔥 烈焰战士
            🛡️ 守护骑士
            🌿 自然之子

            📖 文艺清新风格
            🍵 茶香书韵
            🎋 竹语浅歌
            🌊 墨香书生
            🎭 戏子书生
            📚 书香门第
            🌙 半窗疏影
            🌿 清风徐来
            🌸 诗意江南
            🌾 田园诗人
            ☁️ 云中漫步

            🎮 游戏风格
            ⚔️ 剑舞红尘
            🏹 弓箭少女
            🔥 烈焰狂徒
            🌟 星辰之光
            🛡️ 守护之刃
            🎯 神枪手
            ⚡ 疾风狙击手
            🌪️ 孤狼突击
            🪖 钢铁意志

            🏆 竞技体育风格
            🏅 金牌选手
            ⚽ 足球巨星
            🏸 羽毛球王
            🏊 游泳健将
            🏃 马拉松达人
            🏋️ 健身狂魔
            🚴 骑行高手
            🥋 武术大师
            🥊 拳击冠军
            🏇 马术骑士

            💼 职场精英风格
            📊 数据分析师
            💻 代码大师
            📈 投资顾问
            🎓 学术大咖
            📝 文案高手
            🎤 演讲达人
            📦 供应链专家
            📋 项目管理
            📌 设计师
            📅 时间管理



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
                # 清理响应文本，直接按换行符分割
                nicknames = result['response'].strip().split('\n')
                # 清理每个昵称并验证
                valid_nicknames = []
                for nickname in nicknames:
                    # 清理空白字符和可能的标点符号
                    # cleaned_nickname = nickname.strip().strip('.,。，、').strip()
                    # 增强清理逻辑，移除 '-' 和其他不需要的符号
                    cleaned_nickname = nickname.strip()
                    # 移除常见的标点符号和特殊字符
                    cleaned_nickname = re.sub(r'[-.,。，、\s]', '', cleaned_nickname)
                    # 移除可能的序号（如果有的话）
                    cleaned_nickname = re.sub(r'^\d+[.、]?\s*', '', cleaned_nickname)

                    if cleaned_nickname and self.validate_nickname(cleaned_nickname):
                        valid_nicknames.append(cleaned_nickname)

                if valid_nicknames:
                    self.save_to_database(valid_nicknames, selected_model)
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

    def save_to_database(self, nicknames: List[str], model: str = "llama2") -> None:
        """保存昵称到数据库"""
        try:
            # 获取当前时间
            current_time = datetime.now()
            successful_count = 0
            failed_count = 0

            # 准备插入语句
            insert_query = """
            INSERT INTO config_nickname (nickname, create_time, model, status, gender)
            VALUES (%s, %s, %s, %s, %s)
            """

            # 遍历昵称列表
            for nickname in nicknames:
                try:
                    # 检查昵称是否已存在
                    if self.get_nickname(nickname):
                        print(f"昵称 '{nickname}' 已存在，跳过")
                        failed_count += 1
                        continue

                    # 调用外部 API 检查昵称合法性
                    url = "http://172.17.163.138:8081/internal/text/check"
                    payload = {
                        "body": nickname,
                        "replace": False,
                        "without_ai": True,
                        "without_keyword": False,
                        "service": 2
                    }
                    response = requests.post(url, json=payload)
                    response.raise_for_status()  # 检查请求是否成功

                    # 处理响应
                    result = response.json()
                    category = result.get("data", {}).get("category", -1)  # 默认值为 -1，表示未找到

                    # 如果 category 为 0，表示昵称合法
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
                    if insert_err.errno == 1062:  # 重复键错误
                        print(f"昵称 '{nickname}' 已存在，跳过")
                        failed_count += 1
                    else:
                        print(f"插入昵称 '{nickname}' 时发生数据库错误: {insert_err}")
                        failed_count += 1

            print(f"处理完成：成功插入 {successful_count} 个昵称，失败 {failed_count} 个")

        except Exception as e:
            print(f"保存昵称到数据库时发生未知错误: {e}")


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

    def get_nickname(self, name: str) -> bool:
        """通过 name 查询 user 表，判断是否存在匹配的记录"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()

            # 查询语句
            query = """
            SELECT COUNT(*) 
            FROM user 
            WHERE name = %s
            """

            # 执行查询
            cursor.execute(query, (name,))
            count = cursor.fetchone()[0]

            # 如果 count > 0，说明存在匹配的记录
            return count > 0

        except mysql.connector.Error as err:
            print(f"查询 user 表时发生错误: {err}")
            return False  # 发生错误时返回 False
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
    nicknames = generator.generate_nicknames(50)
    print("生成的昵称：")
    for nickname in nicknames:
        print(nickname)

    # 获取历史生成的昵称
    # print("\n获取历史昵称...")
    # historical_nicknames = generator.get_generated_nicknames(10)
    # print("最近生成的10个昵称：")
    # for record in historical_nicknames:
    #     print(f"ID: {record['id']}, 昵称: {record['nickname']}, 生成时间: {record['create_time']}")

    # 获取禁用词列表
    print("\n获取禁用词列表...")
    forbidden_words = generator.get_forbidden_words()
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
            print("\n等待3秒后重新开始...")
            time.sleep(3)

        except KeyboardInterrupt:
            print("\n检测到 Ctrl+C，程序退出...")
            break
        except Exception as e:
            print(f"\n发生错误: {type(e).__name__}")
            print(f"错误详情: {str(e)}")
            print("等待3秒后重试...")
            time.sleep(3)
            continue

