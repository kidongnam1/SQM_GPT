import os
from google import genai

# [Missing Exception Handling 방어 및 최신 Client 구조 적용]
try:
    # 1. API 키 환경 변수 로드 (Decoupling)
    api_key = os.environ.get("GEMINI_API_KEY")
    
    # 2. 최신 공인 엔진(google.genai) 클라이언트 초기화
    client = genai.Client(api_key=api_key)

    print("=== [최신형 엔진 탑재] 자체 구축 제미나이 CLI 가동 (종료하려면 'exit' 입력) ===")
    
    # 3. 무한 채팅 루프 (UI 로직)
    while True:
        user_input = input("\n[대표님 질문]: ")
        if user_input.lower() == 'exit':
            print("시스템을 안전하게 종료합니다.")
            break
        
        # 4. 최신 구글 제미나이 통신 규격 호출 (핵심 Logic)
        response = client.models.generate_content(
            model='gemini-1.5-pro',
            contents=user_input
        )
        print(f"\n[제미나이 응답]:\n{response.text}")

except Exception as e:
    print(f"\n[시스템 경고]: 최신 엔진 통신 중 문제가 발생했습니다. 상세 내역: {e}")