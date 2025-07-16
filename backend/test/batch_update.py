import pymysql
import sys
import logging
from datetime import datetime
import signal
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('id_batch_update.log'),
        logging.StreamHandler()
    ]
)


class SimpleIDBatchUpdater:
    def __init__(self):
        self.config = {
            'host': 'selectdb-cn-0w7468h1j02.selectdbfe.rds.aliyuncs.com',
            'port': 9030,
            'user': 'admin',
            'password': 'Jybd2020$!',
            'database': 'finkcdc',
            'charset': 'utf8mb4',
            'autocommit': True,
            'connect_timeout': 60,
            'read_timeout': 60,
            'write_timeout': 60
        }
        self.should_stop = False

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        logging.info(f"接收到信号 {signum}，准备停止...")
        self.should_stop = True

    def get_connection(self):
        return pymysql.connect(**self.config)

    def get_basic_info(self):
        """获取基本信息"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 总记录数
        cursor.execute("SELECT COUNT(*) FROM report_log WHERE report_date IS NULL")
        null_count = cursor.fetchone()[0]

        # 最小ID（用作起始点）
        cursor.execute("SELECT MIN(id) FROM report_log WHERE report_date IS NULL")
        min_id = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        logging.info(f"待更新记录数: {null_count:,}")
        logging.info(f"起始ID: {min_id}")

        return null_count, min_id

    def get_id_batch(self, start_id, batch_size):
        """从指定ID开始获取一批ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 从start_id开始，按ID顺序取batch_size条记录的ID
        sql = f"""
          SELECT id 
          FROM report_log 
          WHERE report_date IS NULL 
          AND id >= {start_id}
          ORDER BY id 
          LIMIT {batch_size}
      """

        cursor.execute(sql)
        ids = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return ids

    def update_by_ids(self, ids):
        """根据ID列表更新记录"""
        if not ids:
            return 0

        conn = self.get_connection()
        cursor = conn.cursor()

        # 批量更新
        id_list = ','.join(map(str, ids))
        sql = f"""
          UPDATE report_log 
          SET report_date = date(create_time) 
          WHERE id IN ({id_list})
      """

        affected_rows = cursor.execute(sql)

        cursor.close()
        conn.close()

        return affected_rows

    def multi_thread_update(self, num_threads=10, batch_size=100000):
        """多线程更新：主线程获取ID，工作线程更新"""
        try:
            null_count, start_id = self.get_basic_info()

            if null_count == 0:
                logging.info("没有需要更新的记录")
                return

            logging.info(f"使用 {num_threads} 个工作线程，每批 {batch_size:,} 条记录")

            start_time = datetime.now()
            total_updated = 0
            batch_count = 0
            lock = threading.Lock()

            # 创建任务队列
            task_queue = queue.Queue(maxsize=num_threads * 2)  # 队列大小限制，避免内存占用过多

            def worker(thread_id):
                """工作线程函数"""
                thread_updated = 0
                thread_batches = 0

                try:
                    while not self.should_stop:
                        try:
                            # 从队列获取任务，超时5秒
                            ids = task_queue.get(timeout=5)
                            if ids is None:  # 结束信号
                                break

                            batch_start = datetime.now()

                            # 分小批次更新（避免IN子句过长）
                            sub_batch_size = 8000  # 每个子批次8000条
                            batch_updated = 0

                            for i in range(0, len(ids), sub_batch_size):
                                sub_ids = ids[i:i + sub_batch_size]
                                updated = self.update_by_ids(sub_ids)
                                batch_updated += updated

                            batch_end = datetime.now()
                            batch_time = (batch_end - batch_start).total_seconds()
                            batch_speed = batch_updated / batch_time if batch_time > 0 else 0

                            thread_updated += batch_updated
                            thread_batches += 1

                            with lock:
                                nonlocal total_updated, batch_count
                                total_updated += batch_updated
                                batch_count += 1

                                total_time = (batch_end - start_time).total_seconds()
                                avg_speed = total_updated / total_time if total_time > 0 else 0
                                progress = (total_updated / null_count) * 100
                                remaining = null_count - total_updated
                                eta_seconds = remaining / avg_speed if avg_speed > 0 else 0
                                eta_hours = eta_seconds / 3600

                                logging.info(f"线程 {thread_id}: "
                                             f"处理 {len(ids):,} 个ID, "
                                             f"更新 {batch_updated:,} 条 ({batch_speed:.0f} 条/秒), "
                                             f"线程累计 {thread_updated:,} 条, "
                                             f"总累计 {total_updated:,} 条 ({progress:.2f}%), "
                                             f"总速度: {avg_speed:.0f} 条/秒, "
                                             f"预计剩余: {eta_hours:.1f} 小时")

                            task_queue.task_done()

                        except queue.Empty:
                            continue  # 超时继续等待
                        except Exception as e:
                            logging.error(f"线程 {thread_id} 处理批次时出错: {e}")
                            task_queue.task_done()
                            continue

                except Exception as e:
                    logging.error(f"线程 {thread_id} 异常退出: {e}")

                logging.info(f"线程 {thread_id} 完成，共更新 {thread_updated:,} 条记录，处理 {thread_batches} 个批次")
                return thread_updated

            # 启动工作线程
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                # 提交工作线程
                futures = [executor.submit(worker, i + 1) for i in range(num_threads)]

                # 主线程负责获取ID并放入队列
                current_id = start_id
                main_batch_count = 0

                try:
                    while not self.should_stop and total_updated < null_count:
                        # 获取一批ID
                        ids = self.get_id_batch(current_id, batch_size)

                        if not ids:
                            logging.info("没有更多ID需要处理")
                            break

                        # 将ID批次放入队列
                        task_queue.put(ids)
                        main_batch_count += 1

                        # 更新下一批的起始ID
                        current_id = max(ids) + 1

                        logging.info(
                            f"主线程: 获取第 {main_batch_count} 批，{len(ids):,} 个ID，起始ID: {min(ids):,}，结束ID: {max(ids):,}")

                    # 发送结束信号给所有工作线程
                    for _ in range(num_threads):
                        task_queue.put(None)

                    # 等待所有任务完成
                    task_queue.join()

                except Exception as e:
                    logging.error(f"主线程获取ID时出错: {e}")
                    # 发送结束信号
                    for _ in range(num_threads):
                        task_queue.put(None)

                # 等待所有工作线程完成
                for future in as_completed(futures):
                    try:
                        result = future.result()
                    except Exception as e:
                        logging.error(f"工作线程异常: {e}")

            end_time = datetime.now()
            duration = end_time - start_time
            total_seconds = duration.total_seconds()
            avg_speed = total_updated / total_seconds if total_seconds > 0 else 0

            logging.info("=" * 80)
            logging.info(f"多线程更新完成！")
            logging.info(f"总更新记录: {total_updated:,} 条")
            logging.info(f"使用线程数: {num_threads}")
            logging.info(f"主线程获取批次: {main_batch_count}")
            logging.info(f"工作线程处理批次: {batch_count}")
            logging.info(f"总耗时: {duration}")
            logging.info(f"平均速度: {avg_speed:.0f} 条/秒")
            logging.info("=" * 80)

        except Exception as e:
            logging.error(f"多线程更新失败: {e}")
            raise

    def simple_update(self, batch_size=50000):
        """简单单线程更新"""
        try:
            null_count, start_id = self.get_basic_info()

            if null_count == 0:
                logging.info("没有需要更新的记录")
                return

            logging.info(f"单线程更新，每批 {batch_size:,} 条记录")

            start_time = datetime.now()
            total_updated = 0
            batch_count = 0
            current_id = start_id

            while not self.should_stop and total_updated < null_count:
                batch_start = datetime.now()

                # 获取一批ID
                ids = self.get_id_batch(current_id, batch_size)

                if not ids:
                    logging.info("没有更多记录需要更新")
                    break

                # 更新这批记录
                affected_rows = self.update_by_ids(ids)
                batch_end = datetime.now()

                total_updated += affected_rows
                batch_count += 1
                current_id = max(ids) + 1

                batch_time = (batch_end - batch_start).total_seconds()
                batch_speed = affected_rows / batch_time if batch_time > 0 else 0

                total_time = (batch_end - start_time).total_seconds()
                avg_speed = total_updated / total_time if total_time > 0 else 0

                progress = (total_updated / null_count) * 100
                remaining = null_count - total_updated
                eta_seconds = remaining / avg_speed if avg_speed > 0 else 0
                eta_hours = eta_seconds / 3600

                logging.info(f"批次 {batch_count}: "
                             f"ID范围 {min(ids):,}-{max(ids):,}, "
                             f"更新 {affected_rows:,} 条 ({batch_speed:.0f} 条/秒), "
                             f"累计 {total_updated:,} 条 ({progress:.2f}%), "
                             f"平均速度: {avg_speed:.0f} 条/秒, "
                             f"预计剩余: {eta_hours:.1f} 小时")

            end_time = datetime.now()
            duration = end_time - start_time
            total_seconds = duration.total_seconds()
            avg_speed = total_updated / total_seconds if total_seconds > 0 else 0

            logging.info("=" * 80)
            logging.info(f"单线程更新完成！")
            logging.info(f"总更新记录: {total_updated:,} 条")
            logging.info(f"处理批次数: {batch_count}")
            logging.info(f"总耗时: {duration}")
            logging.info(f"平均速度: {avg_speed:.0f} 条/秒")
            logging.info("=" * 80)

        except Exception as e:
            logging.error(f"单线程更新失败: {e}")
            raise


def main():
    updater = SimpleIDBatchUpdater()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == 'info':
            updater.get_basic_info()
        elif command == 'simple':
            # 单线程更新
            batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 50000
            updater.simple_update(batch_size)
        elif command == 'multi':
            # 多线程更新
            threads = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            batch_size = int(sys.argv[3]) if len(sys.argv) > 3 else 100000
            updater.multi_thread_update(threads, batch_size)
        else:
            print("基于主键ID的高速更新器:")
            print("  python script.py info                    # 查看基本信息")
            print("  python script.py simple 50000           # 单线程，每批5万条")
            print("  python script.py multi 10 100000        # 10线程，每批10万条（推荐）")
            print("  python script.py multi 15 150000        # 15线程，每批15万条（高性能）")
            print()
            print("推荐配置：10-15个线程，每批10-15万条记录")
    else:
        # 默认使用10线程，每批10万条
        updater.multi_thread_update(10, 100000)


if __name__ == "__main__":
    main()