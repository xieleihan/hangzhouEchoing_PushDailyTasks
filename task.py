# -*- coding: utf-8 -*-
import requests
import json
import warnings
import argparse
# Removed matplotlib imports
from tabulate import tabulate
import sys
from collections import OrderedDict
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
import os
import markdown

load_dotenv()

from utils.MailConfig import send_email
# Suppress warnings
from urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter('ignore', InsecureRequestWarning)

# --- Configuration ---
# API_BASE_URL = 'http://platform.localtest.echoing.cc:61002/api/v1'
# ACCESS_TOKEN = 'd16c37694f6b4a65a597d6873181e7cd'
#
login_url = os.getenv("LOGIN_URL")

username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
login_type = int(os.getenv("LOGIN_TYPE", "2"))

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}

session = requests.Session()
    "userName": username,
login_data = {
    "password": password,
    "loginType": login_type
}

response = session.post(
    login_url,
    json=login_data,
    headers=headers,
    allow_redirects=True,
    verify=False  # 仅用于测试，生产环境建议使用真实证书
)

if response.status_code == 200:
    try:
        json_response = response.json()
        print("✅ 登录响应:", json_response)

        if json_response.get("success") is True:
            data = json_response.get("data", {})
            token = data.get("token") if isinstance(data, dict) else None

            if token:
                ACCESS_TOKEN = token
                print("🔑 成功获取 Token:", ACCESS_TOKEN)

            else:
                print("❌ 未找到 token 字段，请检查返回结构")
                sys.exit(1)

        else:
            msg = json_response.get("msg", "未知错误")
            trace_id = json_response.get("traceId", "无追踪ID")
            print(f"❌ 登录失败: {msg} (Trace ID: {trace_id})")
            sys.exit(1)

    except requests.exceptions.JSONDecodeError:
        print("⚠️ 响应不是有效的 JSON")
        print("原始响应内容:", response.text)
        sys.exit(1)
else:
    print(f"❌ 登录失败，状态码：{response.status_code}")
    print("响应内容:", response.text)
    sys.exit(1)

API_BASE_URL = os.getenv('API_BASE_URL')

TASK_API_URL = f'{API_BASE_URL}/ctrlTaskMng/page'
ENUM_API_URL = f'{API_BASE_URL}/dict/all'

# --- Enums will be fetched dynamically ---
PLATFORMS = None
EVENT_TYPES = None
EXCEPTION_TYPE_NAMES = None

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

# Shared Headers
BASE_HEADERS = { 'Accept': 'application/json, text/plain, */*', 'Accept-Language': 'zh_CN', 'Cache-Control': 'no-cache',
                 'Content-Type': 'application/json', 'Origin': 'http://platform.localtest.echoing.cc:61002', 'Pragma': 'no-cache',
                 'Proxy-Connection': 'keep-alive', 'Referer': 'http://platform.localtest.echoing.cc:61002/cloudMachine/loggerList',
                 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
                 'accessToken': ACCESS_TOKEN }

STATUS_SUCCESS = 3
STATUS_FAILURE = 4

# Removed CHINESE_FONT_OPTIONS

# --- Feishu Configuration ---
# !!! WARNING: Avoid hardcoding secrets. Use environment variables or config files. !!!
FEISHU_APP_ID = ""  # Replace with your Feishu App ID
FEISHU_APP_SECRET = "" # Replace with your Feishu App Secret
FEISHU_FOLDER_TOKEN = "" # Replace with your target Feishu folder token

# --- End Configuration ---


