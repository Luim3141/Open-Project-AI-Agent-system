FROM python:3.13-slim@sha256:09a17cad02668ae61ece136b4fd36ac3849e14f670ebedb637ea3e15580525bc
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home commander && mkdir /state && chown commander:commander /state
COPY app ./app
USER commander
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD python -m app.main health || exit 1
CMD ["python", "-m", "app.main"]
