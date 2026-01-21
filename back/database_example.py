from sqlalchemy import create_all, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_USER = "your_name"
DB_PASSWORD = "your_password"
DB_HOST = "DB name.cn8isi2c6dik.ap-northeast-2.rds.amazonaws.com"
DB_PORT = "3306"
DB_NAME = "your_db_name"

# 2. SQLAlchemy 연결 URL (MySQL용)
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# 3. 데이터베이스 엔진 생성
# pool_recycle은 연결 유지를 위해 MySQL 환경에서 권장되는 옵션입니다.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_recycle=3600
)

# 4. 세션 설정 (실제 DB 작업을 수행하는 객체)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 5. 모델 클래스들이 상속받을 기본 클래스
Base = declarative_base()