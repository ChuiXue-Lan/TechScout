# test_feishu.py
from datetime import datetime
from rss_reader.fetcher import Article
from rss_reader.feishu_exporter import FeishuExporter
import os
import sys
sys.path.insert(0, '.')

cfg = {
    "app_id":     os.environ["FEISHU_APP_ID"],
    "app_secret": os.environ["FEISHU_APP_SECRET"],
    "app_token":  os.environ["FEISHU_APP_TOKEN"],
    "table_id":   os.environ["FEISHU_TABLE_ID"],
}
e = FeishuExporter(cfg)
article = Article(
    title="测试标题", url="https://example.com",
    content="测试摘要原文", published=datetime.now(),
    feed_name="测试来源", category=""
)
n = e.export([(article, "测试论文总结")])
print(f"写入 {n} 条")
