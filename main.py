from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import search
from routers import match
from routers import coach

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 장착
app.include_router(search.router)
app.include_router(match.router)
app.include_router(coach.router)

@app.get("/")
def read_root():
    return {"message": "LoL Coach AI Server is Running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)