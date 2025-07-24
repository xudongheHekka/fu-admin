import pymysql
import sys
import logging
from datetime import datetime
import signal
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import math

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sparse_id_update.log'),
        logging.StreamHandler()
    ]
)


class SmartSparseUpdater:
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
        self.max_in_clause_size = 8000

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        logging.info(f"接收到信号 {signum}，准备停止...")
        self.should_stop = True

    def get_connection(self):
        return pymysql.connect(**self.config)

    def analyze_id_distribution(self):
        """分析ID分布情况"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 基本统计
        cursor.execute("SELECT COUNT(*) FROM report_log WHERE report_date IS NULL")
        null_count = cursor.fetchone()[0]

        cursor.execute("SELECT MIN(id), MAX(id) FROM report_log WHERE report_date IS NULL")
        min_id, max_id = cursor.fetchone()

        # 采样分析ID分布
        cursor.execute("""
          SELECT id FROM report_log 
          WHERE report_date IS NULL 
          ORDER BY id 
          LIMIT 1000
      """)
        sample_ids = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        logging.info(f"待更新记录数: {null_count:,}")
        logging.info(f"ID范围: {min_id:,} - {max_id:,}")
        if len(sample_ids) >= 2:
            id_span = max_id - min_id
            density = null_count / id_span if id_span > 0 else 0
            logging.info(f"ID密度: {density:.10f} (记录数/ID范围)")

            # 分析前1000个ID的间隔
            gaps = [sample_ids[i + 1] - sample_ids[i] for i in range(min(len(sample_ids) - 1, 100))]
            avg_gap = sum(gaps) / len(gaps) if gaps else 0
            logging.info(f"平均ID间隔: {avg_gap:,.0f}")

        return null_count, min_id, max_id, sample_ids

    def chunk_based_update(self):
        """基于实际存在的ID块进行更新"""
        try:
            null_count, min_id, max_id, sample_ids = self.analyze_id_distribution()

            if null_count == 0:
                logging.info("没有需要更新的记录")
                return

            conn = self.get_connection()
            cursor = conn.cursor()
            start_time = datetime.now()

            logging.info("开始基于ID块的更新")

            total_updated = 0
            chunk_size = 10000  # 每次获取1万个ID
            batch_count = 0
            offset = 0

            while not self.should_stop:
                batch_start = datetime.now()

                # 获取一批实际存在的ID
                select_sql = f"""
                  SELECT id 
                  FROM report_log 
                  WHERE report_date IS NULL
                  ORDER BY id
                  LIMIT {chunk_size} OFFSET {offset}
              """

                cursor.execute(select_sql)
                ids = [row[0] for row in cursor.fetchall()]

                if not ids:
                    logging.info("没有更多记录需要更新")
                    break

                # 分批更新（避免IN子句过长）
                batch_updated = 0
                for i in range(0, len(ids), self.max_in_clause_size):
                    sub_ids = ids[i:i + self.max_in_clause_size]
                    id_list = ','.join(map(str, sub_ids))

                    update_sql = f"""
                      UPDATE report_log 
                      SET report_date = date(create_time) 
                      WHERE id IN ({id_list})
                  """

                    affected_rows = cursor.execute(update_sql)
                    batch_updated += affected_rows

                batch_end = datetime.now()

                total_updated += batch_updated
                batch_count += 1
                offset += chunk_size

                batch_time = (batch_end - batch_start).total_seconds()
                batch_speed = batch_updated / batch_time if batch_time > 0 else 0

                total_time = (batch_end - start_time).total_seconds()
                avg_speed = total_updated / total_time if total_time > 0 else 0

                progress = (total_updated / null_count) * 100
                remaining = null_count - total_updated
                eta_seconds = remaining / avg_speed if avg_speed > 0 else 0
                eta_hours = eta_seconds / 3600

                logging.info(f"块 {batch_count}: "
                             f"获取 {len(ids):,} 个ID, "
                             f"更新 {batch_updated:,} 条 ({batch_speed:.0f} 条/秒), "
                             f"累计 {total_updated:,} 条 ({progress:.2f}%), "
                             f"平均速度: {avg_speed:.0f} 条/秒, "
                             f"预计剩余: {eta_hours:.1f} 小时")

                # 动态调整块大小
                if batch_speed > 5000 and chunk_size < 50000:
                    chunk_size = min(chunk_size * 2, 50000)
                elif batch_speed < 1000 and chunk_size > 5000:
                    chunk_size = max(chunk_size // 2, 5000)

            cursor.close()
            conn.close()

            end_time = datetime.now()
            duration = end_time - start_time
            total_seconds = duration.total_seconds()
            avg_speed = total_updated / total_seconds if total_seconds > 0 else 0

            logging.info("=" * 80)
            logging.info(f"ID块更新完成！")
            logging.info(f"总更新记录: {total_updated:,} 条")
            logging.info(f"处理块数: {batch_count}")
            logging.info(f"总耗时: {duration}")
            logging.info(f"平均速度: {avg_speed:.0f} 条/秒")
            logging.info("=" * 80)

        except Exception as e:
            logging.error(f"ID块更新失败: {e}")
            raise

    def parallel_chunk_update(self, num_threads=8):
        """并行ID块更新"""
        try:
            null_count, min_id, max_id, sample_ids = self.analyze_id_distribution()

            if null_count == 0:
                logging.info("没有需要更新的记录")
                return

            logging.info(f"使用 {num_threads} 个线程并行处理ID块")

            start_time = datetime.now()
            total_updated = 0
            lock = threading.Lock()
            global_offset = 0

            def chunk_worker(thread_id):
                thread_updated = 0

                try:
                    conn = self.get_connection()
                    cursor = conn.cursor()

                    chunk_size = 8000  # 每个线程每次处理的ID数量
                    thread_batch_count = 0

                    while not self.should_stop:
                        # 使用锁获取下一批数据的偏移量
                        with lock:
                            nonlocal global_offset
                            current_offset = global_offset
                            global_offset += chunk_size

                        batch_start = datetime.now()

                        # 获取一批实际存在的ID
                        select_sql = f"""
                          SELECT id 
                          FROM report_log 
                          WHERE report_date IS NULL
                          ORDER BY id
                          LIMIT {chunk_size} OFFSET {current_offset}
                      """

                        cursor.execute(select_sql)
                        ids = [row[0] for row in cursor.fetchall()]

                        if not ids:
                            break

                        # 批量更新
                        id_list = ','.join(map(str, ids))
                        update_sql = f"""
                          UPDATE report_log 
                          SET report_date = date(create_time) 
                          WHERE id IN ({id_list})
                      """

                        affected_rows = cursor.execute(update_sql)
                        batch_end = datetime.now()

                        thread_updated += affected_rows
                        thread_batch_count += 1

                        batch_time = (batch_end - batch_start).total_seconds()
                        batch_speed = affected_rows / batch_time if batch_time > 0 else 0

                        with lock:
                            nonlocal total_updated
                            total_updated += affected_rows

                            total_time = (batch_end - start_time).total_seconds()
                            avg_speed = total_updated / total_time if total_time > 0 else 0
                            progress = (total_updated / null_count) * 100
                            remaining = null_count - total_updated
                            eta_seconds = remaining / avg_speed if avg_speed > 0 else 0
                            eta_hours = eta_seconds / 3600

                            if thread_batch_count % 5 == 0:
                                logging.info(f"线程 {thread_id}: "
                                             f"获取 {len(ids):,} 个ID, "
                                             f"更新 {affected_rows:,} 条 ({batch_speed:.0f} 条/秒), "
                                             f"线程累计 {thread_updated:,} 条, "
                                             f"总累计 {total_updated:,} 条 ({progress:.2f}%), "
                                             f"总速度: {avg_speed:.0f} 条/秒, "
                                             f"预计剩余: {eta_hours:.1f} 小时")

                    cursor.close()
                    conn.close()

                    logging.info(f"线程 {thread_id} 完成，更新了 {thread_updated:,} 条记录")
                    return thread_updated

                except Exception as e:
                    logging.error(f"线程 {thread_id} 失败: {e}")
                    return thread_updated

            # 使用线程池执行
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(chunk_worker, i + 1) for i in range(num_threads)]

                for future in as_completed(futures):
                    try:
                        result = future.result()
                    except Exception as e:
                        logging.error(f"线程执行异常: {e}")

            end_time = datetime.now()
            duration = end_time - start_time
            total_seconds = duration.total_seconds()
            avg_speed = total_updated / total_seconds if total_seconds > 0 else 0

            logging.info("=" * 80)
            logging.info(f"并行ID块更新完成！")
            logging.info(f"总更新记录: {total_updated:,} 条")
            logging.info(f"使用线程数: {num_threads}")
            logging.info(f"总耗时: {duration}")
            logging.info(f"平均速度: {avg_speed:.0f} 条/秒")
            logging.info("=" * 80)

        except Exception as e:
            logging.error(f"并行ID块更新失败: {e}")
            raise

    def time_based_update(self):
        """基于时间范围的更新（如果create_time有索引）"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 检查是否有时间范围
            cursor.execute("""
              SELECT MIN(create_time), MAX(create_time) 
              FROM report_log 
              WHERE report_date IS NULL
          """)
            min_time, max_time = cursor.fetchone()

            if not min_time or not max_time:
                logging.info("没有有效的时间范围，切换到ID块模式")
                cursor.close()
                conn.close()
                self.chunk_based_update()
                return

            logging.info(f"时间范围: {min_time} - {max_time}")

            start_time = datetime.now()
            total_updated = 0
            batch_count = 0

            # 按天处理
            current_date = min_time.date()
            end_date = max_time.date()

            while current_date <= end_date and not self.should_stop:
                batch_start = datetime.now()

                # 更新当天的记录
                update_sql = f"""
                  UPDATE report_log 
                  SET report_date = date(create_time) 
                  WHERE report_date IS NULL 
                  AND date(create_time) = '{current_date}'
              """

                affected_rows = cursor.execute(update_sql)
                batch_end = datetime.now()

                total_updated += affected_rows
                batch_count += 1

                batch_time = (batch_end - batch_start).total_seconds()
                batch_speed = affected_rows / batch_time if batch_time > 0 else 0

                if affected_rows > 0:
                    logging.info(f"日期 {current_date}: "
                                 f"更新 {affected_rows:,} 条 ({batch_speed:.0f} 条/秒), "
                                 f"累计 {total_updated:,} 条")

                current_date = current_date.replace(day=current_date.day + 1) if current_date.day < 28 else \
                    current_date.replace(month=current_date.month + 1, day=1) if current_date.month < 12 else \
                        current_date.replace(year=current_date.year + 1, month=1, day=1)

            cursor.close()
            conn.close()

            end_time = datetime.now()
            duration = end_time - start_time
            total_seconds = duration.total_seconds()
            avg_speed = total_updated / total_seconds if total_seconds > 0 else 0

            logging.info("=" * 80)
            logging.info(f"时间范围更新完成！")
            logging.info(f"总更新记录: {total_updated:,} 条")
            logging.info(f"处理天数: {batch_count}")
            logging.info(f"总耗时: {duration}")
            logging.info(f"平均速度: {avg_speed:.0f} 条/秒")
            logging.info("=" * 80)

        except Exception as e:
            logging.error(f"时间范围更新失败: {e}")
            # 回退到ID块模式
            logging.info("回退到ID块模式")
            self.chunk_based_update()

    # def smart_update(self):
    #     """智能选择最优策略"""
    #     try:
    #         null_count, min_id, max_id, sample_ids = self.analyze_id_distribution()
    #
    #         if null_count == 0:
    #             logging.info("没有需要更新的记录")
    #             return
    #
    #         # 根据数据量和分布选择策略
    #         if null_count > 100000000:  # 超过1亿条
    #             logging.info("数据量巨大，使用12线程并行ID块更新")
    #             self.parallel_chunk_update(12)
    #         elif null_count > 10000000:  # 超过1000万条
    #             logging.info("数据量较大，使用8线程并行ID块更新")
    #             self.parallel_chunk_update(8)
    #         elif null_count > 1000000:  # 超过100万条
    #             logging.info("数据量中等，使用4线程并行ID块更新")
    #             self.parallel_chunk_update(4)
    #         else:
    #             logging.info("数据量较小，使用单线程ID块更新")
    #             self.chunk_based_update()
    #
    #     except Exception as e:
    #         logging.error(f"智能更新失败: {e}")
    #         raise

    def smart_update(self):
        """智能选择最优策略"""
        try:
            null_count, min_id, max_id, sample_ids = self.analyze_id_distribution()

            if null_count == 0:
                logging.info("没有需要更新的记录")
                return

            # 固定使用3个线程
            logging.info("使用3个线程进行并行更新")
            self.parallel_chunk_update(3)  # 固定使用3个线程

        except Exception as e:
            logging.error(f"智能更新失败: {e}")
            raise



def main():
    updater = SmartSparseUpdater()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == 'analyze':
            updater.analyze_id_distribution()
        elif command == 'chunk':
            # 单线程ID块更新
            updater.chunk_based_update()
        elif command == 'parallel':
            # 并行ID块更新
            threads = int(sys.argv[2]) if len(sys.argv) > 2 else 8
            updater.parallel_chunk_update(threads)
        elif command == 'time':
            # 基于时间的更新
            updater.time_based_update()
        elif command == 'smart':
            # 智能选择策略
            updater.smart_update()
        else:
            print("智能稀疏ID更新器:")
            print("  python script.py analyze      # 分析ID分布")
            print("  python script.py smart        # 智能选择策略（推荐）")
            print("  python script.py parallel 12  # 12线程并行ID块更新")
            print("  python script.py chunk        # 单线程ID块更新")
            print("  python script.py time         # 基于时间范围更新")
            print()
            print("推荐使用 smart 模式")
    else:
        # 默认使用智能模式
        updater.smart_update()


if __name__ == "__main__":
    main()