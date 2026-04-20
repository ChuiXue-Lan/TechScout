"""RSS Feed 抓取模块"""

import feedparser
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from datetime import datetime


# HTTP 缓存文件路径
CACHE_FILE = Path("feed_cache.json")


@dataclass
class Article:
    """文章数据结构"""
    title: str
    url: str
    content: str
    published: Optional[datetime]
    feed_name: str
    category: str

    @property
    def url_hash(self) -> str:
        """生成 URL 的哈希值用于去重"""
        import hashlib
        return hashlib.sha256(self.url.encode()).hexdigest()[:16]


def load_cache() -> dict:
    """加载 HTTP 缓存（ETag/Last-Modified）"""
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_cache(cache: dict):
    """保存 HTTP 缓存"""
    CACHE_FILE.write_text(json.dumps(cache, indent=2))


def clean_html(raw_html: str) -> str:
    """清理 HTML 标签，保留纯文本"""
    # 移除 HTML 标签
    text = re.sub(r'<[^>]+>', '', raw_html)
    # 解码 HTML 实体
    text = html.unescape(text)
    # 清理多余空白
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_published_date(entry) -> Optional[datetime]:
    """解析发布日期"""
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6])
        except (TypeError, ValueError):
            pass
    if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
        try:
            return datetime(*entry.updated_parsed[:6])
        except (TypeError, ValueError):
            pass
    return None


def fetch_feed(feed_config: dict, cache: dict) -> list[Article]:
    """
    抓取单个 RSS feed（支持 HTTP 条件请求）

    Args:
        feed_config: 包含 name, url, category 的字典
        cache: HTTP 缓存字典（存储 etag/modified）

    Returns:
        文章列表
    """
    name = feed_config['name']
    url = feed_config['url']
    category = feed_config.get('category', 'general')

    articles = []

    # 获取缓存的 ETag 和 Last-Modified
    feed_cache = cache.get(url, {})
    etag = feed_cache.get('etag')
    modified = feed_cache.get('modified')

    try:
        # 使用条件请求，如果内容未变化服务器返回 304
        feed = feedparser.parse(url, etag=etag, modified=modified)

        # 304 Not Modified - feed 没有更新
        if hasattr(feed, 'status') and feed.status == 304:
            print(f"  [跳过] {name} 无更新 (304)")
            return articles

        # 更新缓存
        if hasattr(feed, 'etag') and feed.etag:
            feed_cache['etag'] = feed.etag
        if hasattr(feed, 'modified') and feed.modified:
            feed_cache['modified'] = feed.modified
        cache[url] = feed_cache

        if feed.bozo and not feed.entries:
            print(f"[警告] Feed 解析错误 ({name}): {feed.bozo_exception}")
            return articles

        for entry in feed.entries:
            # 提取标题
            title = entry.get('title', '无标题')

            # 提取链接
            link = entry.get('link', '')
            if not link:
                continue

            # 提取内容（优先级：content > summary > description）
            content = ''
            if hasattr(entry, 'content') and entry.content:
                content = entry.content[0].get('value', '')
            elif hasattr(entry, 'summary'):
                content = entry.summary
            elif hasattr(entry, 'description'):
                content = entry.description

            # 清理 HTML
            content = clean_html(content)

            # 限制内容长度（避免 LLM token 过多）
            if len(content) > 3000:
                content = content[:3000] + '...'

            article = Article(
                title=title,
                url=link,
                content=content,
                published=parse_published_date(entry),
                feed_name=name,
                category=category
            )
            articles.append(article)

    except Exception as e:
        print(f"[错误] 抓取 {name} 失败: {e}")

    return articles


def fetch_all_feeds(feeds_config: list[dict]) -> list[Article]:
    """
    抓取所有配置的 feeds（带 HTTP 缓存）

    Args:
        feeds_config: feed 配置列表

    Returns:
        所有文章的列表
    """
    all_articles = []
    # cache = load_cache()
    cache = {}

    for feed_config in feeds_config:
        print(f"[抓取] {feed_config['name']}...")
        articles = fetch_feed(feed_config, cache)
        all_articles.extend(articles)
        if articles:
            print(f"  -> 获取 {len(articles)} 篇文章")

    # 保存更新后的缓存
    save_cache(cache)

    return all_articles


def filter_by_age(articles: list[Article], max_age_hours: int) -> list[Article]:
    """
    过滤出指定时间内的文章

    Args:
        articles: 文章列表
        max_age_hours: 最大文章年龄（小时）

    Returns:
        过滤后的文章列表
    """
    from datetime import timedelta

    now = datetime.now()
    cutoff = now - timedelta(hours=max_age_hours)

    filtered = []
    for article in articles:
        # 如果没有发布时间，保守处理：包含它
        if article.published is None:
            filtered.append(article)
        elif article.published >= cutoff:
            filtered.append(article)

    return filtered
