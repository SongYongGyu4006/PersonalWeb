from database import engine, Base
import models  # 우리가 만든 models.py를 불러옵니다.

def create_tables():
    print("🚀 RDS에 테이블 생성을 시작합니다...")
    try:
        # models.Base에 연결된 모든 테이블 구조를 생성합니다.
        models.Base.metadata.create_all(bind=engine)
        print("✅ 테이블 생성이 완료되었습니다!")
        
        # 생성된 테이블 목록 확인 (선택 사항)
        from sqlalchemy import inspect
        inspector = inspect(engine)
        print("📊 생성된 테이블 목록:", inspector.get_table_names())
        
    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    create_tables()
