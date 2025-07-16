FROM python:3.10-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000 8001 8002
CMD ["python", "advanced_orchestrator/orchestrator.py"]