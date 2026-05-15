FROM python:3.11-slim

# 設定環境變數
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV PATH="/home/appuser/.local/bin:$PATH"

WORKDIR /app

# 建立非 root 使用者
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# 安裝相依套件 (直接安裝到使用者目錄)
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 複製程式碼
COPY --chown=appuser:appuser . .

# 暴露埠號
EXPOSE 8080

# 執行入口
CMD ["python", "main.py"]
