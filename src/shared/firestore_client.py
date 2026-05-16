import logging
from google.cloud import firestore
from google.api_core import exceptions
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class FirestoreClient:
    def __init__(self, project_id: str, collection_name: str = "processed_updates"):
        """
        初始化 Firestore 客戶端
        """
        self.db = firestore.AsyncClient(project=project_id, database="tgcost")
        self.collection_name = collection_name
        logger.info(f"Initialized FirestoreClient for project {project_id}, database tgcost, collection {collection_name}")

    async def try_lock(self, update_id: str, ttl_seconds: int = 600) -> bool:
        """
        [Deep Module] 嘗試獲取執行鎖。
        使用 Firestore Transaction 確保原子性，並包含超時重試機制。
        """
        transaction = self.db.transaction()
        doc_ref = self.db.collection(self.collection_name).document(str(update_id))

        @firestore.async_transactional
        async def _acquire_in_transaction(transaction, doc_ref):
            snapshot = await doc_ref.get(transaction=transaction)
            now = datetime.now(timezone.utc)
            
            if snapshot.exists:
                data = snapshot.to_dict()
                status = data.get("status")
                timestamp = data.get("timestamp")
                
                # 如果已完成，絕對不再執行
                if status == "completed":
                    return False
                
                # 如果正在處理中，檢查是否超時 (TTL)
                if status == "processing":
                    if timestamp and (now - timestamp).total_seconds() < ttl_seconds:
                        # 尚未超時，鎖定依然有效
                        return False
                    else:
                        logger.warning(f"🔓 Lock timeout for {update_id}, reclaiming.")
                
                # 其他狀態 (failed, timeout) 則允許重新鎖定
                transaction.update(doc_ref, {
                    "status": "processing",
                    "timestamp": now,
                    "retry_count": data.get("retry_count", 0) + 1
                })
                return True
            else:
                # 第一次嘗試
                transaction.set(doc_ref, {
                    "status": "processing",
                    "timestamp": now,
                    "retry_count": 0
                })
                return True

        try:
            return await _acquire_in_transaction(transaction, doc_ref)
        except Exception as e:
            logger.error(f"Transaction Error in try_lock: {e}")
            return False

    async def save_user_chat(self, chat_id: str):
        """
        記錄使用者的 Chat ID，用於定時提醒。
        """
        doc_ref = self.db.collection("users").document(str(chat_id))
        await doc_ref.set({
            "chat_id": str(chat_id),
            "last_active": datetime.now(timezone.utc)
        }, merge=True)

    async def add_todo(self, chat_id: str, task_text: str):
        """
        新增待辦事項。
        """
        doc_ref = self.db.collection("todos").document()
        await doc_ref.set({
            "chat_id": str(chat_id),
            "task": task_text,
            "status": "pending",
            "created_at": datetime.now(timezone.utc)
        })
        logger.info(f"Added todo for chat {chat_id}: {task_text}")

    async def get_pending_todos(self, chat_id: str):
        """
        獲取特定使用者的待辦事項。
        """
        todos_ref = self.db.collection("todos")
        query = todos_ref.where("chat_id", "==", str(chat_id)).where("status", "==", "pending")
        # stream() 不需要 await，它回傳的是 AsyncStreamGenerator
        docs = query.stream()
        return [{"id": d.id, **d.to_dict()} async for d in docs]

    async def get_all_active_users(self):
        """
        獲取所有活躍使用者的 Chat ID。
        """
        users_ref = self.db.collection("users")
        # stream() 不需要 await
        docs = users_ref.stream()
        return [d.to_dict().get("chat_id") async for d in docs]

    async def mark_completed(self, update_id: str):
        """
        標記 Webhook 更新任務完成
        """
        doc_ref = self.db.collection(self.collection_name).document(str(update_id))
        await doc_ref.update({
            "status": "completed",
            "completed_at": datetime.now(timezone.utc)
        })

    async def mark_failed(self, update_id: str, error: str):
        """
        標記 Webhook 更新任務失敗
        """
        doc_ref = self.db.collection(self.collection_name).document(str(update_id))
        await doc_ref.update({
            "status": "failed",
            "error": error,
            "failed_at": datetime.now(timezone.utc)
        })
