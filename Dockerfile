FROM python:3.11-slim

WORKDIR /app

ENV FLASK_APP=wsgi.py \
    FLASK_ENV=production \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONBUFFERED=1

# Install dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --system --no-create-home --shell /bin/false blog \
    && mkdir -p instance uploads \
    && chown -R blog:blog /app \
    && chmod +x entrypoint.sh

USER blog

EXPOSE 5000

ENTRYPOINT ["./entrypoint.sh"]