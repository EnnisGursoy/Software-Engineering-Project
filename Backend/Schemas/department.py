from pydantic import BaseModel, ConfigDict


class DepartmentCreate(BaseModel):
    manager_id: int | None = None
    department_name: str

    model_config = ConfigDict(from_attributes=True)



class DepartmentOut(BaseModel):
    department_id: int
    manager_id: int | None = None
    department_name: str

    model_config = ConfigDict(from_attributes=True)


class DepartmentUpdate(BaseModel):
    manager_id: int | None = None
    department_name: str | None = None

    model_config = ConfigDict(from_attributes=True)