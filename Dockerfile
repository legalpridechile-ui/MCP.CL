FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN adduser --disabled-password --gecos '' mcpuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todos tus archivos, incluyendo la carpeta templates
COPY . /app/

RUN chown -R mcpuser:mcpuser /app
USER mcpuser

# El puerto web en el que correrá tu SaaS
EXPOSE 8000

# Comando para ejecutar el servidor MCP
CMD ["python", "-m", "server"]
