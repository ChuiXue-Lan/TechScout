FROM python:3.11-slim

WORKDIR /app

# 禁用 Python 输出缓冲，确保日志实时显示
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
