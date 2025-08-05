from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, nullable=False)
    # Explicitly mark the password column as non-nullable and add a
    # trailing newline to keep tools and the shell happy.
    hashed_password: str = Field(nullable=False)
