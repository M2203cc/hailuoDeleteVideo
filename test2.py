import os
import threading
import requests
import json
import time
import logging
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
from datetime import datetime
from selenium.webdriver.common.action_chains import ActionChains
from queue import Queue
import fcntl

# Configuration for controlling request frequency
REQUESTS_PER_SECOND = 10
request_queue = Queue()  # Request queue for controlling request frequency

url = "http://127.0.0.1:54345"
downloaded_element_id = "rc-tabs-1-panel-mine"
click_mine_element_id = "rc-tabs-1-tab-mine"
headers = {'Content-Type': 'application/json'}
video_dict = {}


def openBrowser(id):
    json_data = {"id": f'{id}'}
    res = requests.post(f"{url}/browser/open", data=json.dumps(json_data), headers=headers).json()
    return res


def closeBrowser(id):
    json_data = {'id': f'{id}'}
    requests.post(f"{url}/browser/close", data=json.dumps(json_data), headers=headers).json()


def get_latest_account():
    """从 CSV 文件中获取最新的账户信息"""
    try:
        with open('bitbrowser_accounts.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            accounts = list(reader)
            if accounts:
                return accounts[-1]  # 返回最新的账户
    except Exception as e:
        print(f"读取账户文件时发生错误: {str(e)}")
    return None


def process_csv(file_path):
    """处理 CSV 文件，去重并提取 videoid"""
    video_ids = set()  # 使用 set 去重
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # 跳过表头
        for row in reader:
            video_url = row[1]
            video_id = video_url.split('_')[-1].split('.')[0]
            video_ids.add(video_id)
    return list(video_ids)  # 返回去重后的 videoid 列表


def delete_video(driver):
    """删除视频并确认，直到没有视频可以删除"""
    while True:
        try:
            # 找到删除按钮的父元素，进行鼠标悬停
            delete_button_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[@id='scroll_wrap']/main/section/div[3]/div[2]/button[3]"))
            )

            actions = ActionChains(driver)
            actions.move_to_element(delete_button_element).perform()
            print("鼠标悬停到删除按钮")

            # 等待删除按钮出现并点击
            delete_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.w-full.flex.items-center:last-child"))
            )
            delete_button.click()
            print("点击了删除按钮")

            # 等待确认删除并点击
            confirm_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/div[2]/div/div[2]/div[3]/button[2]/span"))
            )
            confirm_button.click()
            print("确认删除视频")

            time.sleep(2)  # 可以根据实际情况调整时间

        except Exception as e:
            print(f"删除视频时发生错误: {e}")
            break  # 如果发生错误，退出循环


def handle_request_frequency():
    """控制每秒最多10个请求"""
    while True:
        request_queue.get()  # 获取任务
        time.sleep(1 / REQUESTS_PER_SECOND)  # 控制每秒最多请求次数


def process_video_deletion(video_id, driver):
    """处理单个视频的删除操作，并控制请求频率"""
    try:
        video_url = f"https://hailuoai.video/mine-ai-videos/{video_id}"
        driver.get(video_url)
        time.sleep(5)  # 等待页面加载
        delete_video(driver)
        print(f"视频 {video_id} 删除成功")
    except Exception as e:
        print(f"视频 {video_id} 删除失败: {e}")


def run_all_sessions_in_parallel(video_ids):
    """使用线程池并行删除所有视频"""
    threads = []
    account = get_latest_account()
    if not account:
        print("未找到可用的浏览器帐户，請先運行 create_bitbrowser.py")
        return False

    website = 'google'
    browser_id = None

    browser_id = account['browser_id']
    res = openBrowser(browser_id)
    print(f"\n已开起比特浏览器id：{browser_id}")
    driverPath = res['data']['driver']
    debuggerAddress = res['data']['http']
    # 配置 Selenium 连接
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("debuggerAddress", debuggerAddress)

    chrome_service = Service(driverPath)
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    # Split video IDs into chunks and run each chunk in a separate thread
    chunk_size = len(video_ids) // 3
    video_id_chunks = [video_ids[i:i + chunk_size] for i in range(0, len(video_ids), chunk_size)]

    for chunk in video_id_chunks:
        thread = threading.Thread(target=process_video_deletion_chunk, args=(chunk, driver))
        threads.append(thread)
        thread.start()
        request_queue.put(1)  # 将请求加入队列

    # 启动一个线程来控制请求频率
    frequency_control_thread = threading.Thread(target=handle_request_frequency)
    frequency_control_thread.daemon = True
    frequency_control_thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    print("所有视频删除完成。")


def process_video_deletion_chunk(video_ids, driver):
    """处理视频删除的一个数据块"""
    for video_id in video_ids:
        process_video_deletion(video_id, driver)


def run_browser_session():
    """执行一个完整的浏览器会话，处理视频ID并进行操作"""
    video_ids = process_csv('downloaded_videos.csv')
    print(video_ids)
    if not video_ids:
        print("没有找到有效的视频ID，程序退出。")
        return False
    try:
        # 逐个处理每个视频ID
        run_all_sessions_in_parallel(video_ids)

        print("所有视频处理完成。")
        return True

    except Exception as e:
        print(f"执行过程中发生错误: {str(e)}")
        return False




def main_loop():
    """主循环，处理重试逻辑"""
    retry_delay = 60  # 重试等待时间（秒）
    max_retries = 3  # 最大连续失败次数
    consecutive_failures = 0

    while True:
        try:
            success = run_browser_session()

            if success:
                print("成功完成所有操作")
                break  # 成功时退出循环

        except KeyboardInterrupt:
            print("\n检测到用户中断，程序结束")
            break
        except Exception as e:
            print(f"主循环发生意外错误: {str(e)}")
            consecutive_failures += 1
            if consecutive_failures >= max_retries:
                print("达到最大失败次数，程序退出")
                break
            time.sleep(retry_delay)


if __name__ == '__main__':
    main_loop()
