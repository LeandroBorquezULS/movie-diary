from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
from backend.core.rate_limit import rate_limiter
from backend.routes import movies

app = FastAPI()

init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # para desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(movies.router, prefix="/movies")


@app.middleware("http")
async def apply_rate_limit(request: Request, call_next):
    rate_limiter.check(request)
    return await call_next(request)


@app.get("/")
def root():
    return {"message": "Movie Recommender API running"}
