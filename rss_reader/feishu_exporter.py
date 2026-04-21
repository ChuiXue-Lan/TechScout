"""飞书多维表格导出模块"""

import time
from typing import Optional
from datetime import datetime

import requests

from .fetcher import Article


class FeishuExporter:
    """将文章摘要批量写入飞书多维表格"""

    TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    WIKI_NODE_URL = "https://open.feishu.cn/open-apis/wiki/v2/spaces/get_node"
    BATCH_CREATE_URL = (
        "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}"
        "/tables/{table_id}/records/batch_create"
    )
    # tenant_access_token 有效期 2 小时，提前 5 分钟刷新
    TOKEN_TTL = 7200 - 300

    def __init__(self, config: dict):
        """
        config 字段：
          app_id       飞书应用 App ID
          app_secret   飞书应用 App Secret
          app_token    多维表格 App Token（URL 中的 base 部分）
          table_id     数据表 Table ID
          field_map    （可选）字段名映射，见下方默认值
        """
        self.app_id: str = config["app_id"]
        self.app_secret: str = config["app_secret"]
        # 支持 wiki node token（URL 里 /wiki/ 后面的部分）或直接填 bitable app_token
        self._raw_app_token: str = config["app_token"]
        self.app_token: Optional[str] = None  # 解析后的真实 bitable app_token
        self.table_id: str = config["table_id"]

        # 字段名映射：Python key -> 飞书多维表格列名
        default_field_map = {
            "title":     "标题",
            "published": "发布时间",
            "summary":   "论文总结",
            "content":   "摘要原文",
            "url":       "链接",
            "feed_name": "来源",
        }
        self.field_map: dict = {**default_field_map, **config.get("field_map", {})}

        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0

    # ------------------------------------------------------------------
    # Token 管理
    # ------------------------------------------------------------------

    def _fetch_token(self) -> str:
        """从飞书获取 tenant_access_token"""
        resp = requests.post(
            self.TOKEN_URL,
            json={"app_id": self.app_id, "app_secret": self.app_secret},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"获取 tenant_access_token 失败: {data}")
        return data["tenant_access_token"]

    def _get_token(self) -> str:
        """返回有效的 tenant_access_token，必要时自动刷新"""
        if self._token is None or time.time() >= self._token_expires_at:
            self._token = self._fetch_token()
            self._token_expires_at = time.time() + self.TOKEN_TTL
        return self._token

    def _resolve_app_token(self) -> str:
        """
        解析真实的 bitable app_token。
        若配置的是 wiki node token（以字母开头且不含 'Bas'），
        则调用 wiki API 获取对应的 obj_token。
        """
        if self.app_token:
            return self.app_token

        raw = self._raw_app_token
        # bitable app_token 通常以 Bas 开头；wiki node token 不带这个前缀
        if raw.startswith("Bas") or raw.startswith("bas"):
            self.app_token = raw
            return self.app_token

        # 当作 wiki node token 处理，调用接口获取真实 app_token
        print(f"[飞书] 检测到 wiki node token，正在解析真实 app_token...")
        token = self._get_token()
        resp = requests.get(
            self.WIKI_NODE_URL,
            headers={"Authorization": f"Bearer {token}"},
            params={"token": raw},
            timeout=10,
        )
        if not resp.ok:
            raise RuntimeError(f"wiki node 查询失败 {resp.status_code}: {resp.text}")
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"wiki node 查询失败: {data}")
        obj_token = data["data"]["node"]["obj_token"]
        print(f"[飞书] 解析到 bitable app_token: {obj_token}")
        self.app_token = obj_token
        return self.app_token

    # ------------------------------------------------------------------
    # 记录构建
    # ------------------------------------------------------------------

    def _build_record(self, article: Article, summary: Optional[str]) -> dict:
        """将 (Article, summary) 转换为飞书多维表格 record fields"""
        fm = self.field_map
        fields: dict = {}

        if fm.get("title"):
            fields[fm["title"]] = article.title

        if fm.get("published") and article.published:
            # 飞书日期字段使用毫秒时间戳
            fields[fm["published"]] = int(article.published.timestamp() * 1000)

        if fm.get("summary") and summary:
            fields[fm["summary"]] = summary

        if fm.get("content") and article.content:
            fields[fm["content"]] = article.content

        if fm.get("url"):
            fields[fm["url"]] = {"link": article.url, "text": article.url}

        if fm.get("feed_name"):
            fields[fm["feed_name"]] = article.feed_name

        return {"fields": fields}

    # ------------------------------------------------------------------
    # 导出接口
    # ------------------------------------------------------------------

    def export(
        self,
        results: list[tuple[Article, Optional[str]]],
        batch_size: int = 500,
    ) -> int:
        """
        批量写入多维表格。

        Args:
            results:    [(Article, summary), ...] 列表
            batch_size: 每批最多写入条数（飞书上限 500）

        Returns:
            成功写入的记录数
        """
        if not results:
            return 0

        records = [self._build_record(article, summary) for article, summary in results]
        url = self.BATCH_CREATE_URL.format(
            app_token=self._resolve_app_token(),
            table_id=self.table_id,
        )

        total_created = 0
        for i in range(0, len(records), batch_size):
            chunk = records[i : i + batch_size]
            token = self._get_token()
            resp = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={"records": chunk},
                timeout=30,
            )
            if not resp.ok:
                raise RuntimeError(f"batch_create HTTP {resp.status_code}: {resp.text}")
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != 0:
                raise RuntimeError(f"batch_create 失败 (batch {i // batch_size + 1}): {data}")

            created = len(data.get("data", {}).get("records", []))
            total_created += created
            print(
                f"[飞书] 已写入第 {i // batch_size + 1} 批，"
                f"本批 {created} 条，累计 {total_created} 条"
            )

        return total_created
