FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ src/
RUN uv sync --frozen --no-dev

VOLUME /app/data
ENV DB_PATH=/app/data/simbakit.db
ENV WEB_HOST=0.0.0.0

EXPOSE 8585

CMD ["uv", "run", "python", "-m", "simbakit"]
