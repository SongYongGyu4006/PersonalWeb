# 백엔드 설계
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

    사용자가 채팅을 보내면 프론트에서 post호출. post로 호출되면 백엔드는 가장 먼저 이 질문을 잊지 않도록 RDS에 저장한다.
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
