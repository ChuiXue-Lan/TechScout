"""推送模块 - 飞书/Telegram/Email"""

import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

import requests

from .fetcher import Article


class FeishuNotifier:
    """飞书 Webhook 推送"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, article: Article, summary: str) -> bool:
        """
        发送消息到飞书

        Args:
            article: 文章对象
            summary: 摘要文本

        Returns:
            是否发送成功
        """
        # 构建富文本消息（Smart Brevity 风格）
        content = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"📰 {article.feed_name}"
                    },
                    "template": "blue"
                },
                "elements": [
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": f"原标题: {article.title}"
                            }
                        ]
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "markdown",
                        "content": summary
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "action",
                        "actions": [
                            {
                                "tag": "button",
                                "text": {
                                    "tag": "plain_text",
                                    "content": "🔗 阅读原文"
                                },
                                "type": "primary",
                                "url": article.url
                            }
                        ]
                    }
                ]
            }
        }

        try:
            response = requests.post(
                self.webhook_url,
                json=content,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0 or result.get('StatusCode') == 0:
                    return True
                print(f"[飞书] 发送失败: {result}")
                return False
            else:
                print(f"[飞书] HTTP 错误: {response.status_code}")
                return False

        except Exception as e:
            print(f"[飞书] 发送异常: {e}")
            return False


class TelegramNotifier:
    """Telegram Bot 推送"""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_base = f"https://api.telegram.org/bot{bot_token}"

    def send(self, article: Article, summary: str) -> bool:
        """发送消息到 Telegram"""
        # 构建 Markdown 消息
        text = f"""📰 *{article.feed_name}*

*{self._escape_markdown(article.title)}*

{self._escape_markdown(summary)}

[🔗 阅读原文]({article.url})

_分类: {article.category}_"""

        try:
            response = requests.post(
                f"{self.api_base}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": False
                },
                timeout=10
            )

            if response.status_code == 200:
                return response.json().get('ok', False)
            else:
                print(f"[Telegram] HTTP 错误: {response.status_code}")
                return False

        except Exception as e:
            print(f"[Telegram] 发送异常: {e}")
            return False

    @staticmethod
    def _escape_markdown(text: str) -> str:
        """转义 Markdown 特殊字符"""
        chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in chars:
            text = text.replace(char, f'\\{char}')
        return text


class EmailNotifier:
    """Email SMTP 推送"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        to_address: str
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.to_address = to_address

    def send(self, article: Article, summary: str) -> bool:
        """发送邮件"""
        # 构建 HTML 邮件
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #f5f5f5; padding: 20px; border-radius: 8px;">
                <p style="color: #666; margin: 0;">📰 {article.feed_name}</p>
                <h2 style="margin: 10px 0;">{article.title}</h2>
                <p style="line-height: 1.6;">{summary}</p>
                <a href="{article.url}"
                   style="display: inline-block; background: #1a73e8; color: white;
                          padding: 10px 20px; text-decoration: none; border-radius: 4px;">
                    🔗 阅读原文
                </a>
                <p style="color: #999; font-size: 12px; margin-top: 20px;">
                    分类: {article.category}
                </p>
            </div>
        </body>
        </html>
        """

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"[RSS] {article.title}"
        msg['From'] = self.username
        msg['To'] = self.to_address

        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            return True

        except Exception as e:
            print(f"[Email] 发送失败: {e}")
            return False


class Notifier:
    """统一的通知管理器"""

    def __init__(self, config: dict):
        self.notifiers = []

        # 初始化飞书
        feishu_config = config.get('feishu', {})
        if feishu_config.get('enabled') and feishu_config.get('webhook_url'):
            self.notifiers.append(
                ('飞书', FeishuNotifier(feishu_config['webhook_url']))
            )

        # 初始化 Telegram
        tg_config = config.get('telegram', {})
        if tg_config.get('enabled') and tg_config.get('bot_token'):
            self.notifiers.append(
                ('Telegram', TelegramNotifier(
                    tg_config['bot_token'],
                    tg_config['chat_id']
                ))
            )

        # 初始化 Email
        email_config = config.get('email', {})
        if email_config.get('enabled') and email_config.get('username'):
            self.notifiers.append(
                ('Email', EmailNotifier(
                    email_config['smtp_host'],
                    email_config['smtp_port'],
                    email_config['username'],
                    email_config['password'],
                    email_config['to']
                ))
            )

    def notify(self, article: Article, summary: str) -> dict[str, bool]:
        """
        通过所有启用的渠道发送通知

        Returns:
            各渠道的发送结果
        """
        results = {}

        for name, notifier in self.notifiers:
            print(f"[推送] {name}: {article.title[:30]}...")
            results[name] = notifier.send(article, summary)

        return results

    @property
    def has_notifiers(self) -> bool:
        """是否有可用的通知渠道"""
        return len(self.notifiers) > 0
