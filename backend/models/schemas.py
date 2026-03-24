from pydantic import BaseModel, Field


class RegisterPayload(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    password: str = Field(min_length=6, max_length=120)
    favorite_genre_ids: list[int] = Field(default_factory=list)


class LoginPayload(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    password: str = Field(min_length=6, max_length=120)


class FavoriteGenresPayload(BaseModel):
    genre_ids: list[int] = Field(default_factory=list)


class AccountUpdatePayload(BaseModel):
    current_password: str = Field(min_length=6, max_length=120)
    new_username: str | None = Field(default=None, min_length=3, max_length=40)
    new_password: str | None = Field(default=None, min_length=6, max_length=120)


class DeleteAccountPayload(BaseModel):
    password: str = Field(min_length=6, max_length=120)


class MovieActionPayload(BaseModel):
    movie_id: int
    recommended: bool | None = None
