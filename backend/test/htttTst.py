import requests
import threading
import time
import json
from datetime import datetime
import statistics

# 压测配置
URL = "https://api-meeting.weizhiyanchina.com/web/act/award/open"
HEADERS = {
    "token": "jeUWilf/XCrult+uG28FLNQOcsJnNsn3GtzZwMnpi10=",
    "Content-Type": "application/json"
}
PAYLOAD = {
    "act_code": "WOMAN2025",
    "module_name": "女神化妆盒",
    "amount": 10,
    "group_module": 1
}
THREAD_COUNT = 1
TEST_DURATION = 6  # 10分钟，单位：秒

# 统计数据
stats = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "response_times": [],
    "start_time": None,
    "is_running": True
}

# 线程锁，用于更新统计数据
stats_lock = threading.Lock()


def make_request():
    """发送单个请求并记录结果"""
    try:
        start_time = time.time()
        response = requests.post(URL, headers=HEADERS, json=PAYLOAD, timeout=10)
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # 转换为毫秒

        with stats_lock:
            stats["total_requests"] += 1
            stats["response_times"].append(response_time)

            if response.status_code == 200:
                stats["successful_requests"] += 1
            else:
                stats["failed_requests"] += 1
                print(f"请求失败: 状态码 {response.status_code}, 响应: {response.text}")

        return response.status_code, response_time, response.text
    except Exception as e:
        with stats_lock:
            stats["total_requests"] += 1
            stats["failed_requests"] += 1
        print(f"请求异常: {str(e)}")
        return None, None, str(e)


def worker():
    """工作线程函数，持续发送请求直到测试结束"""
    while stats["is_running"]:
        make_request()


def print_stats():
    """打印当前统计数据"""
    elapsed_time = time.time() - stats["start_time"]
    requests_per_second = stats["total_requests"] / elapsed_time if elapsed_time > 0 else 0

    success_rate = 0
    if stats["total_requests"] > 0:
        success_rate = (stats["successful_requests"] / stats["total_requests"]) * 100

    avg_response_time = 0
    median_response_time = 0
    min_response_time = 0
    max_response_time = 0
    p95_response_time = 0

    if stats["response_times"]:
        avg_response_time = sum(stats["response_times"]) / len(stats["response_times"])
        median_response_time = statistics.median(stats["response_times"])
        min_response_time = min(stats["response_times"])
        max_response_time = max(stats["response_times"])
        sorted_times = sorted(stats["response_times"])
        p95_index = int(len(sorted_times) * 0.95)
        p95_response_time = sorted_times[p95_index]

    print("\n" + "=" * 50)
    print(f"运行时间: {elapsed_time:.2f} 秒")
    print(f"总请求数: {stats['total_requests']}")
    print(f"成功请求: {stats['successful_requests']}")
    print(f"失败请求: {stats['failed_requests']}")
    print(f"成功率: {success_rate:.2f}%")
    print(f"每秒请求数 (RPS): {requests_per_second:.2f}")
    print(f"平均响应时间: {avg_response_time:.2f} ms")
    print(f"中位数响应时间: {median_response_time:.2f} ms")
    print(f"最小响应时间: {min_response_time:.2f} ms")
    print(f"最大响应时间: {max_response_time:.2f} ms")
    print(f"95%响应时间: {p95_response_time:.2f} ms")
    print("=" * 50)


def run_load_test():
    """运行压力测试"""
    print(f"开始压测 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标 URL: {URL}")
    print(f"线程数: {THREAD_COUNT}")
    print(f"测试时间: {TEST_DURATION} 秒")

    # 初始化统计数据
    stats["start_time"] = time.time()
    stats["is_running"] = True

    # 创建并启动工作线程
    threads = []
    for i in range(THREAD_COUNT):
        thread = threading.Thread(target=worker)
        thread.daemon = True
        threads.append(thread)
        thread.start()

    # 定期打印统计数据
    try:
        start_time = time.time()
        while time.time() - start_time < TEST_DURATION:
            time.sleep(5)  # 每5秒打印一次统计数据
            print_stats()

        # 测试结束
        stats["is_running"] = False

        # 等待所有线程结束
        for thread in threads:
            thread.join(1)

        # 打印最终统计数据
        print("\n测试完成！最终统计数据:")
        print_stats()

        # 保存结果到文件
        save_results()

    except KeyboardInterrupt:
        print("\n用户中断测试...")
        stats["is_running"] = False

        # 等待所有线程结束
        for thread in threads:
            thread.join(1)

        # 打印最终统计数据
        print("\n测试中断！最终统计数据:")
        print_stats()

        # 保存结果到文件
        save_results()


def save_results():
    """保存测试结果到文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"loadtest_results_{timestamp}.txt"

    elapsed_time = time.time() - stats["start_time"]
    requests_per_second = stats["total_requests"] / elapsed_time if elapsed_time > 0 else 0

    success_rate = 0
    if stats["total_requests"] > 0:
        success_rate = (stats["successful_requests"] / stats["total_requests"]) * 100

    with open(filename, "w", encoding="utf-8") as f:
        f.write("压力测试结果\n")
        f.write("=" * 50 + "\n")
        f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"目标 URL: {URL}\n")
        f.write(f"线程数: {THREAD_COUNT}\n")
        f.write(f"测试持续时间: {elapsed_time:.2f} 秒\n\n")

        f.write("统计数据:\n")
        f.write(f"总请求数: {stats['total_requests']}\n")
        f.write(f"成功请求: {stats['successful_requests']}\n")
        f.write(f"失败请求: {stats['failed_requests']}\n")
        f.write(f"成功率: {success_rate:.2f}%\n")
        f.write(f"每秒请求数 (RPS): {requests_per_second:.2f}\n\n")

        if stats["response_times"]:
            avg_response_time = sum(stats["response_times"]) / len(stats["response_times"])
            median_response_time = statistics.median(stats["response_times"])
            min_response_time = min(stats["response_times"])
            max_response_time = max(stats["response_times"])
            sorted_times = sorted(stats["response_times"])
            p95_index = int(len(sorted_times) * 0.95)
            p95_response_time = sorted_times[p95_index]

            f.write("响应时间统计 (毫秒):\n")
            f.write(f"平均响应时间: {avg_response_time:.2f}\n")
            f.write(f"中位数响应时间: {median_response_time:.2f}\n")
            f.write(f"最小响应时间: {min_response_time:.2f}\n")
            f.write(f"最大响应时间: {max_response_time:.2f}\n")
            f.write(f"95%响应时间: {p95_response_time:.2f}\n")

    print(f"测试结果已保存到文件: {filename}")


if __name__ == "__main__":
    run_load_test()
