"""SQLite 存储模块 - 用于去重"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional

from .fetcher import Article


class Storage:
    """SQLite 存储管理"""

    def __init__(self, db_path: str = "rss_reader.db"):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url_hash TEXT UNIQUE NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT,
                    feed_name TEXT,
                    summary TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_url_hash
                ON processed_articles(url_hash)
            """)
            conn.commit()

    def is_processed(self, article: Article) -> bool:
        """检查文章是否已处理过"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM processed_articles WHERE url_hash = ?",
                (article.url_hash,)
            )
            return cursor.fetchone() is not None

    def mark_processed(
        self,
        article: Article,
        summary: Optional[str] = None
    ):
        """标记文章为已处理"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO processed_articles
                (url_hash, url, title, feed_name, summary, processed_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                article.url_hash,
                article.url,
                article.title,
                article.feed_name,
                summary,
                datetime.now().isoformat()
            ))
            conn.commit()

    def filter_new_articles(self, articles: list[Article]) -> list[Article]:
        """过滤出未处理的新文章"""
        return [a for a in articles if not self.is_processed(a)]

    def get_recent_articles(self, limit: int = 50) -> list[dict]:
        """获取最近处理的文章"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT url_hash, url, title, feed_name, summary, processed_at
                FROM processed_articles
                ORDER BY processed_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> dict:
        """获取统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM processed_articles"
            )
            total = cursor.fetchone()[0]

            cursor = conn.execute("""
                SELECT feed_name, COUNT(*) as count
                FROM processed_articles
                GROUP BY feed_name
                ORDER BY count DESC
            """)
            by_feed = {row[0]: row[1] for row in cursor.fetchall()}

            return {
                'total_articles': total,
                'by_feed': by_feed
            }
