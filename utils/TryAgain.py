import requests
import os
import sys
import json
import logging

from dotenv import load_dotenv
from datetime import datetime, date, timedelta
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

# 参数信息
login_url = os.getenv("LOGIN_URL")
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
login_type = int(os.getenv("LOGIN_TYPE", "2"))

# 模拟真实用户
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}

# 开启会话
session = requests.Session()
login_data = {
    "userName": username,
    "password": password,
    "loginType": login_type
}

# 发送请求
response = session.post(
    login_url,
    json=login_data,
    headers=headers,
    allow_redirects=True,
    verify=False  # 仅用于测试，生产环境建议使用真实证书
)

# 获取关键token
if response.status_code == 200:
    try:
        json_response = response.json()
        if json_response.get("success") is True:
            data = json_response.get("data", {})
            token = data.get("token") if isinstance(data, dict) else None

            if token:
                ACCESS_TOKEN = token
                print("🔑 成功获取 Token:", ACCESS_TOKEN)
            else:
                sys.exit(1)
        else:
            msg = json_response.get("msg", "未知错误")
            trace_id = json_response.get("traceId", "无追踪ID")
            sys.exit(1)

    except requests.exceptions.JSONDecodeError:
        sys.exit(1)
else:
    sys.exit(1)

# 获取header头
BASE_HEADERS = { 'Accept': 'application/json, text/plain, */*', 'Accept-Language': 'zh_CN', 'Cache-Control': 'no-cache',
                 'Content-Type': 'application/json', 'Origin': 'http://platform.localtest.echoing.cc:61002', 'Pragma': 'no-cache',
                 'Proxy-Connection': 'keep-alive', 'Referer': 'http://platform.localtest.echoing.cc:61002/cloudMachine/loggerList',
                 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
                 'accessToken': ACCESS_TOKEN }

# 定义接口
# http://platform.echoing.cc/api/v1/ctrlTaskMng/page
PLATFORM_BASE_API_ALL = 'http://platform.echoing.cc/api/v1/ctrlTaskMng/page'
PLATFORM_BASE_API_TRY_AGAIN = 'http://platform.echoing.cc/api/v1/ctrlTaskMng/taskRetry'
# Default time range (can be overridden if needed)
now = datetime.now()
print('当前时间:', now)

# 获取今天的 00:00:00
today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

# 昨天的 00:00:00
yesterday_midnight = today_midnight - timedelta(days=1)

# 设置任务时间范围
taskCreateStartTime = yesterday_midnight.strftime("%Y-%m-%d %H:%M:%S")
taskCreateEndTime = today_midnight.strftime("%Y-%m-%d %H:%M:%S")

# 传递的参数信息
def found(exceptionType):
    return {
    "pageNum": 1,
    "pageSize": 500,
    "taskStatus": 4, #任务状态
    "exceptionType": exceptionType, # 异常类型 3为控件找不到 1是未知 67是网络不通
    "creatTime": [
        taskCreateStartTime,
        taskCreateStartTime
    ],
    "taskCreateStartTime": taskCreateStartTime,
    "taskCreateEndTime": taskCreateEndTime
}

# 发起请求获取数据
session = requests.Session()
session.headers.update(BASE_HEADERS)

# 找不到控件的函数
def controlNotFoundFetchData(input_str: str = "") -> str:
    try:
        response = session.post(PLATFORM_BASE_API_ALL, json=found(3), timeout=10)
        if response.status_code == 200:
            data = response.json()

            # 确保路径存在且为列表
            if 'data' in data and isinstance(data['data'], dict):
                outer_data = data['data'].get('data', [])
                # print("提取的原始数据:", outer_data)

                if isinstance(outer_data, list):
                    task_ids = []

                    for item in outer_data:
                        if isinstance(item, dict) and 'detail' in item:
                            detail_dict = item['detail']

                            if isinstance(detail_dict, dict):
                                task_id = detail_dict.get('taskId')
                                if task_id is not None:
                                    task_ids.append(task_id)
                    print("提取的任务ID:", task_ids)
                    # return task_ids
                    TryAgain(task_ids)
                    return f"✅ 成功重试以下任务ID: {task_ids}"
                else:
                    print("data['data']['data'] 不是列表")
            else:
                print("没有找到有效的数据")

        else:
            print("请求失败，状态码:", response.status_code)

        return []  # 默认返回空列表

    except requests.RequestException as e:
        print("请求异常:", e)
        return []

# 未知的函数
def unknownFetchData():
    try:
        response = session.post(PLATFORM_BASE_API_ALL, json=found(1), timeout=10)
        if response.status_code == 200:
            data = response.json()

            # 确保路径存在且为列表
            if 'data' in data and isinstance(data['data'], dict):
                outer_data = data['data'].get('data', [])
                # print("提取的原始数据:", outer_data)

                if isinstance(outer_data, list):
                    task_ids = []

                    for item in outer_data:
                        if isinstance(item, dict) and 'detail' in item:
                            detail_dict = item['detail']

                            if isinstance(detail_dict, dict):
                                task_id = detail_dict.get('taskId')
                                if task_id is not None:
                                    task_ids.append(task_id)
                    print("提取的任务ID:", task_ids)
                    return task_ids

                else:
                    print("data['data']['data'] 不是列表")
            else:
                print("没有找到有效的数据")

        else:
            print("请求失败，状态码:", response.status_code)

        return []  # 默认返回空列表
    except requests.RequestException as e:
        print("请求异常:", e)
        return None

# 网络不通的函数
def networkNotFoundFetchData():
    try:
        response = session.post(PLATFORM_BASE_API_ALL, json=found(67), timeout=10)
        if response.status_code == 200:
            data = response.json()

            task_ids = []

            # 第一种情况：data.data.data 是列表
            if (
                'data' in data and
                isinstance(data['data'], dict) and
                'data' in data['data'] and
                isinstance(data['data']['data'], list)
            ):
                outer_data = data['data']['data']

                for item in outer_data:
                    if isinstance(item, dict):
                        task_id = item.get('taskId')
                        id = item.get('id')
                        if task_id is not None:
                            task_ids.append(task_id)
                        else:
                            task_ids.append(id)

                print("提取的任务ID:", task_ids)
                TryAgain(task_ids)
                return task_ids

            # 第二种情况：data 本身是一个包含 id 的字典
            elif 'id' in data:
                task_id = data.get('id')
                if task_id is not None:
                    task_ids.append(task_id)
                print("提取的任务ID:", task_ids)
                return task_ids

            else:
                print("没有找到有效的数据")
                return []

        else:
            print("请求失败，状态码:", response.status_code)
            return []

    except requests.RequestException as e:
        print("请求异常:", e)
        return []

def single_retry(taskId):
    try:
        logging.info(f"🔄 正在重试任务ID: {taskId}")
        response = session.post(
            PLATFORM_BASE_API_TRY_AGAIN,
            json=[taskId],
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success") is True:
                logging.info(f"✅ 任务 {taskId} 重试成功")
            else:
                logging.error(f"❌ 任务 {taskId} 重试失败: {data.get('msg', '未知错误')}")
        else:
            logging.error(f"❌ 请求失败（任务 {taskId}），状态码: {response.status_code}")

    except requests.RequestException as e:
        logging.error(f"❌ 请求异常（任务 {taskId}）: {e}")

def TryAgain(taskIds):
    if not isinstance(taskIds, list):
        logging.error("❌ 参数必须是一个列表")
        return

    logging.info(f"📦 即将重试 {len(taskIds)} 个任务")
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(single_retry, taskIds)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
