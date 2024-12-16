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
import os
from datetime import datetime
from selenium.webdriver.common.action_chains import ActionChains
# 官方文档地址
# https://doc2.bitbrowser.cn/jiekou/ben-di-fu-wu-zhi-nan.html

# 此demo仅作为参考使用，以下使用的指纹参数仅是部分参数，完整参数请参考文档

url = "http://127.0.0.1:54345"
downloaded_element_id = "rc-tabs-1-panel-mine"
click_mine_element_id = "rc-tabs-1-tab-mine"
headers = {'Content-Type': 'application/json'}
video_dict = {}


def createBrowser():  # 创建或者更新窗口，指纹参数 browserFingerPrint 如没有特定需求，只需要指定下内核即可，如果需要更详细的参数，请参考文档
    json_data = {
        'name': 'google',  # 窗口名称
        'remark': '',  # 备注
        'proxyMethod': 2,  # 代理方式 2自定义 3 提取IP
        # 代理类型  ['noproxy', 'http', 'https', 'socks5', 'ssh']
        'proxyType': 'noproxy',
        'host': '',  # 代理主机
        'port': '',  # 代理端口
        'proxyUserName': '',  # 代理账号
        "browserFingerPrint": {  # 指纹对象
            'coreVersion': '112'  # 内核版本 112 | 104，建议使用112，注意，win7/win8/winserver 2012 已经不支持112内核了，无法打开
        }
    }

    res = requests.post(f"{url}/browser/update",
                        data=json.dumps(json_data), headers=headers).json()
    browserId = res['data']['id']
    print(browserId)
    return browserId


def updateBrowser():  # 更新窗口，支持批量更新和按需更新，ids 传入数组，单独更新只传一个id即可，只传入需要修改的字段即可，比如修改备注，具体字段请参考文档，browserFingerPrint指纹对象不修改，则无需传入
    json_data = {'ids': ['93672cf112a044f08b653cab691216f0'],
                 'remark': '我是一个备注', 'browserFingerPrint': {}}
    res = requests.post(f"{url}/browser/update/partial",
                        data=json.dumps(json_data), headers=headers).json()
    print(res)


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


def deleteBrowser(id):  # 删除窗口
    json_data = {'id': f'{id}'}
    print(requests.post(f"{url}/browser/delete",
          data=json.dumps(json_data), headers=headers).json())


def setup_driver_with_devtools():
    # 存儲捕獲到的網絡請求
    captured_requests = []
    
    def process_browser_logs_for_network_events(logs):
        for entry in logs:
            try:
                log = json.loads(entry["message"])["message"]
                if "Network.response" in log["method"] or "Network.request" in log["method"]:
                    captured_requests.append(log)
            except:
                pass
        return captured_requests

    # 設置 Chrome DevTools Protocol 監聽器
    options = webdriver.ChromeOptions()
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    # 其他必要的設置...
    driver, browser_id = bit.get_driver(
        username='your_username',
        password='your_password',
        proxyType='noproxy',
        options=options  # 添加 options
    )
    
    return driver, browser_id, captured_requests


def monitor_network(driver, url):
    # 訪問目標網頁
    driver.get(url)
    
    # 等待頁面加載（可根據實際情況調整）
    time.sleep(5)
    
    # 獲取瀏覽器日誌
    logs = driver.get_log('performance')
    
    # 分析網絡請求
    for log in logs:
        try:
            # 解析日誌消息
            log_data = json.loads(log['message'])['message']
            
            # 檢查請求URL和響應數據
            if 'params' in log_data:
                params = log_data['params']
                
                # 檢查請求URL
                if 'request' in params and 'url' in params['request']:
                    url = params['request']['url']
                    if '.m3u8' in url or '.js' in url:
                        print(f"發現相關請求: {url}")
                
                # 檢查響應數據
                if 'response' in params:
                    response_data = params['response']
                    # 可以進一步分析響應內容
                    
        except Exception as e:
            continue


def intercept_websocket():
    # 注入 JavaScript 來監聽 WebSocket
    websocket_script = """
    var originalWebSocket = window.WebSocket;
    window.WebSocket = function(url, protocols) {
        var ws = new originalWebSocket(url, protocols);
        ws.addEventListener('message', function(event) {
            // 將 WebSocket 消息保存到全局變量
            if (!window.wsMessages) window.wsMessages = [];
            window.wsMessages.push(event.data);
        });
        return ws;
    };
    """
    driver.execute_script(websocket_script)