# --- Enum Fetching Function (Keep as is) ---
def fetch_enums_from_api():
    """Fetches Platform, EventType, and Exception enums from the API."""
    print(f"Attempting to fetch enums from: {ENUM_API_URL}")
    payload = {
        "langKey": "zh_CN",
        "dictKeys": ["ThirdPlatformEnum", "EventTypeEnum", "GroupCtrlClientReportTaskResultEnum"]
    }
    headers = BASE_HEADERS.copy()

    try:
        response = requests.post(ENUM_API_URL, headers=headers, json=payload, verify=False, timeout=15)
        response.raise_for_status()
        data = response.json()

        if not data.get("success") or data.get("code") != 200:
            print(f"[Error] API reported failure while fetching enums: Code={data.get('code')}, Msg={data.get('msg')}")
            return None, None, None

        enum_data = data.get("data", {})

        platforms_list = enum_data.get("ThirdPlatformEnum")
        if platforms_list is None: print("[Error] 'ThirdPlatformEnum' not found."); return None, None, None
        platforms_map = OrderedDict()
        for item in platforms_list:
            code = item.get("code"); desc = item.get("descZh", item.get("desc"))
            if code is not None and desc is not None: platforms_map[code] = desc

        event_types_list = enum_data.get("EventTypeEnum")
        if event_types_list is None: print("[Error] 'EventTypeEnum' not found."); return None, None, None
        event_types_map = {}
        for item in event_types_list:
            code = item.get("code"); desc = item.get("descZh", item.get("desc"))
            if code is not None and desc is not None: event_types_map[code] = desc

        exceptions_list = enum_data.get("GroupCtrlClientReportTaskResultEnum")
        if exceptions_list is None: print("[Error] 'GroupCtrlClientReportTaskResultEnum' not found."); return None, None, None
        exception_types_map = {}
        for item in exceptions_list:
            code = item.get("code"); desc = item.get("desc")
            if code is not None and desc is not None:
                try: exception_types_map[int(code)] = desc
                except (ValueError, TypeError): print(f"[Warning] Skipping invalid code in GroupCtrlClientReportTaskResultEnum: {code}")

        if 0 not in exception_types_map: exception_types_map[0] = "成功"
        else: exception_types_map[0] = "成功"; print("[Warning] Overwriting API definition for code 0 with '成功'.")

        print("Successfully fetched and processed enums.")
        return platforms_map, event_types_map, exception_types_map

    except requests.exceptions.Timeout: print(f"[Error] Timeout while connecting to enum API: {ENUM_API_URL}"); return None, None, None
    except requests.exceptions.RequestException as e: print(f"[Error] Network error while fetching enums: {e}"); return None, None, None
    except json.JSONDecodeError as e: print(f"[Error] Failed to decode JSON response from enum API: {e}\n    Response text: {response.text[:500]}..."); return None, None, None
    except Exception as e: print(f"[Error] An unexpected error occurred during enum processing: {e}"); return None, None, None


# --- Font Configuration Function (Removed) ---

