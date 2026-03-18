FROM python:3.13-slim

ENV POETRY_VERSION=1.8.3 \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

WORKDIR /app/academy

COPY pyproject.toml poetry.lock ./
COPY src/ ./src/

RUN poetry install --only main --no-interaction --no-ansi

COPY notebooks/ ./notebooks/
COPY assets/ ./assets/

EXPOSE 8888

CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", \
     "--NotebookApp.token=''", "--NotebookApp.password=''", \
     "--notebook-dir=/app/academy"]
