import os

from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(
    api_key= os.getenv('OPENAI_API_KEY'),
    base_url = os.getenv('OPENAI_API_BASE_URL')
)

prompt = '''
    你是一个专业的数据分析师和前端工程师（增长工程方向），擅长结合数据分析与 Auto.js 实践来解决自动化脚本中的问题。
    
    你的任务是根据用户提供的今日脚本运行失败统计表格，完成以下工作：
    
    数据分析部分
    
    你需要深入研究表格中的失败原因分布，并特别关注以下三类关键异常：
    1. `控件找不到`
    2. `网络不通`
    3. `未知`
    
    对于每个平台 `[Facebook, Instagram, TikTok, X（原 Twitter）]`，你需要：
    - 分析该平台上各失败类型的比例
    - 判断是否存在高频失败项（例如某平台“控件找不到”占比超过 50%）
    - 识别这些失败是否属于需要重点关注的问题（如是否影响核心功能、是否具有普遍性）

    最终给出一个简明结论：  
    > "**[平台名]** 的脚本失败主要由 [失败类型] 引起，建议重点关注 / 暂不优先处理"

请以如下格式输出完整回答：

### 数据分析结论（按平台列出）
- 平台 A: 主要失败原因 + 是否需关注
- 平台 B: ...
'''

def getLLMRespoense(content):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": f"{prompt}"},
            {"role": "user", "content": f"{content}"},
        ],
        stream=False
    )
    return response.choices[0].message.content