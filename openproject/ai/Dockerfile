ARG PYTHON_IMAGE=python:3.14-slim@sha256:f85c5697265c178cc6887276c55fe16cf3d14ca35c3df6a5eab3b360534a55d2
FROM ${PYTHON_IMAGE}
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 QLDAPM_AI_RUNTIME=/state QLDAPM_AI_WORKSPACES=/workspaces
WORKDIR /app
COPY requirements.lock.txt ./
RUN pip install --no-cache-dir -r requirements.lock.txt && useradd --uid 10001 --create-home gateway
COPY gateway/ ./gateway/
COPY knowledge_sources/ ./knowledge_sources/
USER 10001
EXPOSE 8090
CMD ["python", "-m", "uvicorn", "gateway.app:app", "--host", "0.0.0.0", "--port", "8090", "--no-access-log"]
