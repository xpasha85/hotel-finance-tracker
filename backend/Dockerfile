FROM python:3.12-slim

WORKDIR /app

# 1. pip
RUN python -m pip install --upgrade pip

# 2. зависимости (явно!)
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    sqlalchemy \
    psycopg[binary] \
    alembic \
    python-jose \
    passlib[bcrypt] \
    python-multipart \
    pydantic \
    pydantic-settings

# 3. код
COPY . /app
