"""Concrete reviewer draft from a new controlled Native source; not human ground truth."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
source_path = ROOT.parent / 'n8n/final-completion-source392-frozen.json'
source = json.loads(source_path.read_text(encoding='utf-8'))
assert (source['native_id'], source['project_id'], source['lock_version']) == (392, 6, 0)
text = source['description']
sha = lambda value: hashlib.sha256(value).hexdigest()
definitions = [
    ('review:recovery-requirements:vi', 'vi', 'positive', 'Theo tài liệu WP392, phục hồi ORBIT-CANONICAL cần những bằng chứng nào?',
     'ORBIT-CANONICAL recovery requires a durable index failure receipt and current source citation.',
     'Cần cả durable index failure receipt và citation của source hiện hành; không phải chứng cứ một coding run đã chạy.'),
    ('review:recovery-requirements:en', 'en', 'positive', 'According to WP392, what evidence is required for ORBIT-CANONICAL recovery?',
     'ORBIT-CANONICAL recovery requires a durable index failure receipt and current source citation.',
     'Both a durable index failure receipt and a current source citation are required. This is a fixture requirement, not proof of a completed run.'),
    ('review:coding-premise:vi', 'vi', 'positive', 'WP392 có phải task viết code cần Dev agent thực thi không?',
     'Not a coding task.', 'Không. Mô tả ghi rõ đây không phải coding task; không suy diễn về task khác.'),
    ('review:coding-premise:en', 'en', 'positive', 'Is WP392 a coding task for a Dev agent?',
     'Not a coding task.', 'No. The source explicitly says this is not a coding task.'),
    ('review:retry-interval:vi', 'vi', 'negative', 'Riêng mô tả WP392 quy định phải đợi chính xác bao nhiêu giây giữa hai lần retry?',
     None, 'ABSTAIN: mô tả không đưa ra retry interval. Không trả lời không có retry; không suy diễn interval từ cấu hình Gateway hoặc nguồn ngoài scope.'),
    ('review:retry-interval:en', 'en', 'negative', 'In the WP392 description alone, exactly how many seconds must pass between retry attempts?',
     None, 'ABSTAIN: no retry interval is stated in this scoped description. This does not assert that retries do not exist.'),
]
cards = []
for identity, language, kind, query, literal, proposed in definitions:
    evidence = None
    if literal is not None:
        start = text.index(literal)
        evidence = {'text': literal, 'start': start, 'end': start + len(literal), 'sha256': sha(literal.encode()), 'offset_unit': 'Python Unicode code points within description'}
        assert text[evidence['start']:evidence['end']] == literal
    cards.append({'id': identity, 'language': language, 'kind_proposed': kind, 'query': query,
                  'native_ids': [392], 'expected_source_proposed': [392] if kind == 'positive' else [],
                  'evidence': evidence, 'proposed_judgment': proposed,
                  'owner_judgment': None, 'owner_correction': None, 'review_status': 'PENDING'})
packet = {'status': 'DRAFT_NOT_HUMAN_GROUND_TRUTH', 'author': 'implementation assistant; not independent evaluator',
          'human_reviewed': False, 'scored_or_tuned': False,
          'source': {**source, 'frozen_artifact_sha256': sha(source_path.read_bytes()), 'description_sha256': sha(text.encode()),
                     'source_sha256_meaning': 'canonical full Native read-back hash supplied by n8n source capture; not the description hash or salted knowledge document ID'},
          'scope': 'Each query restricted to native_ids=[392], frozen Native description v0, Project6; human permission/visibility must still be verified on a live call.',
          'cards': cards,
          'limitations': ['6 wording cases, only3 correlated intents,4positive+2negative; too small for quality acceptance',
                          'controlled fixture cannot establish representative semantic RAG quality',
                          'source and queries are now visible to implementation; no unseen-document or independent-holdout claim',
                          'negative judgments apply only to explicitly scoped description, not global semantic absence',
                          'owner review is a factual judgment, not approval to deploy failed candidate'],
          'independent_holdout_protocol': ['A separate evaluator authors new cases and evidence before any candidate scoring; labels must state actual reviewer identity/type.',
                                          'Split by intent before lock, keep paired VN/EN wording in one split; include positive, no-answer, false-premise, ACL, stale/deleted and multi-source cases.',
                                          'Publish only source/case counts, plan and SHA256; store holdout questions/labels privately outside implementation context.',
                                          'Freeze source/model/config/tests before one qualification run; verify source version and citation offsets, report answer and retrieval metrics separately.',
                                          'No tuning on failed/consumed holdout; retain failed evidence and create independently authored replacement for later candidates.']}
target = ROOT / 'OWNER_REVIEW_PACKET_V2.json'
assert not target.exists(), 'PRESERVE_EXISTING_REVIEW_PACKET'
target.write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'status': packet['status'], 'cases': len(cards), 'intents': 3, 'source': 392,
                  'packet_sha256': sha(target.read_bytes()), 'human_reviewed': False, 'holdout_created': False}))
