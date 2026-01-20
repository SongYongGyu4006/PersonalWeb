import pymysql

# 주의: 여기서는 접속 주소에 DB 이름을 넣지 않습니다.
connection = pymysql.connect(
    host='yonggyu-bedrock-db.cn8isi2c6dik.ap-northeast-2.rds.amazonaws.com',
    user='admin',
    password='thddydrb001!',
    charset='utf8mb4'
)

try:
    with connection.cursor() as cursor:
        # 에러 메시지에 나왔던 그 이름을 그대로 생성합니다.
        sql = "CREATE DATABASE IF NOT EXISTS `yonggyu-bedrock-db`"
        cursor.execute(sql)
    connection.commit()
    print("✅ 'yonggyu-bedrock-db' 데이터베이스 생성 성공!")
finally:
    connection.close()
