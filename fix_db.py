from database import SessionLocal
import models

db = SessionLocal()
try:
    # 1. 먼저 1번 사용자가 있는지 확인 (없으면 생성)
    user = db.query(models.User).filter(models.User.user_id == 1).first()
    if not user:
        user = models.User(user_id=1, username="yonggyu")
        db.add(user)
        db.commit()
        print("✅ 1번 사용자 생성 완료")

    # 2. 1번 대화방이 있는지 확인하고 생성 (title 인자 제거)
    existing_conv = db.query(models.Conversation).filter(models.Conversation.conv_id == 1).first()
    if not existing_conv:
        # 모델 정의에 따라 user_id와 conv_id만 할당합니다.
        new_conv = models.Conversation(conv_id=1, user_id=1)
        db.add(new_conv)
        db.commit()
        print("✅ 1번 대화방이 생성되었습니다!")
    else:
        print("ℹ️ 이미 1번 대화방이 존재합니다.")
finally:
    db.close()
