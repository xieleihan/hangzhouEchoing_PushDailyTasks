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

subject = 'ECHOING 每日推送报告'
content = '''
<div style="width:100%;">
    <div style="width:100%;">
        <img src="https://example.com/assets/images/logo.png " alt="logo" />
    </div>
</div>
'''

msg = MIMEText(content, 'html', 'utf-8')
msg['From'] = sender_email
msg['To'] = receiver_email
msg['Subject'] = Header(subject, 'utf-8')

try:
    # 连接 SMTP 服务器（SSL 加密）
    with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, [receiver_email], msg.as_string())
    print("✅ 邮件发送成功")
except Exception as e:
    print("❌ 邮件发送失败:", str(e))