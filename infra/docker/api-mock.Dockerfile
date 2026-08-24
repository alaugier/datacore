FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV API_MOCK_HOST=0.0.0.0

EXPOSE 5050

CMD ["python3", "app.py"]
