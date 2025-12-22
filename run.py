"""
Flask 애플리케이션 실행 진입점
MVC 패턴이 적용된 리팩토링 버전
"""

from app import create_app

# Flask 앱 생성
app = create_app()

if __name__ == '__main__':
    print("\n" + "="*50)
    print("Pet Aegen vs Teto Test Server Starting!")
    print("="*50)
    print("Server address: http://localhost:5000")
    print("Please connect via browser!")
    print("="*50 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
