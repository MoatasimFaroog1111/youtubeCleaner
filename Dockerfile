FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# يعيد بناء ملفات OAuth من متغيرات البيئة عند بدء التشغيل
CMD ["sh", "-c", "printf '%s' \"$GOOGLE_CREDENTIALS_JSON\" > credentials.json && printf '%s' \"$GOOGLE_TOKEN_JSON\" > token.json && touch .env && python main_guardian.py"]
