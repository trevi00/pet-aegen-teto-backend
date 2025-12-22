"""
E2E 테스트: 전체 시스템 통합 테스트
백엔드 API와 AI 모델이 정상적으로 작동하는지 확인
"""

import sys
import io
import os
import requests
import time

# Windows 콘솔 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def test_health_check():
    """서버 상태 확인"""
    print("\n" + "="*60)
    print("1. 서버 상태 확인 (Health Check)")
    print("="*60)

    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        data = response.json()

        print(f"✓ 서버 응답: {response.status_code}")
        print(f"✓ 상태: {data['status']}")
        print(f"✓ 모델 로드 여부: {data['models_loaded']}")

        if data['status'] == 'ok' and data['models_loaded']:
            print("✓ Health Check 성공!")
            return True
        else:
            print("✗ 모델이 로드되지 않았습니다.")
            return False

    except Exception as e:
        print(f"✗ Health Check 실패: {e}")
        return False


def test_dataset_info():
    """데이터셋 정보 확인"""
    print("\n" + "="*60)
    print("2. 데이터셋 정보 확인")
    print("="*60)

    try:
        response = requests.get("http://localhost:5000/dataset_info", timeout=5)
        data = response.json()

        if data['success']:
            print(f"✓ 에겐 데이터: {data['aegen']}장")
            print(f"✓ 테토 데이터: {data['teto']}장")
            print(f"✓ 총 데이터: {data['total']}장")
            return True
        else:
            print(f"✗ 데이터셋 정보 조회 실패: {data.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"✗ 데이터셋 정보 조회 실패: {e}")
        return False


def test_image_analysis():
    """이미지 분석 테스트"""
    print("\n" + "="*60)
    print("3. 이미지 분석 테스트")
    print("="*60)

    # 테스트용 이미지 경로 찾기
    dataset_folder = 'D:/pet-aegen-teto-dataset'

    test_images = []

    # 에겐 이미지 1개
    aegen_folder = os.path.join(dataset_folder, 'aegen')
    if os.path.exists(aegen_folder):
        aegen_files = [f for f in os.listdir(aegen_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if aegen_files:
            test_images.append(('aegen', os.path.join(aegen_folder, aegen_files[0])))

    # 테토 이미지 1개
    teto_folder = os.path.join(dataset_folder, 'teto')
    if os.path.exists(teto_folder):
        teto_files = [f for f in os.listdir(teto_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if teto_files:
            test_images.append(('teto', os.path.join(teto_folder, teto_files[0])))

    if not test_images:
        print("✗ 테스트 이미지를 찾을 수 없습니다.")
        return False

    results = []

    for label, image_path in test_images:
        print(f"\n[{label} 이미지 분석]")
        print(f"  경로: {image_path}")

        try:
            with open(image_path, 'rb') as f:
                files = {'image': f}
                response = requests.post("http://localhost:5000/analyze", files=files, timeout=60)

            if response.status_code == 200:
                data = response.json()

                if data['success']:
                    print(f"  ✓ 분석 성공!")
                    print(f"    - 분류: {data['classification']}")
                    print(f"    - 에겐: {data['aegen_percentage']:.1f}%")
                    print(f"    - 테토: {data['teto_percentage']:.1f}%")
                    print(f"    - 신뢰도: {data.get('confidence', 'N/A'):.1f}%")
                    print(f"    - 모델 일치: {'✓' if data.get('models_agree', False) else '✗'}")
                    print(f"    - 코멘트: {data['comment'][:50]}...")

                    results.append({
                        'expected': label,
                        'predicted': data['classification'],
                        'confidence': data.get('confidence', 0)
                    })
                else:
                    print(f"  ✗ 분석 실패: {data.get('error', 'Unknown error')}")
            else:
                print(f"  ✗ HTTP 오류: {response.status_code}")

        except Exception as e:
            print(f"  ✗ 예외 발생: {e}")

    # 결과 요약
    print("\n" + "-"*60)
    print("분석 결과 요약:")
    print("-"*60)

    if results:
        correct = sum(1 for r in results if r['expected'] == r['predicted'])
        accuracy = (correct / len(results)) * 100
        avg_confidence = sum(r['confidence'] for r in results) / len(results)

        print(f"  총 테스트: {len(results)}개")
        print(f"  정확도: {accuracy:.1f}% ({correct}/{len(results)})")
        print(f"  평균 신뢰도: {avg_confidence:.1f}%")

        return accuracy > 0

    return False


def test_result_image():
    """결과 이미지 생성 확인"""
    print("\n" + "="*60)
    print("4. 결과 이미지 확인")
    print("="*60)

    result_folder = 'results'
    if not os.path.exists(result_folder):
        print("✗ 결과 폴더가 없습니다.")
        return False

    result_files = [f for f in os.listdir(result_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    if result_files:
        print(f"✓ 결과 이미지 {len(result_files)}개 발견")
        print(f"  최근 파일: {result_files[-1]}")
        return True
    else:
        print("⚠ 결과 이미지가 없습니다.")
        return False


def run_all_tests():
    """모든 테스트 실행"""
    print("\n" + "="*60)
    print("🐾 반려동물 에겐 vs 테토 E2E 테스트")
    print("="*60)

    print("\n⚠ 테스트 시작 전에 Flask 서버가 실행 중이어야 합니다!")
    print("   서버 주소: http://localhost:5000")

    input("\nEnter 키를 눌러 테스트를 시작하세요...")

    tests = [
        ("Health Check", test_health_check),
        ("데이터셋 정보", test_dataset_info),
        ("이미지 분석", test_image_analysis),
        ("결과 이미지", test_result_image),
    ]

    results = []

    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
            time.sleep(1)  # 테스트 간 딜레이
        except Exception as e:
            print(f"\n✗ 테스트 실행 중 예외: {e}")
            results.append((name, False))

    # 최종 결과
    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print("="*60)

    for name, success in results:
        status = "✓ 성공" if success else "✗ 실패"
        print(f"  {status}: {name}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    print("\n" + "="*60)
    print(f"총 {total}개 테스트 중 {passed}개 통과 ({passed/total*100:.1f}%)")
    print("="*60)

    if passed == total:
        print("\n🎉 모든 테스트를 통과했습니다!")
    else:
        print("\n⚠ 일부 테스트가 실패했습니다. 로그를 확인하세요.")


if __name__ == '__main__':
    run_all_tests()
