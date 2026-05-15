# 使用輕量化 Python 映像檔
FROM python:3.11-slim AS builder

# 設定環境變數
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 安裝編譯依賴 (若有需要)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 建立虛擬環境
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 安裝相依套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- 最終運行階段 ---
FROM python:3.11-slim

WORKDIR /app

# 從 builder 複製虛擬環境與程式碼
COPY --from=builder /opt/venv /opt/venv
COPY . .

# 設定路徑與環境變數
ENV PATH="/opt/venv/bin:$PATH"
ENV PORT=8080

# 建立非 root 使用者以提升安全性
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# 暴露埠號
EXPOSE 8080

# 執行入口
CMD ["python", "main.py"]
