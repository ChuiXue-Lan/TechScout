#!/usr/bin/env python3
"""删除 rss_reader.db 中最后 3 条记录（用于测试）"""

import sqlite3
import os
import sys

DB_PATH = "rss_reader.db"


def main():
    if not os.path.exists(DB_PATH):
        print(f"[错误] 数据库文件不存在: {DB_PATH}")
        return 1

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT id FROM processed_articles ORDER BY id DESC LIMIT 162")
    ids = [row[0] for row in cursor.fetchall()]

    if not ids:
        print("[info] 数据库为空，无记录可删")
        return 0

    print(f"将删除 id: {ids}")
    conn.execute("DELETE FROM processed_articles WHERE id IN ({})".format(','.join('?' * len(ids))), ids)
    conn.commit()
    print(f"已删除 {conn.total_changes} 条")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