def check_network_requests():
    try:
        # 設置並啟動帶有 DevTools 的驅動
        driver, browser_id, captured_requests = setup_driver_with_devtools()
        
        # 訪問目標網頁
        target_url = "your_target_url"
        driver.get(target_url)
        
        # 注入 WebSocket 監聽器
        intercept_websocket()
        
        # 等待頁面完全加載
        time.sleep(5)  # 可以根據需要調整等待時間
        
        # 監控網絡請求
        monitor_network(driver, target_url)
        
        # 獲取 WebSocket 消息
        ws_messages = driver.execute_script("return window.wsMessages || [];")
        for message in ws_messages:
            if 'rtmp://' in str(message):
                print(f"在WebSocket中發現RTMP URL: {message}")
        
        # 分析所有JavaScript文件
        js_files = driver.execute_script("""
            var links = document.getElementsByTagName('script');
            var sources = [];
            for(var i = 0; i < links.length; i++) {
                if(links[i].src) sources.push(links[i].src);
            }
            return sources;
        """)
        
        for js_file in js_files:
            if js_file:
                try:
                    response = requests.get(js_file)
                    if 'rtmp://' in response.text:
                        print(f"在JS文件中發現RTMP URL: {js_file}")
                        # 使用正則表達式提取具體的RTMP URL
                        rtmp_urls = re.findall(r'rtmp://[^\s<>"\']+', response.text)
                        print(f"提取的RTMP URLs: {rtmp_urls}")
                except:
                    continue
                    
    except Exception as e:
        print(f"發生錯誤: {str(e)}")
    finally:
        # 關閉瀏覽器
        bit.close_browser(browser_id)
        bit.del_browser(browser_id)

# def get_mine_videos(driver, timeout=10, downloaded_csv="downloaded_videos.csv"):
#     try:
#         # 等待面板加載
#         print("等待面板加載...")
#         panel = WebDriverWait(driver, timeout).until(
#             EC.presence_of_element_located((By.ID, "rc-tabs-0-panel-mine"))
#         )
        
#         # 等待初始視頻加載
#         time.sleep(5)
        
#         # 滾動加載所有視頻
#         last_height = driver.execute_script("return arguments[0].scrollHeight", panel)
#         while True:
#             # 找到當前可見的所有視頻
#             videos = panel.find_elements(By.TAG_NAME, "video")
#             current_video_count = len(video_dict)
            
#             print(f"當前已找到 {len(videos)} 個視頻")
            
#             # 處理當前可見的視頻
#             for index, video in enumerate(videos, start=1):
#                 try:
#                     src = video.get_attribute('src')
#                     if src and src not in video_dict:  # 確保不重複記錄
#                         video_dict[src] = True
                        
#                         # 寫入CSV
#                         with open(downloaded_csv, 'a', newline='', encoding='utf-8') as f:
#                             writer = csv.writer(f)
#                             if index == 1 and not os.path.getsize(downloaded_csv):
#                                 writer.writerow(['timestamp', 'video_url', 'status'])
#                             writer.writerow([
#                                 datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#                                 src,
#                                 'downloaded'
#                             ])
#                 except Exception as e:
#                     print(f"處理第 {index} 個視頻時出錯: {str(e)}")
#                     continue
            
#             # 滾動到面板底部
#             driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", panel)
#             time.sleep(2)  # 等待新內容加載
            
#             # 檢查是否到達底部
#             new_height = driver.execute_script("return arguments[0].scrollHeight", panel)
#             if new_height == last_height:
#                 # 再次檢查是否有新視頻加入
#                 if len(video_dict) == current_video_count:
#                     print("已到達底部，沒有更多視頻")
#                     break
#             last_height = new_height
            
#             print("繼續滾動加載...")
        
#         # 輸出最終統計信息
#         print(f"\n總共找到 {len(video_dict)} 條視頻")
#         print("\n視頻列表：")
#         for src in video_dict.keys():
#             print(f"視頻鏈接: {src}")
            
