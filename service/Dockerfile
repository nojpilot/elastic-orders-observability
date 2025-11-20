FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./

EXPOSE 8080
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:8080", "--access-logfile", "-"]
