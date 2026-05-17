import logging
from typing import List, Optional
from google.cloud import firestore
from google.api_core import exceptions
from datetime import datetime, timezone

from src.shared.models import UserSettings, TodoItem

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
        記錄使用者的 Chat ID 並初始化預設提醒時間（使用 UserSettings Pydantic 模型）。
        """
        doc_ref = self.db.collection("users").document(str(chat_id))
        user_settings = UserSettings(chat_id=str(chat_id))
        await doc_ref.set(user_settings.model_dump(), merge=True)
        logger.info(f"Saved user chat settings for {chat_id}")

    async def set_user_reminder_times(self, chat_id: str, times: list):
        """
        更新使用者的提醒時間設定。
        """
        doc_ref = self.db.collection("users").document(str(chat_id))
        await doc_ref.update({
            "reminder_times": times
        })
        logger.info(f"Updated reminder times for {chat_id}: {times}")

    async def get_user_settings(self, chat_id: str) -> Optional[UserSettings]:
        """
        獲取使用者的設定，回傳驗證後的 UserSettings 物件。
        """
        doc_ref = self.db.collection("users").document(str(chat_id))
        doc = await doc_ref.get()
        if doc.exists:
            try:
                return UserSettings.model_validate(doc.to_dict())
            except Exception as e:
                logger.error(f"Error validating user settings for {chat_id}: {e}")
        return None

    async def add_todo(self, chat_id: str, task_text: str):
        """
        新增待辦事項（使用 TodoItem Pydantic 模型）。
        """
        doc_ref = self.db.collection("todos").document()
        todo = TodoItem(chat_id=str(chat_id), task=task_text)
        await doc_ref.set(todo.model_dump())
        logger.info(f"Added todo for chat {chat_id}: {task_text}")

    async def get_pending_todos(self, chat_id: str) -> List[TodoItem]:
        """
        獲取特定使用者的待辦事項，回傳驗證後的 TodoItem 列表。
        """
        todos_ref = self.db.collection("todos")
        query = todos_ref.where("chat_id", "==", str(chat_id)).where("status", "==", "pending")
        docs = query.stream()
        
        items = []
        async for d in docs:
            try:
                items.append(TodoItem.model_validate({"id": d.id, **d.to_dict()}))
            except Exception as e:
                logger.error(f"Error validating todo item {d.id}: {e}")
        return items

    async def get_all_active_users(self) -> List[UserSettings]:
        """
        獲取所有活躍使用者及其設定，回傳驗證後的 UserSettings 列表。
        """
        users_ref = self.db.collection("users")
        docs = users_ref.stream()
        
        users = []
        async for d in docs:
            try:
                users.append(UserSettings.model_validate(d.to_dict()))
            except Exception as e:
                logger.error(f"Error validating active user data: {e}")
        return users

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
