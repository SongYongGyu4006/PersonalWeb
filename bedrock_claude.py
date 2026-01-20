import boto3
import json

def chat_with_claude():
    client = boto3.client('bedrock-runtime', region_name='us-east-1')
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    # 대화 기록을 저장할 리스트 (문맥 유지용)
    messages = []

    print("=== Claude 챗봇 모드 (종료하려면 'exit' 입력) ===")

    while True:
        user_input = input("나: ")
        if user_input.lower() == 'exit':
            break

        # 사용자의 질문을 메시지 리스트에 추가
        messages.append({"role": "user", "content": user_input})

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": messages,
            "temperature": 0.7
        })

        try:
            response = client.invoke_model(body=body, modelId=model_id)
            response_body = json.loads(response.get('body').read())
            claude_response = response_body['content'][0]['text']
            
            print(f"\nClaude: {claude_response}\n")

            # AI의 답변도 메시지 리스트에 추가 (다음 대화의 문맥이 됨)
            messages.append({"role": "assistant", "content": claude_response})

        except Exception as e:
            print(f"에러 발생: {e}")

if __name__ == "__main__":
    chat_with_claude()
