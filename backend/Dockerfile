FROM python:3.12-slim

# Instalar FFmpeg e dependências de C++ (libgomp1 para ctranslate2)
RUN apt-get update && \
    apt-get install -y ffmpeg libgomp1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante da aplicação
COPY ./app ./app

# Criar pasta data
RUN mkdir -p /app/data

# Configurar variáveis de ambiente padrão
ENV HOST=0.0.0.0
ENV PORT=8000
ENV DATABASE_URL="sqlite:///./data/transcriber.db"
ENV DATA_DIR="./data"

EXPOSE 8000

# Executar a aplicação
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
