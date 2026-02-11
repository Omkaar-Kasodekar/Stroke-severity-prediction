FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

ENV POSTGRES_HOST=postgres \
    POSTGRES_PORT=5432 \
    POSTGRES_USER=postgres \
    POSTGRES_PASSWORD=password \
    POSTGRES_DB=stroke_cds

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

