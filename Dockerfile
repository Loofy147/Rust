FROM python:3.10-slim
WORKDIR /ap<<<<<<< cursor/reasoning-agent-for-knowledge-graph-and-llm-interaction-bfb6
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
=======
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]> main
