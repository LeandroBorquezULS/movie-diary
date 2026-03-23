from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import movies

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # para desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(movies.router, prefix="/movies")


@app.get("/")
def root():
    return {"message": "Movie Recommender API running"}