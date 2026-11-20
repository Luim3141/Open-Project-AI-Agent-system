FROM qldapm-gateway:stabilization-admission
COPY gateway/engineering.py gateway/engineering_fencing.py gateway/engineering_operator.py gateway/engineering_reporting.py gateway/knowledge_search.py gateway/knowledge_ingestion.py gateway/knowledge_storage.py gateway/vector_client.py gateway/store.py /app/gateway/
