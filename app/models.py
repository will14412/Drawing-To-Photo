from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str     = Field(index=True, unique=True, nullable=False)
    hashed_password: str