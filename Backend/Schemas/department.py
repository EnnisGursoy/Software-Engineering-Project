from pydantic import BaseModel


class DepartmentCreate(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True