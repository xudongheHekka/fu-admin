import time
import requests
import re
import mysql.connector
import random
from datetime import datetime
from typing import List, Dict
from contextlib import contextmanager


class NicknameGenerator:
    def __init__(self):
        # 数据库配置
        self.db_config = {
            'host': 'rm-2ze2gje6no17082up.mysql.rds.aliyuncs.com',
            'user': 'user',
            'password': 'gMpg4gnVJ+c',
            'database': 'user'
        }

        # 加载禁用词
        self.forbidden_words = self.load_forbidden_words()

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
            prompt = f"""请生成 {num_nicknames} 个中文昵称，要求如下：

            ---

            ### 1. 基本规则
            - 字数限制：3-12 个字
            - 风格要求：简洁优雅，富有创意，昵称不要重复
            - 禁止内容：
              - 不使用英文字母和数字
              - 避免使用敏感词或不雅词汇
              - 不使用任何标点符号（`**`、`()`、`{'、'}` 等数学符号）
              - 不使用任何标点符号
              - 不使用以下词语及谐音：{forbidden_words_str}

            ---

            ### 2. 装饰规则
            - 可以使用 **emoji 表情** 或 **颜文字** 作为装饰，但必须与文字结合
            - **禁止纯表情符号或纯颜文字的昵称**（如 🌊🌴🌊、(๑•̀ㅂ•́)و✧）
            - 每个昵称中装饰符号（emoji 或颜文字）的数量不得超过 2 个

            ---

            ### 3. 风格示例

            #### 3.1 游戏风格（如王者荣耀、和平精英）
            - ⚔️剑舞红尘
            - 绝地枪王
            - 🎯神射手
            - 荣耀王者
            - 🎲谋略大师
            - 开黑达人
            - ⚡疾风剑豪
            - 荣耀归来
            - 🏹弓箭少女

            #### 3.2 社交软件风格
            - 无敌战神
            - 🔥烈焰狂徒
            - 疾风剑豪
            - 🌟星辰之光
            - 冷月无双
            - 🛡️守护之刃
            - 影舞者

            #### 3.3 文艺清新风格
            - 🍵茶香书韵
            - 半窗疏影
            - 🎋竹语浅歌
            - 诗与橘子
            - 🌊墨香书生
            - 清风徐来
            - 🎭戏子书生
            - 云天墨客
            - 📚书香门第
            - 诗意江南

            #### 3.4 日常生活风格
            - 🥤可乐冰
            - 暖阳小屋
            - 🌞早安打工
            - 摸鱼达人
            - ☕咖啡时光
            - 宅家追剧
            - 🍜美食猎人
            - 睡到自然
            - 🎵音乐达人
            - 运动健将

            #### 3.5 个性标签风格
            - 💫追梦人
            - 独行侠
            - 🌊深海漫游
            - 江湖故人
            #### 3.6 颜文字风格
            - (๑•̀ㅂ•́)و✧战神
            - ٩(ˊᗜˋ*)و萌系少女
            - (ง •̀_•́)ง奋斗者
            - (＾▽＾)社交达人
            - (●'◡'●)甜心教主
            
            ---

            ### 4. 输出格式
            - 每个昵称占一行
            - 不要添加序号或其他前缀
            - 确保昵称符合上述所有规则

            ---

            ### 示例输出
            ⚔️剑舞红尘
            绝地枪王
            🎯神射手
            荣耀王者
            🎲谋略大师
            开黑达人
            ⚡疾风剑豪
            荣耀归来
            🏹弓箭少女
            """

            models = ["nezahatkorkmaz/deepseek-v3"]
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


def main():
    """主函数：演示使用示例"""
    generator = NicknameGenerator()

    # 生成新昵称
    print("生成新昵称...")
    nicknames = generator.generate_nicknames(50)
    print("生成的昵称：")
    for nickname in nicknames:
        print(nickname)

    # 获取禁用词列表
    # print("\n获取禁用词列表...")
    # forbidden_words = generator.load_forbidden_words()  # 修改这里
    # print("当前禁用词：")
    # for word in forbidden_words:
    #     print(f"词: {word['word']}, 分类: {word['category']}")


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
