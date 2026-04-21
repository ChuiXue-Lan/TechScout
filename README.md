# 前置准备
1. 创建多维表格：在飞书/飞书文档中新建一个多维表格（Bitable）
2. 建好列（列名与 `field_map` 一致，默认是中文）：

| 列名 | 类型 |
| --- | --- |
| 标题 | 文本 |
| 发布时间 | 日期 |
| 论文总结 | 文本（长文本） |
| 摘要原文 | 文本（长文本） |
| 链接 | 超链接 |
| 来源 | 文本 |
|  |  |


3. 取 `app_token` 和 `table_id`：打开多维表格，URL 格式为：`[https://xxx.feishu.cn/base/<app_token>?table=<table_id>](https://xxx.feishu.cn/base/<app_token>?table=<table_id>)`
4. 创建飞书自建应用，授权 `bitable:app` 读写权限和`wiki:wiki:readonly`权限，将应用添加为表格协作者，获取 `app_id` / `app_secret`，填入环境变量即可。
5. 添加机器人到多维表格
    1. 打开你的多维表格
    2. 右上角 「···」→「更多」→「添加文档应用」
    3. 搜索你创建的自建应用名称，点击添加


```bash
打开你的飞书多维表格，URL 长这样：(本项目配置了自动解析，即便是wiki链接也可以运行)

`[https://xxx.feishu.cn/base/bascnABCDEFGHIJ?table=tblXXXXXXXXXX&view=vewYYYYYYYY](https://xxx.feishu.cn/base/bascnABCDEFGHIJ?table=tblXXXXXXXXXX&view=vewYYYYYYYY)`

+ `bascnABCDEFGHIJ` → 这就是 `app_token`（`/base/` 后面到 `?` 之前）
+ `tblXXXXXXXXXX` → 这就是 `table_id`（`table=` 后面到 `&` 之前）
```

```bash
`app_id` 和 `app_secret` 怎么获得：

1. 打开[飞书开放平台](https://open.feishu.cn/app)，点「创建企业自建应用」
2. 进入应用后，「凭证与基础信息」页面就能看到 `App ID` 和 `App Secret`
3. 左侧「权限管理」→ 搜索并开通 `bitable:app`（多维表格读写权限）
4. 回到你的多维表格 → 右上角「...」→「更多」→「添加文档应用」→ 搜索你刚创建的应用名称并添加
```

# TechScout 配置说明

配置文件为 `config.yaml`，所有敏感信息（API Key、Token 等）通过环境变量注入，格式为 `${VAR_NAME}`。

---

## 环境变量设置

推荐使用 conda 环境变量统一管理：

```bash
conda env config vars set VAR_NAME="值" -n techscout
conda deactivate && conda activate techscout  # 重新激活后生效
```

---

## 一、feeds — RSS 订阅源

```yaml
feeds:
  - name: "Arxiv CS.AI"           # 来源名称，会写入表格的「来源」列
    url: "https://..."            # RSS 地址
    max_articles: 2               # 每次最多处理该来源的文章数
    keywords:                     # 关键词白名单（OR 逻辑，不区分大小写）
      - "agent"                   # 标题或正文包含任意一个词才处理
    exclude_keywords:             # 关键词黑名单（OR 逻辑，命中即丢弃）
      - "clinical"
```

---

## 二、llm — AI 摘要模型

```yaml
llm:
  provider: "minimax"             # 可选：claude / openai / minimax
  model: "MiniMax-M2.7"          # 对应 provider 的模型名称
  api_key: "${MINIMAX_API_KEY}"  # 当前 provider 的 API Key

  # 仅 provider 为 openai 时使用
  openai_api_key: "${OPENAI_API_KEY}"
  openai_model: "gpt-4o-mini"

  summary_prompt: |              # 自定义摘要 prompt，支持 {title} {content} 占位符
    ...
```

| 环境变量 | 说明 |
|---|---|
| `MINIMAX_API_KEY` | MiniMax API Key |
| `OPENAI_API_KEY` | OpenAI API Key（provider=openai 时使用） |

---

## 三、notify — 推送配置

```yaml
notify:
  notify_mode: "digest"          # 推送模式，见下方说明
```

**notify_mode 可选值：**

| 值 | 行为 |
|---|---|
| `full` | 每篇文章生成摘要后立即推送完整卡片到群聊 |
| `digest` | 所有文章处理完毕后，推送一条汇总消息「本次新增 N 篇」 |

---

### 3.1 飞书机器人 Webhook

```yaml
notify:
  feishu:
    enabled: true
    webhook_url: "${FEISHU_WEBHOOK}"
```

| 环境变量 | 说明 |
|---|---|
| `FEISHU_WEBHOOK` | 飞书群机器人的 Webhook 地址 |

获取方式：飞书群 → 设置 → 机器人 → 添加自定义机器人 → 复制 Webhook 地址。

---

### 3.2 飞书多维表格 Bitable

将摘要结果写入飞书多维表格，表格列结构需提前创建：

| 列名 | 类型 |
|---|---|
| 标题 | 文本 |
| 发布时间 | 日期 |
| 论文总结 | 文本（长文本）|
| 摘要原文 | 文本（长文本）|
| 链接 | 超链接 |
| 来源 | 文本 |

```yaml
notify:
  feishu_bitable:
    enabled: true
    table_url: "https://li.feishu.cn/wiki/xxx"  # 表格链接，digest 模式下附在汇总消息中
    app_id: "${FEISHU_APP_ID}"
    app_secret: "${FEISHU_APP_SECRET}"
    app_token: "${FEISHU_APP_TOKEN}"             # wiki node token 或 bitable app_token
    table_id: "${FEISHU_TABLE_ID}"
```

| 环境变量 | 说明 | 获取方式 |
|---|---|---|
| `FEISHU_APP_ID` | 飞书自建应用 App ID | 开放平台 → 应用 → 凭证与基础信息 |
| `FEISHU_APP_SECRET` | 飞书自建应用 App Secret | 同上 |
| `FEISHU_APP_TOKEN` | 多维表格标识 | URL 中 `/base/` 后的部分；若是 wiki 链接则填 `/wiki/` 后的 node token |
| `FEISHU_TABLE_ID` | 数据表 ID | URL 中 `?table=` 后的部分（`tbl` 开头）|

**自建应用需要开通的权限：**

| 权限 | 用途 |
|---|---|
| `bitable:app` | 读写多维表格 |
| `wiki:wiki:readonly` | 仅当 `app_token` 填写的是 wiki node token 时需要 |

**应用授权步骤：**
1. 开放平台 → 权限管理 → 开通上述权限
2. 版本管理与发布 → 创建版本 → 提交发布（企业应用需管理员审批）
3. 打开多维表格 → 右上角 `···` → 更多 → 添加文档应用 → 搜索应用名称并添加（权限选「可编辑」）

---

### 3.3 Telegram（可选）

```yaml
notify:
  telegram:
    enabled: false
    bot_token: "${TELEGRAM_BOT_TOKEN}"
    chat_id: "${TELEGRAM_CHAT_ID}"
```

---

### 3.4 Email（可选）

```yaml
notify:
  email:
    enabled: false
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
    username: "${EMAIL_USER}"
    password: "${EMAIL_PASS}"
    to: "you@example.com"
```

---

## 四、schedule — 运行配置

```yaml
schedule:
  interval_minutes: 5        # 定时任务间隔（分钟）
  max_articles_per_run: 10   # 每次运行全局最多处理文章数
  max_age_hours: 24          # 只处理最近 N 小时内发布的文章
```

---

## 五、运行方式

```bash
python main.py --once      # 执行一次
python main.py             # 启动定时任务（按 interval_minutes 循环）
python main.py --stats     # 查看数据库统计
python main.py --config my.yaml  # 使用自定义配置文件
```