#         return video_dict
        
#     except Exception as e:
#         print(f"獲取視頻列表時發生錯誤: {str(e)}")
#         return {}
def get_mine_videos(driver, timeout=10, downloaded_csv="downloaded_videos.csv"):
    video_dict = {}
    try:
        # 等待面板加載
        print("等待面板加載...")
        panel = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, downloaded_element_id))
        )
        
        # 等待初始視頻加載
        time.sleep(5)
        
        def get_current_videos():
            """獲取當前頁面上的視頻數量"""
            return len(panel.find_elements(By.TAG_NAME, "video"))
        
        def scroll_panel():
            """滾動面板到底部"""
            try:
                # 使用 JavaScript 滾動到底部
                driver.execute_script("""
                    var panel = document.getElementById(arguments[0]);
                    panel.scrollTop = panel.scrollHeight;
                """, downloaded_element_id)
                # 備用滾動方法
                if panel:
                    actions = ActionChains(driver)
                    actions.move_to_element(panel).perform()
                    panel.send_keys(Keys.END)
            except Exception as e:
                print(f"滾動時發生錯誤: {str(e)}")
        
        # 初始視頻數量
        previous_count = 0
        current_count = get_current_videos()
        no_new_videos_count = 0
        max_no_new_attempts = 3
        
        print(f"初始視頻數量: {current_count}")
        
        # 持續滾動直到沒有新視頻
        while True:
            scroll_panel()
            print("滾動加載中...")
            time.sleep(3)  # 等待新內容加載
            
            # 嘗試點擊"加載更多"按鈕（如果存在）
            try:
                load_more = driver.find_element(By.XPATH, "//button[contains(text(), '加載更多')]")
                if load_more and load_more.is_displayed():
                    load_more.click()
                    time.sleep(2)
            except:
                pass
            
            previous_count = current_count
            current_count = get_current_videos()
            
            print(f"當前視頻數量: {current_count}")
            
            if current_count > previous_count:
                print(f"發現 {current_count - previous_count} 個新視頻")
                no_new_videos_count = 0
            else:
                no_new_videos_count += 1
                print(f"沒有發現新視頻 ({no_new_videos_count}/{max_no_new_attempts})")
                
                if no_new_videos_count >= max_no_new_attempts:
                    # 最後再試一次滾動
                    scroll_panel()
                    time.sleep(3)
                    final_count = get_current_videos()
                    if final_count == current_count:
                        print("已經到達底部，停止滾動")
                        break
                    else:
                        current_count = final_count
                        no_new_videos_count = 0
        
        # 獲取所有視頻的 src
        print("\n開始收集視頻信息...")
        videos = panel.find_elements(By.TAG_NAME, "video")
        print (videos, len(videos))
        # 處理視頻信息
        for index, video in enumerate(videos, 1):
            try:
                src = video.get_attribute('src')
                if src and src not in video_dict:
                    video_dict[src] = True
                    # 寫入CSV
                    with open(downloaded_csv, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        if index == 1 and not os.path.getsize(downloaded_csv):
                            writer.writerow(['timestamp', 'video_url', 'status'])
                        writer.writerow([
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            src,
                            'downloaded'
                        ])
            except Exception as e:
                print(f"處理第 {index} 個視頻時出錯: {str(e)}")
                continue
        
        print(f"\n總共找到 {len(video_dict)} 個視頻")
        return video_dict
        
    except Exception as e:
        print(f"獲取視頻列表時發生錯誤: {str(e)}")
        return {}

def find_and_click_mine_tab(driver, timeout=60):
    wait = WebDriverWait(driver, timeout)
    
    # 嘗試不同的定位方式
    locators = [
        (By.CSS_SELECTOR, f"div.ant-tabs-tab-btn#{click_mine_element_id}"),  # 使用 class 和 id 組合
        (By.XPATH, f"//div[@class='ant-tabs-tab-btn' and @id={click_mine_element_id}]"),  # 使用 XPath
        (By.ID, f"click_mine_element_id")  # 僅使用 ID
    ]
    
    for by, value in locators:
        try:
            print(f"Trying to find Mine tab using {by}: {value}")
            element = wait.until(EC.element_to_be_clickable((by, value)))
            print("Mine tab found, clicking...")
            element.click()
            print("Mine tab clicked successfully")
            return True
        except Exception as e:
            print(f"Failed with {by}: {value} - {str(e)}")
            continue
    
    print("Failed to find and click Mine tab with all methods")
    return False



def monitor_video_changes(driver, initial_videos, csv_filename="pending_downloads.csv", check_interval=60):
    """
    監控視頻變化並記錄新的視頻到CSV
    
    Args:
        driver: WebDriver實例
        initial_videos: 初始視頻字典
        csv_filename: CSV文件名
        check_interval: 檢查間隔（秒）
    """
    try:
        while True:
            print(f"\n[{datetime.now()}] 開始檢查新視頻...")
            
            # 等待面板
            panel = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "rc-tabs-1-panel-mine"))
            )
            
            # 找到所有視頻標籤
            videos = panel.find_elements(By.TAG_NAME, "video")
            new_videos_found = False
            
            # 檢查每個視頻
            for video in videos:
                try:
                    src = video.get_attribute('src')
                    if src and src not in initial_videos:
                        new_videos_found = True
                        print(f"發現新視頻: {src}")
                        
                        # 將新視頻添加到CSV
                        with open(csv_filename, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                src,
                                'pending'  # 狀態標記
                            ])
                        
                        # 更新字典
                        initial_videos[src] = True
                        
                except Exception as e:
                    print(f"處理視頻時出錯: {str(e)}")
                    continue
            
            if not new_videos_found:
                print("沒有發現新視頻")
            
            # 等待指定時間後再次檢查
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print("\n監控已停止")
    except Exception as e:
        print(f"監控過程中發生錯誤: {str(e)}")
        
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

