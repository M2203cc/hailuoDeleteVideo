import csv
import time
import os
import random
import string
from datetime import datetime
import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service       

# from BitAPI import *

url = "http://127.0.0.1:54345"
headers = {'Content-Type': 'application/json'}
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



def save_to_csv(browser_id, csv_file='bitbrowser_accounts.csv'):
    """保存帳號信息到CSV"""
    # 檢查文件是否存在，如果不存在則創建並寫入標題
    file_exists = os.path.isfile(csv_file)
    
    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['browser_id', 'created_at'])
        
        # 寫入新的帳號信息
        writer.writerow([
            browser_id,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ])

def create_browser():
    """創建比特瀏覽器並等待手動登入"""
    # 生成隨機帳號密碼
    print(f"\n已生成比特瀏覽器id：")
    
    try:
        # 初始化比特瀏覽器
        # bit = BitBrowser('google')
        # driver, browser_id = bit.get_driver(
        #     username=username,
        #     password=password,
        #     proxyType='noproxy',
        #     proxyIp='',
        #     proxyPort='',
        #     proxyUsername='',
        #     proxyPassword='',
        #     dynamicIpUrl=''
        # )
        browser_id = createBrowser()
        print(f"\n已生成比特瀏覽器id：{browser_id}")
        res = openBrowser(browser_id)
        driverPath = res['data']['driver']
        debuggerAddress = res['data']['http']

        print(driverPath)
        print(debuggerAddress)

        # selenium 连接代码
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option("debuggerAddress", debuggerAddress)

        chrome_service = Service(driverPath)
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
        
        # 訪問網站
        print("\n正在打開網站...")
        driver.get('https://hailuoai.video/')
        
        # 等待手動操作
        print("\n請在瀏覽器中完成以下操作：")
        print("1. 手動登入網站")
        print("2. 完成其他必要設置")
        print("\n完成所有操作後，請按 Enter 鍵結束程序...")
        input()
        
        # 保存帳號信息
        save_to_csv(browser_id)
        print("\n帳號信息已保存！")
        print("程序將在 3 秒後關閉...")
        time.sleep(3)
        
    except Exception as e:
        print(f"\n發生錯誤: {str(e)}")
    finally:
        if 'bit' in locals() and 'browser_id' in locals():
            bit.close_browser(browser_id)

if __name__ == "__main__":
    create_browser() 