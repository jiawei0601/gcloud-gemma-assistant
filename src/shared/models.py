from __future__ import annotations
from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class TaskStatus(str, Enum):
    """
    研究任務的狀態枚舉
    """
    PENDING = "pending"      # 等待中
    IN_PROGRESS = "running"  # 執行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失敗
    PAUSED = "paused"        # 已暫停

class InformationFragment(BaseModel):
    """
    資訊碎片：研究過程中從外部來源（如網頁、PDF）擷取到的原始資訊片段。
    """
    id: UUID = Field(default_factory=uuid4)
    content: str = Field(..., description="擷取到的原始文字或內容")
    source: str = Field(..., description="資訊來源的 URL 或檔案路徑")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="額外的元數據（如標題、擷取時間等）")
    timestamp: datetime = Field(default_factory=datetime.now)

class ResearchArtifact(BaseModel):
    """
    研究成果：由 AI 整理後的結構化產出物（例如：摘要、報告、比較表格）。
    """
    id: UUID = Field(default_factory=uuid4)
    title: str = Field(..., description="成果的標題")
    artifact_type: str = Field(..., description="成果類型（例如：summary, report, list_of_links）")
    content: str = Field(..., description="整理後的詳細內容")
    related_fragment_ids: List[UUID] = Field(default_factory=list, description="此成果所引用的資訊碎片 ID 列表")
    created_at: datetime = Field(default_factory=datetime.now)

class ResearchTask(BaseModel):
    """
    研究任務：整個作業的核心單元，包含了目標、狀態、收集到的資訊與最終產出的成果。
    """
    id: UUID = Field(default_factory=uuid4)
    goal: str = Field(..., description="研究的核心目標或問題")
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    
    # 收集到的原始資料碎片
    fragments: List[InformationFragment] = Field(default_factory=list)
    
    # 產出的結構化成果
    artifacts: List[ResearchArtifact] = Field(default_factory=list)
    
    # 任務的詳細紀錄與元數據
    description: Optional[str] = Field(None, description="任務的詳細說明")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def update_timestamp(self):
        """更新任務的最後修改時間"""
        self.updated_at = datetime.now()

# 為了處理 Pydantic 循環引用或未來擴充，建議加上此註解
ResearchTask.model_rebuild()