def run_browser_session():
    """執行一個完整的瀏覽器會話"""
    account = get_latest_account()
    if not account:
        print("未找到可用的瀏覽器帳號，請先運行 create_bitbrowser.py")
        return False
        
    website = 'google'
    # bit = BitBrowser(website)
    browser_id = None
    
    try:
        # 使用保存的帳號密碼創建瀏覽器
        browser_id = account['browser_id']
        res = openBrowser(browser_id)
        print(f"\n已開啟比特瀏覽器id：{browser_id}")
        driverPath = res['data']['driver']
        debuggerAddress = res['data']['http']

        print(driverPath)
        print(debuggerAddress)

        # selenium 连接代码
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option("debuggerAddress", debuggerAddress)

        chrome_service = Service(driverPath)
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
        
        csv_filename = "pending_downloads.csv"
        downloaded_csv = "downloaded_videos.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'video_url', 'status'])
        
        driver.get('https://hailuoai.video/')
        time.sleep(5)
        
        if find_and_click_mine_tab(driver, timeout=60):
            initial_videos = get_mine_videos(driver)
            print(f"初始視頻數量: {len(initial_videos)}")
            monitor_video_changes(driver, initial_videos, csv_filename)
            
        return True
        
    except Exception as e:
        print(f"執行過程中發生錯誤: {str(e)}")
        return False
    finally:
        if browser_id:
                pass

def main_loop():
    """主循環，處理重試邏輯"""
    retry_delay = 60  # 重試等待時間（秒）
    max_retries = 3   # 最大連續失敗次數
    consecutive_failures = 0
    
    print("啟動監控程序...")
    
    while True:
        try:
            success = run_browser_session()
            
            if success:
                consecutive_failures = 0  # 重置失敗計數
            else:
                consecutive_failures += 1
                print(f"執行失敗，這是第 {consecutive_failures} 次連續失敗")
                
                if consecutive_failures >= max_retries:
                    print(f"已達到最大連續失敗次數 ({max_retries})，等待較長時間後重試...")
                    time.sleep(retry_delay * 2)  # 加倍等待時間
                    consecutive_failures = 0  # 重置失敗計數
                else:
                    print(f"等待 {retry_delay} 秒後重試...")
                    time.sleep(retry_delay)
            
        except KeyboardInterrupt:
            print("\n檢測到用戶中斷，程序結束")
            break
        except Exception as e:
            print(f"主循環發生意外錯誤: {str(e)}")
            consecutive_failures += 1
            time.sleep(retry_delay)

if __name__ == '__main__':
    main_loop()
