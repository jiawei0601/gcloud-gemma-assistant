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

    async def try_lock(self, update_id: str) -> bool:
        """
        嘗試鎖定 update_id 以進行去重。
        支援重試：如果狀態不是 'completed'，則允許再次嘗試。
        """
        doc_ref = self.db.collection(self.collection_name).document(str(update_id))
        try:
            doc = await doc_ref.get()
            if doc.exists:
                data = doc.to_dict()
                if data.get("status") == "completed":
                    logger.info(f"⏭️ Update {update_id} already completed. Skipping.")
                    return False
                else:
                    logger.warning(f"🔄 Update {update_id} was in state '{data.get('status')}', allowing retry.")
                    await doc_ref.update({
                        "status": "processing",
                        "retry_timestamp": datetime.now(timezone.utc)
                    })
                    return True
            else:
                # 原子化建立文件
                await doc_ref.create({
                    "status": "processing",
                    "timestamp": datetime.now(timezone.utc)
                })
                return True
        except exceptions.AlreadyExists:
            return False
        except Exception as e:
            logger.error(f"Firestore Error in try_lock: {e}")
            raise e

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
        docs = await query.stream()
        return [{"id": d.id, **d.to_dict()} async for d in docs]

    async def get_all_active_users(self):
        """
        獲取所有活躍使用者的 Chat ID。
        """
        users_ref = self.db.collection("users")
        docs = await users_ref.stream()
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
