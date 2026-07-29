# Hafif ve hızlı bir Python imajı kullanıyoruz
FROM python:3.10-slim

# Konteyner içindeki çalışma dizinimiz
WORKDIR /app

# Kütüphane listesini kopyala ve kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# API kodunu kopyala
COPY main.py .

# Dış dünyaya açılacak port
EXPOSE 8000

# Sunucuyu başlatma komutu (0.0.0.0 diyerek Docker dışından erişime izin veriyoruz)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]