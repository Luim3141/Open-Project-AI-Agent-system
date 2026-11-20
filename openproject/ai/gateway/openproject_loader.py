"""OpenProject Resource Loader for QLDAPM Local Second Brain RAG.
Converts live Work Packages, Epics, Tasks, Bugs, Subtasks, and Sprints
into canonical KnowledgeDocuments with native provenance and lockVersion.
"""
import re
from typing import Any, Dict, List, Optional
from .knowledge_classifier import KnowledgeDocType, KnowledgeDocument, classify_document
from .native import Native
from .presentation import safe_text
from .store import digest


def sanitize_text(text: Any, project_id=None) -> str:
    if text is None:
        return ""
    if isinstance(text, dict):
        text = text.get("raw", "")
    text_str = safe_text(text)
    if str(project_id)=='6':
        # Project6 stores Native artifact references, never crawls their targets.
        # Keep the classifier's no-URL/no-crawler boundary and use opaque aliases;
        # the fresh Native citation remains the way to recover the original link.
        text_str=re.sub(r'(?:https?://|internal-ref://)[^\s<>\"\)\]]+',
            lambda match:'[Native-reference:'+digest(match[0])[:16]+']',text_str)
        text_str=re.sub(r'github\.com', '[external-host-reference]',text_str,flags=re.I)
    # Redact URLs to comply with internal policy
    return re.sub(r"https?://", "internal-ref://", text_str).strip()


def actor_work_package_document(wp, project_id, actor, role, activities):
    comments = sorted((a for a in activities if type(a.get('id')) is int
        and a['id'] > 0 and (a.get('comment') or {}).get('raw')), key=lambda a:a['id'])[-20:]
    description = wp.get('description') or {}
    content = sanitize_text(wp.get('subject',''),project_id)+'\n'+sanitize_text(
        description.get('raw','') if isinstance(description,dict) else description,project_id)[:47000]
    # shortcut: retain the latest 20 comments, expand with separate activity documents for full journal history.
    content += '\n'+'\n'.join(f'Bình luận #{a["id"]}: '+sanitize_text(a['comment']['raw'],project_id)[:750] for a in comments)
    metadata={'native_id':wp['id'],'lock_version':wp['lockVersion'],'actor_id':actor,
        'activity_ids':[a['id'] for a in comments],
        'activity_hashes':{str(a['id']):digest(sanitize_text(a['comment']['raw'],project_id)) for a in comments}}
    if wp.get('updatedAt') is not None:metadata['source_updated_at']=wp['updatedAt']
    return classify_document(KnowledgeDocType.WORK_PACKAGE,str(project_id),f'actor:{actor}:wp:{wp["id"]}',
        safe_text(wp['subject']),content[:64000],allowed_roles=[role],metadata=metadata)


def work_package_to_document(wp: Dict[str, Any], project_id: str = "5") -> KnowledgeDocument:
    wp_id = wp.get("id")
    subject = sanitize_text(wp.get("subject", f"Work Package #{wp_id}"),project_id)
    desc = sanitize_text(wp.get("description", ""),project_id)
    lock_version = wp.get("lockVersion", 1)

    type_title = wp.get("_links", {}).get("type", {}).get("title", "Task")
    status_title = wp.get("_links", {}).get("status", {}).get("title", "NEW")
    priority_title = wp.get("_links", {}).get("priority", {}).get("title", "Normal")
    assignee_title = wp.get("_links", {}).get("assignee", {}).get("title", "Chưa phân công")
    version_title = wp.get("_links", {}).get("version", {}).get("title", "Chưa có Sprint")
    parent_href = wp.get("_links", {}).get("parent", {}).get("href", "")
    parent_id = int(parent_href.split("/")[-1]) if parent_href and parent_href.split("/")[-1].isdigit() else None

    # Determine DocType
    if type_title == "Epic":
        doc_type = KnowledgeDocType.ARCHITECTURE
    elif type_title in ("Feature", "User story"):
        doc_type = KnowledgeDocType.ACCEPTANCE_CRITERIA
    else:
        doc_type = KnowledgeDocType.WORK_PACKAGE

    content_lines = [
        f"Mã công việc: #{wp_id}",
        f"Tiêu đề: {subject}",
        f"Loại: {type_title}",
        f"Trạng thái: {status_title}",
        f"Mức độ ưu tiên: {priority_title}",
        f"Người phụ trách: {assignee_title}",
        f"Sprint / Phiên bản: {version_title}",
    ]
    if parent_id:
        content_lines.append(f"Công việc cha (Parent ID): #{parent_id}")
    if wp.get("startDate"):
        content_lines.append(f"Ngày bắt đầu: {wp.get('startDate')}")
    if wp.get("dueDate"):
        content_lines.append(f"Hạn hoàn thành: {wp.get('dueDate')}")
    if desc:
        content_lines.append(f"\nMô tả chi tiết:\n{desc}")

    full_content = "\n".join(content_lines)

    title = f"[{type_title}] #{wp_id} - {subject}"
    source_id = f"op:wp:{wp_id}"

    return classify_document(
        doc_type=doc_type,
        project_id=str(project_id),
        source_id=source_id,
        title=title,
        content=full_content,
        allowed_roles=["PM", "BA", "FE", "BE", "QA"],
        metadata={
            "native_id": wp_id,
            "work_package_id": wp_id,
            "lock_version": lock_version,
            "type": type_title,
            "status": status_title,
            "parent_id": parent_id,
            "version": version_title,
        },
    )


def sprint_to_document(sprint: Dict[str, Any], project_id: str = "5") -> KnowledgeDocument:
    sp_id = sprint.get("id")
    name = sprint.get("name", f"Sprint {sp_id}")
    status = sprint.get("status", "open")
    start = sprint.get("startDate", "N/A")
    finish = sprint.get("finishDate", "N/A")

    content = (
        f"Sprint ID: {sp_id}\n"
        f"Tên Sprint: {name}\n"
        f"Trạng thái: {status}\n"
        f"Ngày bắt đầu: {start}\n"
        f"Ngày kết thúc: {finish}\n"
    )

    return classify_document(
        doc_type=KnowledgeDocType.SPRINT_REPORT,
        project_id=str(project_id),
        source_id=f"op:sprint:{sp_id}",
        title=f"Thông tin {name}",
        content=content,
        allowed_roles=["PM", "BA", "FE", "BE", "QA"],
        metadata={
            "sprint_id": sp_id,
            "name": name,
            "status": status,
        },
    )


def load_openproject_work_packages(native: Native, project_id: str = "5") -> List[KnowledgeDocument]:
    packages = native.packages()
    return [work_package_to_document(wp, project_id=project_id) for wp in packages]


def load_openproject_sprints(native: Native, project_id: str = "5") -> List[KnowledgeDocument]:
    sprints = native.sprints()
    return [sprint_to_document(sp, project_id=project_id) for sp in sprints]
