from pydantic import BaseModel

class TaskRequest(BaseModel):
    input: str

class TaskResult(BaseModel):
    id: str
    status: str
    result: str = None