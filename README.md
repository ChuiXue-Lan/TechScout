# RSS AI Reader

一个轻量级的 RSS AI 阅读器，自动抓取订阅、生成摘要、推送到 IM。

## 功能特点

- 📡 自动抓取 RSS/Atom feeds
- 🤖 使用 LLM (Claude/OpenAI) 生成中文摘要
- 📬 多渠道推送：飞书、Telegram、Email
- 💾 SQLite 本地存储，自动去重
- ⏰ 支持定时任务

## 快速开始

### 1. 安装依赖

```bash
cd ~/projects/rss-reader
pip install -r requirements.txt
```

### 2. 配置

编辑 `config.yaml`：

```yaml
# 添加你的 RSS 订阅
feeds:
  - name: "Hacker News"
    url: "https://hnrss.org/frontpage"
    category: "tech"

# 配置 LLM
llm:
  provider: "claude"  # 或 "openai"
  model: "claude-sonnet-4-20250514"
  api_key: "${ANTHROPIC_API_KEY}"

# 配置推送渠道
notify:
  feishu:
    enabled: true
    webhook_url: "${FEISHU_WEBHOOK}"
```

### 3. 设置环境变量

```bash
export ANTHROPIC_API_KEY="your-api-key"
export FEISHU_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
```

### 4. 运行

```bash
# 单次执行
python main.py --once

# 启动定时任务（每小时执行一次）
python main.py

# 查看统计
python main.py --stats
```

## 配置说明

### LLM 配置

支持两种 LLM 提供商：

**Claude (推荐)**
```yaml
llm:
  provider: "claude"
  model: "claude-sonnet-4-20250514"
  api_key: "${ANTHROPIC_API_KEY}"
```

**OpenAI**
```yaml
llm:
  provider: "openai"
  openai_model: "gpt-4o-mini"
  openai_api_key: "${OPENAI_API_KEY}"
```

### 推送渠道

**飞书 Webhook**
1. 在飞书群中添加自定义机器人
2. 复制 Webhook 地址到配置

**Telegram**
1. 通过 @BotFather 创建 Bot
2. 获取 Bot Token 和 Chat ID

**Email**
```yaml
email:
  enabled: true
  smtp_host: "smtp.gmail.com"
  smtp_port: 587
  username: "your@gmail.com"
  password: "app-password"
  to: "receiver@example.com"
```

## 命令行参数

```
usage: main.py [-h] [--config CONFIG] [--once] [--stats] [--db DB]

options:
  -h, --help            显示帮助信息
  --config, -c CONFIG   配置文件路径 (默认: config.yaml)
  --once                只执行一次，不启动定时任务
  --stats               显示统计信息并退出
  --db DB               数据库文件路径 (默认: rss_reader.db)
```

## 项目结构

```
rss-reader/
├── config.yaml          # 配置文件
├── main.py              # 主入口
├── rss_reader/
│   ├── __init__.py
│   ├── fetcher.py       # RSS 抓取
│   ├── summarizer.py    # LLM 摘要
│   ├── notifier.py      # 推送通知
│   └── storage.py       # SQLite 存储
├── requirements.txt
└── README.md
```

## 飞书消息效果

```
📰 Hacker News

**Why SQLite is Taking Over**

📝 SQLite 正在从嵌入式数据库扩展到更多应用场景。
文章分析了其在边缘计算、移动应用中的优势...

[🔗 阅读原文]
```

## License

MIT
