FROM python:3.8-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip wheel \
    && pip wheel --wheel-dir /wheels -r requirements.txt


FROM python:3.8-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DATA_DIR=/app/data

WORKDIR /app

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup --home /app appuser \
    && mkdir -p /app/data /app/scripts

COPY --from=builder /wheels /wheels
COPY requirements.txt .

RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

COPY Bot ./Bot
COPY scripts/render-entrypoint.sh ./scripts/render-entrypoint.sh

RUN chmod 755 /app/scripts/render-entrypoint.sh \
    && chown -R appuser:appgroup /app

USER appuser

ENTRYPOINT ["/app/scripts/render-entrypoint.sh"]
CMD ["python", "-u", "Bot/bot.py"]
