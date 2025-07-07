import smtplib
from email.mime.text import MIMEText
from email.header import Header
from dotenv import load_dotenv
import os

load_dotenv()

smtp_server = os.getenv("SMTP_SERVER")
smtp_port = int(os.getenv("SMTP_PORT"))
sender_email = os.getenv("SENDER_EMAIL")
sender_password = os.getenv("SENDER_PASSWORD")
receiver_email = os.getenv("RECEIVER_EMAIL")

def getMainData(params):
    # 将传入的 HTML 数据保存为 html_content
    html_content = params

    # 构造完整的邮件内容（包含 header 和 logo）
    full_html = f"""
        <div style="width:100%;">
            <div style="text-align:center; width:100%;">
                <img src="https://github.com/xieleihan/hangzhouEchoing_PushDailyTasks/blob/main/assets/images/logo.png?raw=true" alt="logo" style="max-width: 200px;" />
            </div>
            <hr style="border: 1px solid #ddd;" />
            {html_content}
        </div>
        """

    subject = 'ECHOING 每日推送报告'

    return {
        "subject": subject,
        "content": full_html
    }

def send_email(html_content):
    """
    发送 HTML 邮件
    """
    # 获取邮件主题和内容
    email_data = getMainData(html_content)

    # 构造邮件对象
    msg = MIMEText(email_data["content"], 'html', 'utf-8')
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = Header(email_data["subject"], 'utf-8')

    try:
        # 连接 SMTP 服务器（SSL 加密）
        print(f"Connecting to {smtp_server}:{smtp_port}")
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, [receiver_email], msg.as_string())
        print("✅ 邮件发送成功")
    except Exception as e:
        print("❌ 邮件发送失败:", str(e))