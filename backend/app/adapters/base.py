from abc import ABC, abstractmethod


class AIAdapter(ABC):
    @abstractmethod
    async def clean_text(self, text: str) -> str:
        """清洗：纠正错别字 + 删除 AI 来源标记（如"由豆包生成"）。
        Prompt 要求：只做纠错和删除 AI 标记，不改变原文意思和句式结构。
        """

    @abstractmethod
    async def extract_structure(self, text: str) -> dict[str, object]:
        """识别章节结构，返回标题树 JSON。
        输出格式见 backend/CLAUDE.md §M3 AI 结构识别输出 Schema。
        """
