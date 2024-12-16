import os
import threading
import requests
import json
import time
import logging
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
# from python-demo.bit_api import *
# from BitAPI import *
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import csv
from datetime import datetime
from selenium.webdriver.common.action_chains import ActionChains

url = "http://127.0.0.1:54345"
downloaded_element_id = "rc-tabs-1-panel-mine"
click_mine_element_id = "rc-tabs-1-tab-mine"
headers = {'Content-Type': 'application/json'}
video_dict = {}

def openBrowser(id):  # 直接指定ID打开窗口，也可以使用 createBrowser 方法返回的ID
    json_data = {"id": f'{id}'}
    res = requests.post(f"{url}/browser/open",
                        data=json.dumps(json_data), headers=headers).json()
    print(res)
    print(res['data']['http'])
    return res

def closeBrowser(id):  # 关闭窗口
    json_data = {'id': f'{id}'}
    requests.post(f"{url}/browser/close",
                  data=json.dumps(json_data), headers=headers).json()


def get_latest_account():
    """從 CSV 文件中獲取最新的帳號信息"""
    try:
        with open('bitbrowser_accounts.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # 轉換為列表並獲取最後一個記錄
            accounts = list(reader)
            if accounts:
                return accounts[-1]  # 返回最新的帳號
    except Exception as e:
        print(f"讀取帳號文件時發生錯誤: {str(e)}")
    return None


def delete_video(driver, video_url):
    """删除视频并确认，直到没有视频可以删除，同时更新 CSV 文件"""
    while True:
        try:
            # 找到删除按钮的父元素，进行鼠标悬停
            delete_button_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#scroll_wrap > main > section > div.detail-prompt-web.flex.w-\[350px\].max-w-\[350px\].flex-1.flex-col.items-center.justify-between.gap-6.pl-6.pb-\[78px\].pt-6.text-white.pr-\[5px\] > div.flex.w-full.h-11.items-center.justify-center.gap-\[10px\].text-\[14px\] > button:nth-child(4)")
                )
            )

            # 使用 ActionChains 执行鼠标悬停
            actions = ActionChains(driver)
            actions.move_to_element(delete_button_element).perform()
            print("鼠标悬停到删除按钮")

            # 等待删除按钮（Delete）出现并点击
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

            # 从 CSV 文件中删除对应的视频 URL
            remove_video_from_csv(video_url)

            # 等待删除完成
            time.sleep(2)  # 可以根据实际情况调整时间

        except Exception as e:
            print(f"删除视频时发生错误: {e}")
            break  # 如果发生错误，退出循环


def run_browser_session():
    """执行一个完整的浏览器会话，处理视频ID并进行操作"""
    video_ids = process_csv('downloaded_videos.csv')

    if not video_ids:
        print("没有找到有效的视频ID，程序退出。")
        return False

    account = get_latest_account()

    if not account:
        print("未找到可用的浏览器帐户，請先運行 create_bitbrowser.py")
        return False

    website = 'google'
    browser_id = None

    try:
        browser_id = account['browser_id']
        res = openBrowser(browser_id)
        print(f"\n已开起比特浏览器id：{browser_id}")

        driverPath = res['data']['driver']
        debuggerAddress = res['data']['http']

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option("debuggerAddress", debuggerAddress)

        chrome_service = Service(driverPath)
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

        # 逐个处理每个视频ID
        for video_id in video_ids:
            video_url = f"https://hailuoai.video/mine-ai-videos/{video_id}"
            driver.get(video_url)
            time.sleep(5)

            # 在这里调用 delete_video 时传递 video_url
            delete_video(driver, video_url)

        print("所有视频处理完成。")
        return True

    except Exception as e:
        print(f"执行过程中发生错误: {str(e)}")
        return False

    finally:
        if browser_id:
            try:
                closeBrowser(browser_id)
                print("浏览器关闭成功")
            except Exception as e:
                print(f"关闭浏览器时发生错误: {str(e)}")


def remove_video_from_csv(video_url):
    """从 CSV 文件中删除指定的视频 URL"""
    rows = []
    with open('downloaded_videos.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['video_url'] != video_url:  # 保留不匹配的行
                rows.append(row)

    with open('downloaded_videos.csv', 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['timestamp', 'video_url', 'status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()  # 写入表头
        writer.writerows(rows)  # 写入剩余的行

def process_csv(file_path):
    """处理 CSV 文件，去重并提取 videoid"""
    video_ids = set()  # 使用 set 去重

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # 跳过表头
        for row in reader:
            # 假设视频 URL 在第二列（row[1]）
            video_url = row[1]

            # 使用 "_" 分割并提取倒数第二部分作为 videoid（去掉".mp4"）
            video_id = video_url.split('_')[-1].split('.')[0]

            video_ids.add(video_id)  # 添加到 set 去重
        print(len(video_ids))
    return list(video_ids)  # 返回去重后的 videoid 列表



def main_loop():
    """主循环，处理重试逻辑"""
    retry_delay = 60  # 重试等待时间（秒）
    max_retries = 3  # 最大连续失败次数
    consecutive_failures = 0

    while True:
        try:
            # 执行浏览器会话操作
            run_browser_session()

        except KeyboardInterrupt:
            print("\n检测到用户中断，程序结束")
            break
        except Exception as e:
            print(f"主循环发生意外错误: {str(e)}")
            consecutive_failures += 1
            time.sleep(retry_delay)


if __name__ == '__main__':
    main_loop()