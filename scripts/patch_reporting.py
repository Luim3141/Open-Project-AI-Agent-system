from pathlib import Path

p = Path('openproject/ai/gateway/engineering_reporting.py')
text = p.read_text(encoding='utf-8')

target = '''        rows = db.execute(
            "SELECT id, report_type, title, created FROM engineering_reports "
            "WHERE project=6 ORDER BY created DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()

    items = [
        {
            "id": r["id"],
            "report_type": r["report_type"],
            "title": r["title"],
            "created": r["created"],
            "created_iso": format_iso(r["created"]),
        }
        for r in rows
    ]'''

replacement = '''        rows = db.execute(
            "SELECT id, report_type, title, created, document FROM engineering_reports "
            "WHERE project=6 ORDER BY created DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()

    items = []
    for r in rows:
        doc = json.loads(r["document"]) if r["document"] else {}
        items.append({
            "id": r["id"],
            "report_type": r["report_type"],
            "title": r["title"],
            "created": r["created"],
            "created_iso": format_iso(r["created"]),
            "narrative": doc.get("narrative", ""),
            "metrics": doc.get("metrics", {}),
            "summary": doc.get("summary", ""),
        })'''

assert target in text, "Target not found"
p.write_text(text.replace(target, replacement), encoding='utf-8')
print("Successfully patched engineering_reporting.py")
