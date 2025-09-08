# 1. Imagem base
FROM python:3.11-slim

# 2. Define o diretório de trabalho
WORKDIR /app

# 3. Instala o FFmpeg, Tesseract OCR e dependências de compilação
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    tesseract-ocr \
    tesseract-ocr-por \
    tesseract-ocr-eng \
    build-essential \
    gcc \
    g++ \
    make \
    pkg-config \
    libffi-dev \
    libssl-dev \
    cmake \
    libopencv-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgcc-s1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 4. Copia e instala as dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copia todos os arquivos do projeto
COPY . .

# 6. Cria um usuário não-root por segurança
RUN useradd --system --create-home appuser
RUN chown -R appuser:appuser /app

# 7. Muda para o usuário não-root
USER appuser

# 8. Comando de execução
CMD ["python", "bot.py"]