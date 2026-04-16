from typing import TypedDict, Literal

TaskStatus = Literal["pending", "processing", "completed", "failed"]


class GenerationTask(TypedDict, total=False):
    status: TaskStatus
    stage: str
    message: str
    progress: int
    created_at: float
    updated_at: float
    response_status_code: int
    response_content_type: str
    response_headers: dict
    response_body: bytes
    error_message: str
