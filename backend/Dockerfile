FROM python:3.9-slim

WORKDIR /app

# Copiar apenas os requisitos primeiro para aproveitar o cache de camadas do Docker
COPY requirements.txt .

# Instalar dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código
COPY . .

# Criar diretório de dados
RUN mkdir -p /app/data

# Expor porta
EXPOSE 8000

# Comando para iniciar a aplicação
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]