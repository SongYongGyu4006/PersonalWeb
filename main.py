from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import boto3
import json
from sqlalchemy.orm import Session

# DB 연동을 위한 모듈 불러오기
import models
from database import engine, SessionLocal

# 서버 실행 시 테이블이 없으면 자동으로 생성
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# DB 세션을 할당받기 위한 의존성 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bedrock 클라이언트 초기화 (기존 로직 유지)
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1' 
)

class ChatRequest(BaseModel):
    prompt: str
    history: list = [] # 채팅 기록
    user_ip: str = "unknown"

@app.post("/chat")
async def chat_with_claude(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        # 1. 사용자의 질문을 RDS 'messages' 테이블에 저장
        user_msg = models.Message(role="user", content=request.prompt, conv_id=request.user_ip)
        db.add(user_msg)
        db.commit()

        # 2. Bedrock 프롬프트 구성 (기존 로직 그대로 사용)
        messages = []
        for item in request.history:
            messages.append({"role": item["role"], "content": item["content"]})
        messages.append({"role": "user", "content": request.prompt})

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": messages,
            "temperature": 0.7
        })

        model_id = "us.anthropic.claude-sonnet-4-20250514-v1:0"

        response = bedrock_runtime.invoke_model(
            body=body,
            modelId=model_id,
            accept="application/json",
            contentType="application/json"
        )

        response_body = json.loads(response.get('body').read())
        claude_response = response_body['content'][0]['text']

        # 3. Claude의 답변을 RDS 'messages' 테이블에 저장
        bot_msg = models.Message(role="assistant", content=claude_response, conv_id=request.user_ip)
        db.add(bot_msg)
        db.commit()

        return {"answer": claude_response}

    except Exception as e:
        db.rollback() # 에러 발생 시 진행 중인 DB 작업 취소
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{user_ip}")
async def get_chat_history(user_ip: str, db: Session = Depends(get_db)):
    # 1. DB에서 해당 user_ip를 가진 메시지들을 생성 시간순(asc)으로 조회
    messages = db.query(models.Message)\
                 .filter(models.Message.conv_id == user_ip)\
                 .order_by(models.Message.created_at.asc())\
                 .all()
    
    # 2. 프론트엔드가 이해할 수 있는 리스트 형식으로 반환
    return {
        "history": [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]
    }

if __name__ == "__main__":
    import uvicorn
    # 0.0.0.0으로 설정해야 외부(S3/브라우저)에서 접속이 가능합니다.
    uvicorn.run(app, host="0.0.0.0", port=8000)
