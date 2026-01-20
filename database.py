from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ⚠️ RDS 생성이 완료되면 실제 '엔드포인트' 주소로 바꾸세요!
# 형식: mysql+pymysql://사용자이름:비밀번호@엔드포인트:3306/DB이름
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://admin:thddydrb001!@yonggyu-bedrock-db.cn8isi2c6dik.ap-northeast-2.rds.amazonaws.com:3306/yonggyu-bedrock-db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# DB 세션을 가져오는 의존성 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
