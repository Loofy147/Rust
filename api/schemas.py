from pydantic import BaseModel, constr, validator

class TaskRequest(BaseModel):
    input: constr(strip_whitespace=True, min_length=1, max_length=2048)

    @validator('input')
    def no_control_chars(cls, v):
        if any(ord(c) < 32 for c in v):
            raise ValueError('Input contains control characters')
        return v

class TaskResult(BaseModel):
    id: str
    status: str
    result: str = None