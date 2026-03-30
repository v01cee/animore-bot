FROM python:3.12-slim

# Принудительно IPv4 (Docker может пытаться IPv6, который не маршрутизируется)
RUN echo 'precedence ::ffff:0:0/96 100' >> /etc/gai.conf

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
