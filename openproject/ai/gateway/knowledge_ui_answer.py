"""Knowledge-grounded UI Answer Generator for QLDAPM Local Second Brain.
Enforces anti-hallucination verification, honest missing knowledge reporting, and native citations.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from .knowledge_retrieval import KnowledgeRetriever
from .decision_memory import DecisionMemory

@dataclass
class UIAnswerResult:
    query: str
    answer_text: str
    found: bool
    citations: List[str] = field(default_factory=list)

class KnowledgeAnswerGenerator:
    def __init__(
        self,
        retriever: KnowledgeRetriever,
        decision_memory: Optional[DecisionMemory] = None,
    ):
        self.retriever = retriever
        self.decision_memory = decision_memory

    def generate_answer(
        self,
        query: str,
        project_id: str,
        role: str,
    ) -> UIAnswerResult:
        ctx = self.retriever.retrieve_context(
            query=query,
            project_id=project_id,
            role=role,
            max_items=3,
        )

        if not ctx.results:
            msg = f"Thông tin về '{query}' hiện chưa có trong cơ sở tri thức nội bộ hoặc bạn không có quyền truy cập trong dự án {project_id}."
            return UIAnswerResult(
                query=query,
                answer_text=msg,
                found=False,
                citations=[],
            )

        citations: List[str] = []
        body_parts: List[str] = [
            f"Dưới đây là thông tin được xác thực từ cơ sở tri thức nội bộ dự án {project_id}:"
        ]

        for r in ctx.results:
            native_part = f"#{r.native_id}" if r.native_id else "N/A"
            lock_part = f"lockVersion={r.lock_version}" if r.lock_version else "lockVersion=N/A"
            cite_tag = f"[Doc: {r.source_id} {native_part} {lock_part}]"
            citations.append(cite_tag)

            body_parts.append(f"\n- **{r.title}** ({cite_tag}):\n  {r.snippet}")

        answer = "\n".join(body_parts)
        return UIAnswerResult(
            query=query,
            answer_text=answer,
            found=True,
            citations=citations,
        )
