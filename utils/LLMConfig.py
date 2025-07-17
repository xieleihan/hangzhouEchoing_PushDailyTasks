import os

from openai import OpenAI
from dotenv import load_dotenv
from utils.TryAgain import controlNotFoundFetchData,networkNotFoundFetchData
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.tools import Tool

load_dotenv()

# 工具函数
tools = [
    Tool(
        name="controlNotFoundFetchData",
        func=controlNotFoundFetchData,
        description="尝试重试控件找不到的任务"
    ),
    Tool(
        name="networkNotFoundFetchData",
        func=networkNotFoundFetchData,
        description="尝试重试网络不通的任务"
    )
]

# 初始化 LLM
llm = ChatOpenAI(
    api_key= os.getenv('OPENAI_API_KEY'),
    base_url = os.getenv('OPENAI_API_BASE_URL'),
    model="deepseek-chat",
    temperature=0,
)

# 开启记忆
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, output_key="output")

# client = OpenAI(
#     api_key= os.getenv('OPENAI_API_KEY'),
#     base_url = os.getenv('OPENAI_API_BASE_URL')
# )

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

请以中文并且以如下格式输出完整回答：

### 数据分析结论
- 平台 A: 主要失败原因 + 是否需关注
- 平台 B: ...

回答后,如果发现高频失败项目是控件找不到,请主动调用 controlNotFoundFetchData 工具来重试下控件找不到的任务;如果发现高频失败项目是网络不通,请主动调用 networkNotFoundFetchData 工具来重试下网络不通的任务。
只能在最高高频失败的时候调用其中一个工具，不能同时调用所有工具。
'''

# def getLLMRespoense(content):
#     response = client.chat.completions.create(
#         model="deepseek-chat",
#         messages=[
#             {"role": "system", "content": f"{prompt}"},
#             {"role": "user", "content": f"{content}"},
#         ],
#         stream=False
#     )
#     return response.choices[0].message.content

def getLLMRespoense(content):
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        memory=memory,
        verbose=True,
        agent_kwargs = {
            "system_message": prompt
        }
    )

    response = agent.run(content)
    return response