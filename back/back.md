# 백엔드 설계
---
## 백엔드 동작 프로세스
1. 데이터 베이스 세션 관리 (의존성 주입)

    백엔드는 요청이 들어올 때마다 DB에 연결할 통로를 열고, 작업이 끝나면 닫아야 한다.
#### main.py
```
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```
2. 사용자의 질문 수신 및 DB기록

    사용자가 채팅을 보내면 프론트에서 post호출. post로 호출되면 백엔드는 가장 먼저 해당 ip의 대화방이 있는지 찾는다. 만약 없다면 새로운 대화방을 생성후 DB에 저장. 그 다음, 이 질문을 잊지 않도록 Message 테이블에 저장한다.
#### main.py
```
@app.post("/chat")
async def chat_with_claude(request: ChatRequest, db: Session = Depends(get_db)):
    db_conv = db.query(models.Conversation).filter(models.Conversation.conv_id == request.user_ip).first()
    if not db_conv:
        new_conv = models.Conversation(conv_id=request.user_ip)
        db.add(new_conv)
        db.commit()

    user_msg = models.Message(role="user", content=request.prompt, conv_id=request.user_ip)
    db.add(user_msg)
    db.commit()
```
3. AWS Bedrock(Claude)에게 질문하기

    AI를 호출하고, AI의 대화문맥파악을 위해 과거의 대화 내역(history)을 챙겨서 질문을 던진다.
   
   (history는 role(user or assistant)과 content가 저장돼 있음)
#### main.py
   ```
    messages = []
    for item in request.history:
        messages.append({"role": item["role"], "content": item["content"]})
    messages.append({"role": "user", "content": request.prompt})

    response = bedrock_runtime.invoke_model(
        modelId="us.anthropic.claude-sonnet-4-20250514-v1:0", # Claude 3.5 모델
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "messages": messages,
            "max_tokens": 1000
        })
    )
   ```
4. AI 답변 저장 및 응답 반환

    AI가 준 답변을 다시 DB에 저장하고, 최종적으로 프론트엔드에게 전달한다.

#### main.py
```
    response_body = json.loads(response.get('body').read())
    claude_response = response_body['content'][0]['text']

    bot_msg = models.Message(role="assistant", content=claude_response, conv_id=request.user_ip)
    db.add(bot_msg)
    db.commit()

    return {"answer": claude_response}
```
5. 히스토리 조회

    웹페이지 로드 시, get호출. get호출 시 백엔드는 특정 사용자의 IP를 기준으로 DB에서 메시지를 시간순으로 긁어모아 전송한다.
#### main.py
```
@app.get("/history/{user_ip}")
async def get_chat_history(user_ip: str, db: Session = Depends(get_db)):
    messages = db.query(models.Message)\
                 .filter(models.Message.conv_id == user_ip)\
                 .order_by(models.Message.created_at.asc())\
                 .all()
    
    history_data = [
        {"role": msg.role, "content": msg.content} 
        for msg in messages
    ]
    
    return {"history": history_data}
```

---
---
## 데이터베이스 설계
1. 접속 정보 정의

   RDS 서버의 주소와 ID, PW를 정의한다.
#### database.py
```
DB_USER = "your_name"
DB_PASSWORD = "your_password"
DB_HOST = "your_db_host"
DB_PORT = "3306"
DB_NAME = "your_db_name"
```
2. 연결 URL 생성 및 엔진 생성

   SQLALchemy가 인식할 수 있는 주소 형식으로 반환하고 실제 DB와 물리적으로 연결되는 장치인 엔진을 생성한다.
#### database.py
```
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_recycle=3600)
```
3. 세션 생성기

   실제 DB가 작업을 수행할 때마다 하나씩 뽑아서 쓰는 작업 창구이다.
#### database.py
```
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```
4. Base 클래스 생성

   이후 모델들이 이 클래스를 상속받아 DB 테이블로 등록된다.
#### database.py
```
Base = declarative_base()
```
5. user 테이블 정의

   속성은 user_id(PK), username(nullable), conversation을 갖는다.
#### models.py
```
class User(Base):
    __tablename__ = "users"
    user_id = Column(String(50), primary_key=True, index=True) 
    username = Column(String(50), nullable=False)
    conversations = relationship("Conversation", back_populates="owner")
```
6. conversation 테이블 정의

    속성은 conv_id(PK), user_id(FK), created_at, owner, message를 갖는다.
#### models.py
```
class Conversation(Base):
    __tablename__ = "conversations"
    conv_id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    owner = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")
```
7. message 테이블 정의

    속성은 msg_id(PK), conv_id(FK), role, content, created_at, conversation을 갖는다.
#### models.py
```
class Message(Base):
    __tablename__ = "messages"
    msg_id = Column(Integer, primary_key=True, index=True)
    conv_id = Column(String(50), ForeignKey("conversations.conv_id"))
    role = Column(Enum('user', 'assistant'), nullable=False
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    conversation = relationship("Conversation", back_populates="messages")
```

---
## 백엔드 동작 시나리오
1. main.py 실행 시 database.py의 engine을 통해 RDS 접속
2. models.py의 구조를 보고 RDS 내부에 users, conversations, messages 테이블을 자동 생성
3. 사용자가 접속하면 프론트에서 get 호출(+IP 전달).
4. get 호출 시, 백엔드는 models.Message 테이블에서 해당 IP와 일치하는 기록(conv_id == user_ip인)을 시간순으로 모두 조회 후 프론트에 반환.
5. 사용자가 메시지를 입력하고 '전송'버튼을 누르던가 enter을 치면, 프론트에서 post 호출.
6. post 호출 시, 백엔드는 가장 먼저 DB에서 request.user_ip의 대화방이 있는지 확인 후, 없다면 새로운 대화방을 만들고 커밋함.
7. post가 호출되며 넘어온 request의 prompt(내용)을 Message 테이블에 저장(role = 'user', content = request.prompt, conv_id = request.user_ip).
8. AI는 대화 문맥을 파악하기 위해 기존의 대화내용도 전달해줘야 해서 Message 리스트에 request.hitory를 저장한다. 또한 현재 질문(request.prompt)도 Message에 저장한다.
9. invoke_model()을 통해 AI에게 json형태로 Message 등 각 파라미터를 넘기고 json 형태로 응답을 받는다.
10. json.lead()를 통해 질의에 대한 응답을 읽고 그 내용을 추출한 다음 Message 테이블에 저장(role = 'assistant', content = 응답 내용, conv_id = request.user_ip).
11. 또한 응답을 post의 반환값으로 반환한다.

