FROM python:3.12-slim

WORKDIR /app

RUN python -m pip install --upgrade pip

# 1) Сначала requirements (чтобы кешировалось)
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/requirements.txt

# 2) Потом код
COPY . /app
