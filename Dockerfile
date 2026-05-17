FROM python:3.11-slim

WORKDIR /app

# 安裝基礎依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式碼
COPY . .

# 設定環境變數預設值
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# 曝露埠號
EXPOSE 8080

# 使用 gunicorn 啟動 Flask 應用 (推薦用於 Cloud Run 生產環境)
# 如果您更偏好單純 python bot.py 也可以，但 gunicorn 穩定性更高
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 bot:app
