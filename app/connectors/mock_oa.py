"""Connector: a mock OA / ticket system with built-in sample data.

Stands in for OA/HR/CRM/ERP exports so the demo runs with zero setup. The data
intentionally contains both wins and problems so retrospectives are non-trivial.
Replace `_SAMPLE` with a real API call to adapt this to a production system.
"""
from __future__ import annotations

from app.config import Settings
from app.connectors.base import Connector
from app.schemas import Document

_SAMPLE = {
    "2026-W41": [
        ("oa:daily", "本周 OA 日报汇总", (
            "完成 Agent 平台 v0.3 知识库检索接口联调\n"
            "上线 企业微信 审批流 Agent，覆盖请假/报销两类单据\n"
            "交付 BI 周报自动生成脚本给财务\n"
            "ERP 对接联调延期：对方测试环境本周三故障，阻塞 2 天\n"
            "RAG 召回在长文档上出现 bug：切块超长导致部分命中丢失"
        )),
        ("ticket:INC-1182", "工单 INC-1182 推理服务超时", (
            "现象：高峰期 chat 接口 P99 timeout 偶发\n"
            "影响：审批 Agent 回复失败率升高\n"
            "定位中：疑似 Redis 连接池耗尽 + 下游模型排队"
        )),
        ("ticket:REQ-337", "需求 REQ-337 新增 CRM 连接器", (
            "业务方希望把客户跟进记录纳入复盘\n"
            "完成 接口字段梳理，待排期开发"
        )),
    ],
}


class MockOAConnector(Connector):
    name = "mock_oa"

    def __init__(self, settings: Settings) -> None:
        self._data = _SAMPLE

    def fetch(self, period: str | None = None) -> list[Document]:
        periods = [period] if period and period in self._data else list(self._data)
        docs: list[Document] = []
        for per in periods:
            for doc_id, title, content in self._data.get(per, []):
                docs.append(Document(
                    id=doc_id, source=self.name, title=title,
                    content=content, timestamp=per, meta={"period": per},
                ))
        return docs
