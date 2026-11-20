"""Context Retrieval Engine for QLDAPM Local Second Brain.
Enforces fail-closed ACL verification and builds cited prompt context for LLM agents.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from .knowledge_search import KnowledgeSearchEngine, SearchResult

@dataclass
class RetrievedContext:
    query: str
    project_id: str
    role: str
    results: List[SearchResult] = field(default_factory=list)
    formatted_prompt_context: str = ""

class KnowledgeRetriever:
    def __init__(self, search_engine: KnowledgeSearchEngine):
        self.search_engine = search_engine

    def retrieve_context(
        self,
        query: str,
        project_id: str,
        role: str,
        max_items: int = 5,
    ) -> RetrievedContext:
        results = self.search_engine.search(
            query=query,
            project_id=project_id,
            role=role,
            limit=max_items,
        )

        if not results:
            return RetrievedContext(
                query=query,
                project_id=project_id,
                role=role,
                results=[],
                formatted_prompt_context="",
            )

        context_lines = [
            "### Relevant Internal Knowledge Context (Citations Required)",
            "The following verified internal documents were retrieved based on your role authorization:",
        ]

        for r in results:
            native_ref = f"#{r.native_id}" if r.native_id else "N/A"
            lock_ref = f"lockVersion={r.lock_version}" if r.lock_version else "lockVersion=N/A"
            citation = f"[Doc: {r.source_id} {native_ref} {lock_ref}]"
            context_lines.append(f"\n- **{r.title}** ({citation})")
            context_lines.append(f"  {r.snippet}")

        formatted = "\n".join(context_lines)
        return RetrievedContext(
            query=query,
            project_id=project_id,
            role=role,
            results=results,
            formatted_prompt_context=formatted,
        )
