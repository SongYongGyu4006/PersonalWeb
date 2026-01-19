# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 프론트엔드(JS)에서 백엔드로 접근할 수 있도록 허용 (CORS 설정)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터베이스 역할 (실제로는 MySQL이나 MongoDB를 연결함)
db_storage = []

class User(BaseModel):
    name: str

# 1. 데이터를 저장하는 API (Create)
@app.post("/users")
async def create_user(user: User):
    db_storage.append(user.name)
    return {"message": f"{user.name} 등록 성공!", "current_db": db_storage}

# 2. 데이터를 가져오는 API (Read)
@app.get("/users")
async def get_users():
    return {"users": db_storage}