# --- Feishu API Helper Functions (Keep as is) ---
def get_feishu_tenant_token(app_id, app_secret):
    """获取飞书 Tenant Access Token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    payload = json.dumps({"app_id": app_id, "app_secret": app_secret})
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("code") == 0:
            print("飞书 Token 获取成功。")
            return data.get("tenant_access_token")
        else:
            print(f"飞书 Token 获取失败: Code={data.get('code')}, Msg={data.get('msg')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"获取飞书 Token 时发生网络错误: {e}")
        return None
    except json.JSONDecodeError:
        print("解析飞书 Token 响应失败。")
        return None

def create_feishu_doc(token, folder_token, title):
    """在指定文件夹下创建新的飞书文档"""
    url = "https://open.feishu.cn/open-apis/docx/v1/documents"
    headers = { "Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8" }
    payload = json.dumps({"folder_token": folder_token, "title": title})
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data.get("code") == 0:
            doc_id = data.get("data", {}).get("document", {}).get("document_id")
            print(f"飞书文档创建成功: '{title}' (ID: {doc_id})")
            return doc_id
        else:
            print(f"飞书文档创建失败: Code={data.get('code')}, Msg={data.get('msg')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"创建飞书文档时发生网络错误: {e}")
        return None
    except json.JSONDecodeError:
        print("解析创建飞书文档响应失败。")
        return None

def append_text_block_to_feishu_doc(token, document_id, text_content):
    """向飞书文档追加一个文本块"""
    if not text_content: return False
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks?document_revision_id=-1"
    headers = { "Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8" }
    block_data = { "block_type": 2, "text": { "elements": [ {"text_run": {"content": text_content}} ] } }
    payload = json.dumps({"children": [block_data]})
    try:
        response = requests.patch(url, headers=headers, data=payload, timeout=30) # Slightly longer timeout for potentially large content
        response.raise_for_status()
        data = response.json()
        if data.get("code") == 0: return True
        else:
            print(f"追加内容到飞书文档失败: Code={data.get('code')}, Msg={data.get('msg')}")
            print(f"  Payload snippet: {payload[:200]}..."); return False
    except requests.exceptions.RequestException as e: print(f"追加内容到飞书文档时发生网络错误: {e}"); return False
    except json.JSONDecodeError: print("解析追加飞书文档响应失败。"); return False

# --- NEW: Dedicated Feishu Sending Function ---
def send_report_to_feishu(report_content, document_title):
    """Handles the entire process of sending the report content to a new Feishu doc."""
    print("初始化飞书发送流程...")
    if not all([FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_FOLDER_TOKEN]):
        print("[错误] 飞书配置不完整 (APP_ID, APP_SECRET, FOLDER_TOKEN)。请在脚本顶部设置它们。")
        return # Stop Feishu process if config is missing

    feishu_token = get_feishu_tenant_token(FEISHU_APP_ID, FEISHU_APP_SECRET)
    if not feishu_token:
        print("无法获取飞书 Token，发送失败。")
        return # Stop if token acquisition fails

    print(f"尝试创建飞书文档: '{document_title}'")
    new_doc_id = create_feishu_doc(feishu_token, FEISHU_FOLDER_TOKEN, document_title)

    if not new_doc_id:
        print("未能创建飞书文档，发送失败。")
        return # Stop if doc creation fails

    print(f"准备将报告内容发送到飞书文档 ID: {new_doc_id}...")

    # Simple length check (adjust limit as needed based on Feishu API constraints)
    if len(report_content) > 150000: # Example limit
        print("[警告] 报告内容可能过长，飞书追加可能失败或被截断。")

    # Append the content
    success = append_text_block_to_feishu_doc(feishu_token, new_doc_id, report_content)

    if success:
        print(f"报告已成功发送到飞书文档 '{document_title}' (ID: {new_doc_id})")
    else:
        # Error message printed within append_text_block_to_feishu_doc
        print(f"发送报告内容到飞书文档 '{document_title}' (ID: {new_doc_id}) 失败。")

# --- End Feishu Sending Function ---


# --- Analysis Functions (Keep as is, but plotting call removed) ---

def get_task_count(task_status, exception_type=None, platform_id=None, event_type=None):
    """查询任务计数 API"""
    payload = {"pageNum": 1, "pageSize": 1, "taskStatus": task_status,
                "taskCreateStartTime": taskCreateStartTime, "taskCreateEndTime": taskCreateEndTime }
    if platform_id is not None: payload["platform"] = platform_id
    if exception_type is not None: payload["exceptionType"] = exception_type
    if event_type is not None: payload["eventType"] = event_type

    desc_parts = [f"status={task_status}"]
    if platform_id is not None: desc_parts.append(f"platform={platform_id}")
    if exception_type is not None: desc_parts.append(f"exception={exception_type}")
    if event_type is not None: desc_parts.append(f"eventType={event_type}")
    request_desc = ", ".join(desc_parts)

    try:
        response = requests.post( TASK_API_URL, headers=BASE_HEADERS, json=payload, verify=False, timeout=45 )
        response.raise_for_status()
        data = response.json()
        if data.get("success") and data.get("code") == 200:
            total_count = data.get("data", {}).get("totalCount")
            return int(total_count) if total_count is not None else 0
        else: print(f"\n任务计数API错误: Code={data.get('code')}, Msg={data.get('msg')} (请求: {request_desc})"); return None
    except requests.exceptions.Timeout: print(f"\n任务计数HTTP超时 (请求: {request_desc})"); return None
    except requests.exceptions.RequestException as e: print(f"\n任务计数HTTP请求错误: {e} (请求: {request_desc})"); return None
    except (json.JSONDecodeError, ValueError) as e: print(f"\n任务计数响应解析错误: {e} (请求: {request_desc})"); return None

# --- Plotting Function (Removed) ---
# def plot_failure_distribution(...):

def analyze_task_rates(platform_id=None):
    """获取平台基础数据，计算比率，识别 Top 3 失败原因"""
    platform_name_scope = PLATFORMS.get(platform_id, f"ID {platform_id}") if platform_id is not None else "所有平台 (聚合)"
    print(f"\n  正在分析范围: {platform_name_scope}...")

    total_success = get_task_count(task_status=STATUS_SUCCESS, platform_id=platform_id)
    if total_success is None: return None
    total_failure = get_task_count(task_status=STATUS_FAILURE, platform_id=platform_id)
    if total_failure is None: return None

    total_tasks = total_success + total_failure
    if total_tasks == 0:
        print(f"    -> 未找到 {platform_name_scope} 的任务。")
        return { "platform_name": platform_name_scope, "total_tasks": 0, "total_success": 0, "total_failure": 0,
                 "success_rate": 0, "failure_rate": 0, "failure_details": {}, "sum_individual_failures": 0, "top_failures": ["无"] * 3 }

    overall_success_rate = (total_success / total_tasks) * 100
    overall_failure_rate = (total_failure / total_tasks) * 100
    failure_details = {}; sum_individual_failures = 0

    if total_failure > 0:
        print(f"    正在为 {platform_name_scope} 获取失败详情 (按异常类型)...")
        exception_codes_to_check = sorted([code for code in EXCEPTION_TYPE_NAMES if code != 0])
        if not exception_codes_to_check: print("      [警告] 未找到可检查的异常类型定义 (除了成功)。")
        for i, code in enumerate(exception_codes_to_check):
            name = EXCEPTION_TYPE_NAMES.get(code, f"未知代码 {code}")
            progress = f"[{i+1}/{len(exception_codes_to_check)}]"
            print(f"\r      {progress} 检查异常类型 {code} ({name})...", end='', flush=True)
            count = get_task_count(task_status=STATUS_FAILURE, exception_type=code, platform_id=platform_id)
            if count is None: print(f"\r      {progress} [!] 获取异常类型 {code} 失败。跳过。 {' '*20}"); continue
            if count > 0:
                 sum_individual_failures += count; rate_within_failures = (count / total_failure) * 100
                 rate_overall = (count / total_tasks) * 100
                 failure_details[code] = { "name": name, "count": count, "rate_within_failures": rate_within_failures, "rate_overall": rate_overall }
        print(f"\r{' ' * 80}\r      完成获取失败详情。")

    top_failures_formatted = ["无"] * 3
    if failure_details:
        sorted_failures_list = sorted( failure_details.items(), key=lambda item: item[1]['count'], reverse=True )
        for i in range(min(3, len(sorted_failures_list))):
            code, details = sorted_failures_list[i]
            top_failures_formatted[i] = ( f"{details['name']} ({code}): {details['count']} ({details['rate_within_failures']:.1f}%)" )

    print(f"    -> {platform_name_scope} 基础分析完成。")
    return { "platform_name": platform_name_scope, "total_tasks": total_tasks, "total_success": total_success,
             "total_failure": total_failure, "success_rate": overall_success_rate, "failure_rate": overall_failure_rate,
             "failure_details": failure_details, "sum_individual_failures": sum_individual_failures, "top_failures": top_failures_formatted }


def analyze_event_type_rates_for_platform(platform_id):
    """获取指定平台每个事件类型的数据并计算成功/失败率"""
    platform_name = PLATFORMS.get(platform_id, f"ID {platform_id}")
    print(f"    正在为平台 '{platform_name}' (ID: {platform_id}) 分析事件类型统计...")
    results_by_event = []
    event_type_codes = sorted(EVENT_TYPES.keys())

    if not event_type_codes: print("      [警告] 未找到可分析的事件类型定义。"); return []

    for i, code in enumerate(event_type_codes):
        event_name = EVENT_TYPES.get(code, f"未知代码 {code}")
        progress = f"[{i+1}/{len(event_type_codes)}]"
        print(f"\r      {progress} 分析事件类型 {code} ({event_name})...", end='', flush=True)

        success_count = get_task_count(task_status=STATUS_SUCCESS, event_type=code, platform_id=platform_id)
        failure_count = get_task_count(task_status=STATUS_FAILURE, event_type=code, platform_id=platform_id)

        if success_count is None or failure_count is None:
            print(f"\r      {progress} [!] 获取平台 {platform_id} 事件类型 {code} 数据时出错。标记为错误。{' '*10}")
            results_by_event.append([code, event_name, "错误", "错误", "错误", "N/A", "N/A"])
            continue

        total_tasks = success_count + failure_count
        success_rate_str, failure_rate_str = "N/A", "N/A"
        if total_tasks > 0:
            success_rate = (success_count / total_tasks) * 100; failure_rate = (failure_count / total_tasks) * 100
            success_rate_str = f"{success_rate:.2f}%"; failure_rate_str = f"{failure_rate:.2f}%"
        elif total_tasks == 0: success_rate_str = "0.00%"; failure_rate_str = "0.00%"

        results_by_event.append([ code, event_name, total_tasks, success_count, failure_count, success_rate_str, failure_rate_str ])

    print(f"\r{' ' * 80}\r      完成平台 '{platform_name}' (ID: {platform_id}) 的事件类型分析。")
    return results_by_event

# --- Reporting Functions (Keep as is) ---

def format_detailed_report_markdown(results, platform_name_override=None):
    """将平台基础分析结果格式化为 Markdown 字符串"""
    platform_name = platform_name_override if platform_name_override else results.get("platform_name", "未知范围")
    report_parts = [f"## 详细结果: {platform_name}", f"\n**分析日期范围:** {taskCreateStartTime} 至 {taskCreateEndTime}"]

    if results is None: report_parts.append("\n```\n未能完成此平台的基础分析。\n```"); return "\n".join(report_parts)

    basic_stats = [f"查询任务总数: {results['total_tasks']}", f"  - 成功总数: {results['total_success']}", f"  - 失败总数: {results['total_failure']}"]
    if results['total_tasks'] > 0: basic_stats.extend(["-" * 30, f"总体成功率: {results['success_rate']:.2f}%", f"总体失败率: {results['failure_rate']:.2f}%"])
    else: basic_stats.append("\n未找到任务，比率不适用。")
    report_parts.append("\n```\n" + "\n".join(basic_stats) + "\n```")

    report_parts.append("\n### 按异常类型分析失败原因:")
    failure_details = results.get("failure_details", {})
    total_failure = results['total_failure']

    if total_failure > 0 and failure_details:
        headers = ["代码", "异常名称", "数量", "占失败比例", "占总任务比例"]
        table_data = []
        sorted_failures = sorted(failure_details.items(), key=lambda item: item[1]['count'], reverse=True)
        for code, details in sorted_failures:
            exc_name = EXCEPTION_TYPE_NAMES.get(code, f"未知代码 {code}")
            table_data.append([ code, exc_name, details['count'], f"{details.get('rate_within_failures', 0):.2f}%", f"{details.get('rate_overall', 0):.2f}%" ])
        markdown_table = tabulate(table_data, headers=headers, tablefmt="github", stralign="left", numalign="right")
        report_parts.append("\n" + markdown_table)

        sum_individual = results.get('sum_individual_failures', 0)
        if sum_individual != total_failure:
             mismatch = total_failure - sum_individual
             report_parts.append(f"\n> [!警告] 异常计数不匹配: 各类型总和={sum_individual}, API报告失败总数={total_failure} (差异={mismatch})")
             if mismatch > 0: report_parts.append(f">  -> 可能有 {mismatch} 个失败具有未知/未列出的异常类型代码。")
    elif total_failure > 0: report_parts.append("\n失败总数 > 0，但未找到具有已知异常类型代码的具体失败记录。")
    else: report_parts.append("\n此平台在此期间无失败记录。")

    return "\n".join(report_parts)


# def format_event_type_report_markdown(event_type_results, add_main_header=False, header_level=3):
#     """将事件类型分析结果格式化为 Markdown 字符串表格"""
#     report_parts = []
#     header_prefix = "#" * header_level
#     if add_main_header: report_parts.append(f"{header_prefix} 按事件类型统计成功/失败率")
#
#     if not event_type_results: report_parts.append("\n未能生成事件类型统计数据。"); return "\n".join(report_parts)
#
#     headers = ["事件代码", "事件描述", "总任务数", "成功数", "失败数", "成功率", "失败率"]
#     valid_data = [row for row in event_type_results if "错误" not in row]
#     error_data = [row for row in event_type_results if "错误" in row]
#
#     if valid_data:
#         markdown_table = tabulate(valid_data, headers=headers, tablefmt="github", stralign="left", numalign="right")
#         report_parts.append("\n" + markdown_table)
#     else: report_parts.append("\n无有效的事件类型数据可供展示。")
#
#     if error_data:
#         report_parts.append("\n\n**以下事件类型未能成功获取数据:**")
#         error_headers = ["事件代码", "事件描述"]
#         error_table_data = [[row[0], row[1]] for row in error_data]
#         error_table = tabulate(error_table_data, headers=error_headers, tablefmt="github")
#         report_parts.append("\n" + error_table)
#
#     return "\n".join(report_parts)

def format_event_type_report_markdown(event_type_results, add_main_header=False, header_level=3):
    """将事件类型分析结果格式化为 Markdown 字符串表格, 并按指定顺序排序"""
    report_parts = []
    header_prefix = "#" * header_level
    if add_main_header:
        report_parts.append(f"{header_prefix} 按事件类型统计成功/失败率")

    if not event_type_results:
        report_parts.append("\n未能生成事件类型统计数据。")
        return "\n".join(report_parts)

    headers = ["事件代码", "事件描述", "总任务数", "成功数", "失败数", "成功率", "失败率"]
    valid_data = [row for row in event_type_results if "错误" not in row]
    error_data = [row for row in event_type_results if "错误" in row]

    if valid_data:
        # --- Custom Sorting Logic ---
        # Define the desired order for specific event types
        priority_order = ["发帖", "主动评论", "主动点赞", "主动关注"]

        # Create a sort key function
        def get_sort_key(row):
            event_name = row[1] # Event description is at index 1
            if event_name in priority_order:
                # Assign a low number (its index in the priority list) for priority items
                return (priority_order.index(event_name), event_name)
            else:
                # Assign a high number for non-priority items, then sort alphabetically
                return (len(priority_order), event_name)

        # Sort the valid data using the custom key
        sorted_valid_data = sorted(valid_data, key=get_sort_key)
        # --- End Custom Sorting Logic ---

        # Use the sorted data to create the table
        markdown_table = tabulate(sorted_valid_data, headers=headers, tablefmt="github", stralign="left", numalign="right")
        report_parts.append("\n" + markdown_table)
    else:
        report_parts.append("\n无有效的事件类型数据可供展示。")

    if error_data:
        report_parts.append("\n\n**以下事件类型未能成功获取数据:**")
        error_headers = ["事件代码", "事件描述"]
        # Sort error data by code for consistency, although order might not matter as much here
        error_table_data = sorted([[row[0], row[1]] for row in error_data], key=lambda x: x[0])
        error_table = tabulate(error_table_data, headers=error_headers, tablefmt="github")
        report_parts.append("\n" + error_table)

    return "\n".join(report_parts)

# --- 主执行块 ---
if __name__ == "__main__":

    # Step 1: Fetch Enums
    PLATFORMS, EVENT_TYPES, EXCEPTION_TYPE_NAMES = fetch_enums_from_api()
    if PLATFORMS is None or EVENT_TYPES is None or EXCEPTION_TYPE_NAMES is None:
        print("[致命错误] 无法从 API 获取必要的枚举定义。脚本无法继续执行。")
        sys.exit(1)

    # Step 2: Define Argument Parser
    parser = argparse.ArgumentParser(
        description='分析任务成功/失败率，可按平台/事件类型统计，可选输出到飞书。枚举从 API 动态获取。' # Removed plotting mention
    )
    platform_help_text = f'指定平台 ID ({", ".join(f"{k}={v}" for k, v in PLATFORMS.items() if k != -1)})。省略则分析所有。'
    parser.add_argument( '--platform', type=int, required=False, help=platform_help_text )
    # Removed --plot argument
    parser.add_argument( '--feishu', action='store_true', help='将报告发送到配置的飞书文档文件夹。' )

    # Step 3: Parse Arguments
    args = parser.parse_args()
    platform_to_analyze = args.platform
    # Removed generate_plot_flag
    send_to_feishu_flag = args.feishu

    # Prepare Report Storage
    console_outputs = []
    feishu_markdown_parts = []
    report_title_base = "任务分析报告"
    report_date_str = date.today().strftime("%Y-%m-%d")
    report_title = "" # Will be set based on scope

    # --- Main Logic ---
    if platform_to_analyze is not None:
        # --- Analyze a SINGLE Specific Platform ---
        if platform_to_analyze not in PLATFORMS:
            if platform_to_analyze == -1 and -1 in PLATFORMS: platform_name = PLATFORMS[platform_to_analyze]
            else: print(f"[错误] 无效平台ID: {platform_to_analyze}。有效: {list(k for k in PLATFORMS.keys() if k != -1)}"); sys.exit(1)
        else: platform_name = PLATFORMS[platform_to_analyze]

        report_title = f"{report_title_base} - {platform_name} - {report_date_str}"
        console_outputs.append(f"# {report_title}"); feishu_markdown_parts.append(f"# {report_title}")

        results = analyze_task_rates(platform_id=platform_to_analyze)
        if results:
            platform_report_md = format_detailed_report_markdown(results)
            console_outputs.append(platform_report_md); feishu_markdown_parts.append(platform_report_md)

            event_type_results = analyze_event_type_rates_for_platform(platform_id=platform_to_analyze)
            if event_type_results:
                event_type_table_md = format_event_type_report_markdown(event_type_results, add_main_header=True, header_level=3)
                console_outputs.append("\n" + event_type_table_md); feishu_markdown_parts.append("\n" + event_type_table_md)
            else: msg = f"\n### 未能完成平台 {platform_name} 的事件类型分析。"; console_outputs.append(msg); feishu_markdown_parts.append(msg)

            # Removed plotting call
        else: msg = f"\n## 未能完成平台 {platform_name} (ID: {platform_to_analyze}) 的基础分析。"; console_outputs.append(msg); feishu_markdown_parts.append(msg)

    else:
        # --- Analyze ALL Platforms (Aggregate + Individual) ---
        report_title = f"{report_title_base} - 所有平台 - {report_date_str}"
        console_outputs.append(f"# {report_title}"); feishu_markdown_parts.append(f"# {report_title}")

        # 1. Aggregate Analysis
        console_outputs.append("## 聚合分析 (所有平台)"); feishu_markdown_parts.append("## 聚合分析 (所有平台)")
        aggregate_results = analyze_task_rates(platform_id=None)
        if aggregate_results:
            agg_report_md = format_detailed_report_markdown(aggregate_results, platform_name_override="所有平台 (聚合)")
            console_outputs.append(agg_report_md); feishu_markdown_parts.append(agg_report_md)
            # Removed plotting call
        else: msg = "\n### 未能完成所有平台的聚合分析。"; console_outputs.append(msg); feishu_markdown_parts.append(msg)

        console_outputs.append("\n---\n\n# 各独立平台分析与详情\n"); feishu_markdown_parts.append("\n---\n\n# 各独立平台分析与详情\n")
        platform_summary_data = []
        summary_headers = ["平台", "总任务数", "成功数", "失败数", "成功率", "失败率", "Top 1 失败(异常)", "Top 2 失败(异常)", "Top 3 失败(异常)"]
        platform_ids_to_analyze = [pid for pid in PLATFORMS.keys() if pid != -1]

        # 2. Individual Platform Analysis Loop
        for i, pid in enumerate(platform_ids_to_analyze):
            pname = PLATFORMS.get(pid, f"ID {pid}")
            section_header = f"\n## 平台: {pname} (ID: {pid})\n"
            console_outputs.append("\n" + "="*40 + section_header + "="*40); feishu_markdown_parts.append(section_header)

            individual_results = analyze_task_rates(platform_id=pid)
            if individual_results:
                ind_report_md = format_detailed_report_markdown(individual_results, platform_name_override=pname)
                console_outputs.append(ind_report_md.split('\n', 1)[1]); feishu_markdown_parts.append(ind_report_md.split('\n', 1)[1])

                top_failures = individual_results.get("top_failures", ["无"] * 3)
                platform_summary_data.append([ pname, individual_results['total_tasks'], individual_results['total_success'], individual_results['total_failure'], f"{individual_results['success_rate']:.2f}%", f"{individual_results['failure_rate']:.2f}%", top_failures[0], top_failures[1], top_failures[2] ])

                event_type_results = analyze_event_type_rates_for_platform(platform_id=pid)
                if event_type_results:
                    event_type_table_md = format_event_type_report_markdown(event_type_results, add_main_header=True, header_level=3)
                    console_outputs.append("\n" + event_type_table_md); feishu_markdown_parts.append("\n" + event_type_table_md)
                else: msg = f"\n### 未能完成平台 {pname} 的事件类型分析。"; console_outputs.append(msg); feishu_markdown_parts.append(msg)

                # Removed plotting call
            else:
                msg = f"\n### 未能完成平台 {pname} (ID: {pid}) 的基础分析。"; console_outputs.append(msg); feishu_markdown_parts.append(msg)
                platform_summary_data.append([pname, "错误", "错误", "错误", "错误", "错误", "N/A", "N/A", "N/A"])

            if i < len(platform_ids_to_analyze) - 1: hr = "\n---\n"; console_outputs.append(hr); feishu_markdown_parts.append(hr)

        # 3. Summary Table
        console_outputs.append("\n---\n\n## 各独立平台汇总表\n"); feishu_markdown_parts.append("\n---\n\n## 各独立平台汇总表\n")
        if platform_summary_data:
             summary_title = f"\n**汇总日期范围:** {taskCreateStartTime} 至 {taskCreateEndTime}\n"
             console_outputs.append(summary_title); feishu_markdown_parts.append(summary_title)
             summary_table_md = tabulate(platform_summary_data, headers=summary_headers, tablefmt="github", stralign="left", numalign="right")
             console_outputs.append(summary_table_md); feishu_markdown_parts.append(summary_table_md)
        else: no_summary_msg = "无法生成各独立平台的汇总数据。"; console_outputs.append(no_summary_msg); feishu_markdown_parts.append(no_summary_msg)

    # --- Final Output ---
    print("\n\n" + "="*60 + "\n--- 完整报告开始 (控制台输出) ---" + "\n" + "="*60)
    print('\n'.join(console_outputs))
    print("\n" + "="*60 + "\n--- 完整报告结束 (控制台输出) ---" + "\n" + "="*60)

    # 合并所有部分为一个字符串
    full_markdown_content = "\n".join(feishu_markdown_parts)

    html_content = markdown.markdown(full_markdown_content,extensions=['tables', 'fenced_code'])

    send_email(html_content)

    # 定义输出文件路径（当前目录下的 output_summary.md）
    output_file_path = "README.md"

    # 写入文件
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(full_markdown_content)

    print(f"✅ Markdown 文件已保存至: {output_file_path}")

    # --- Call Feishu Sending Function (Refactored) ---
    if send_to_feishu_flag:
        print("\n" + "="*60 + "\n--- 发送到飞书 ---" + "\n" + "="*60)
        final_feishu_content = "\n\n".join(feishu_markdown_parts) # Join parts for Feishu content
        # 'report_title' was set earlier based on analysis scope
        send_report_to_feishu(final_feishu_content, report_title)
        print("="*60 + "\n--- 飞书发送结束 ---" + "\n" + "="*60)

    # --- Script End ---
    print("\n脚本执行完毕。")
