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
        self.db = firestore.AsyncClient(project=project_id)
        self.collection_name = collection_name
        logger.info(f"Initialized FirestoreClient for project {project_id}, collection {collection_name}")

    async def try_lock(self, update_id: str) -> bool:
        """
        嘗試鎖定 update_id 以進行去重。
        使用 .create() 原子操作。
        """
        doc_ref = self.db.collection(self.collection_name).document(str(update_id))
        try:
            # 原子化建立文件
            await doc_ref.create({
                "status": "processing",
                "timestamp": datetime.now(timezone.utc)
            })
            return True
        except exceptions.AlreadyExists:
            # 已經存在，代表是重複請求
            return False
        except Exception as e:
            logger.error(f"Firestore Error in try_lock: {e}")
            # 如果是權限錯誤 (403)，則這裡會報錯
            raise e

    async def mark_completed(self, update_id: str):
        """
        標記任務完成
        """
        doc_ref = self.db.collection(self.collection_name).document(str(update_id))
        await doc_ref.update({
            "status": "completed",
            "completed_at": datetime.now(timezone.utc)
        })

    async def mark_failed(self, update_id: str, error: str):
        """
        標記任務失敗
        """
        doc_ref = self.db.collection(self.collection_name).document(str(update_id))
        await doc_ref.update({
            "status": "failed",
            "error": error,
            "failed_at": datetime.now(timezone.utc)
        })
