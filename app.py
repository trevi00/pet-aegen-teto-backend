"""
Flask 웹 애플리케이션
반려동물 에겐 vs 테토 테스트
"""

import sys
import io

# Windows 콘솔 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import traceback
import uuid

from pet_analyzer import PetAnalyzer
from classifier import AegenTetoClassifier
from custom_analyzer import CustomPetAnalyzer
from ensemble_analyzer import EnsembleAnalyzer

# 프로덕션 환경에서 정적 파일 서빙 설정
static_folder = 'static' if os.path.exists('static') else None
app = Flask(__name__, static_folder=static_folder, static_url_path='')
CORS(app)  # React 앱과의 통신을 위한 CORS 설정

# 설정
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB 제한

# 폴더 생성
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# AI 모델 초기화 (앱 시작 시 한 번만)
print("="*60)
print("AI 모델 로딩 중...")
print("="*60)
analyzer = None
classifier = None

try:
    # 앙상블 분석기 로드 (BLIP + Custom)
    analyzer = EnsembleAnalyzer()
    classifier = AegenTetoClassifier()

    print("="*60)
    print("✓ 모든 모듈 로딩 완료!")
    print("="*60)
except Exception as e:
    print(f"모델 로딩 실패: {e}")
    print(traceback.format_exc())
    analyzer = None
    classifier = None


def allowed_file(filename):
    """허용된 파일 확장자 체크"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    """이미지 분석 API"""
    try:
        # 파일 체크
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': '이미지 파일이 없습니다.'}), 400

        file = request.files['image']

        if file.filename == '':
            return jsonify({'success': False, 'error': '파일이 선택되지 않았습니다.'}), 400

        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': '허용되지 않은 파일 형식입니다.'}), 400

        # 모델 체크
        if analyzer is None or classifier is None:
            return jsonify({'success': False, 'error': 'AI 모델이 로드되지 않았습니다. 서버를 재시작해주세요.'}), 500

        # 파일 저장 (한글 파일명 안전 처리)
        original_filename = file.filename
        _, ext = os.path.splitext(original_filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # secure_filename으로 안전한 파일명 생성
        safe_name = secure_filename(original_filename)
        # 한글 등으로 파일명이 사라진 경우 UUID 사용
        if not safe_name or safe_name == ext.lstrip('.'):
            unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}{ext}"
        else:
            unique_filename = f"{timestamp}_{safe_name}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        print(f"이미지 업로드 완료: {filepath}")

        # AI 분석 (앙상블 분석기 사용)
        print("AI 앙상블 분석 시작...")
        analysis_result = analyzer.analyze_for_classification(filepath)
        print(f"분석 완료: {analysis_result['classification']}")

        # 분류 및 코멘트 생성
        print("분류 및 코멘트 생성...")
        classification_result = classifier.classify(analysis_result)
        print(f"분류 완료: {classification_result}")

        # 신뢰도 정보 추가
        confidence = analysis_result.get('ensemble_info', {}).get('final_confidence', 50)
        models_agree = analysis_result.get('ensemble_info', {}).get('models_agree', False)

        return jsonify({
            'success': True,
            'classification': classification_result['classification'],
            'comment': classification_result['comment'],
            'aegen_percentage': classification_result['aegen_percentage'],
            'teto_percentage': classification_result['teto_percentage'],
            # 신뢰도 및 앙상블 정보 추가
            'confidence': confidence,
            'confidence_level': analyzer.get_confidence_level(confidence) if hasattr(analyzer, 'get_confidence_level') else '보통',
            'models_agree': models_agree,
            'ensemble_info': analysis_result.get('ensemble_info', {})
        })

    except Exception as e:
        print(f"분석 중 오류 발생: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': f'분석 중 오류가 발생했습니다: {str(e)}'}), 500


@app.route('/health')
def health():
    """서버 상태 체크"""
    return jsonify({
        'status': 'ok',
        'models_loaded': analyzer is not None and classifier is not None
    })


# 프로덕션 환경에서 프론트엔드 정적 파일 서빙
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """프론트엔드 정적 파일 서빙 (프로덕션)"""
    if static_folder and os.path.exists(static_folder):
        # API 경로는 404 반환
        if path.startswith('api/') or path.startswith('result/') or path.startswith('health'):
            return jsonify({'error': 'Not found'}), 404

        # 파일이 존재하면 해당 파일 반환
        if path and os.path.exists(os.path.join(static_folder, path)):
            return send_from_directory(static_folder, path)

        # 그 외의 경우 index.html 반환 (React Router)
        return send_from_directory(static_folder, 'index.html')
    else:
        # 개발 환경에서는 API만 동작
        return jsonify({'message': 'API Server Running', 'note': 'Frontend should be served separately in development mode'}), 200


# 데이터셋 관련 기능 (D 드라이브 사용)
DATASET_FOLDER = 'D:/pet-aegen-teto-dataset'
os.makedirs(os.path.join(DATASET_FOLDER, 'aegen'), exist_ok=True)
os.makedirs(os.path.join(DATASET_FOLDER, 'teto'), exist_ok=True)

# 학습 상태 관리
training_status = {
    'status': 'idle',  # idle, training, completed, error
    'progress': 0,
    'message': '',
    'log': '',
    'accuracy': 0
}


@app.route('/label')
def label_page():
    """라벨링 페이지"""
    return render_template('label.html')


@app.route('/train')
def train_page():
    """학습 페이지"""
    return render_template('train.html')


@app.route('/upload_dataset', methods=['POST'])
def upload_dataset():
    """데이터셋 업로드 및 저장"""
    try:
        files = request.files.getlist('images')
        labels = request.form.getlist('labels')

        if len(files) != len(labels):
            return jsonify({'success': False, 'error': '이미지와 라벨 수가 일치하지 않습니다.'}), 400

        saved_count = 0
        for file, label in zip(files, labels):
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                unique_filename = f"{timestamp}_{filename}"

                # 라벨에 따라 폴더 선택
                folder = os.path.join(DATASET_FOLDER, label)
                filepath = os.path.join(folder, unique_filename)
                file.save(filepath)
                saved_count += 1

        return jsonify({
            'success': True,
            'saved': saved_count,
            'message': f'{saved_count}장의 이미지가 저장되었습니다.'
        })

    except Exception as e:
        print(f"데이터셋 업로드 오류: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/dataset_info')
def dataset_info():
    """데이터셋 정보 조회"""
    try:
        aegen_count = len([f for f in os.listdir(os.path.join(DATASET_FOLDER, 'aegen'))
                          if os.path.isfile(os.path.join(DATASET_FOLDER, 'aegen', f))])
        teto_count = len([f for f in os.listdir(os.path.join(DATASET_FOLDER, 'teto'))
                         if os.path.isfile(os.path.join(DATASET_FOLDER, 'teto', f))])

        return jsonify({
            'success': True,
            'aegen': aegen_count,
            'teto': teto_count,
            'total': aegen_count + teto_count
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/start_training', methods=['POST'])
def start_training():
    """모델 학습 시작"""
    global training_status

    if training_status['status'] == 'training':
        return jsonify({'success': False, 'error': '이미 학습이 진행 중입니다.'}), 400

    try:
        # 학습 상태 초기화
        training_status = {
            'status': 'training',
            'progress': 0,
            'message': '학습 준비 중...',
            'log': '',
            'accuracy': 0
        }

        # 별도 스레드에서 학습 시작
        import threading
        from train_model_v2 import train_model_v2

        def training_thread():
            try:
                result = train_model_v2(DATASET_FOLDER, training_status)
                training_status['status'] = 'completed'
                training_status['progress'] = 100
                training_status['accuracy'] = result.get('accuracy', 0)
                training_status['message'] = '학습 완료!'
            except Exception as e:
                print(f"학습 중 오류: {e}")
                print(traceback.format_exc())
                training_status['status'] = 'error'
                training_status['message'] = f'학습 실패: {str(e)}'

        thread = threading.Thread(target=training_thread)
        thread.daemon = True
        thread.start()

        return jsonify({'success': True, 'message': '학습이 시작되었습니다.'})

    except Exception as e:
        print(f"학습 시작 오류: {e}")
        print(traceback.format_exc())
        training_status['status'] = 'error'
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/training_progress')
def training_progress():
    """학습 진행 상황 조회"""
    return jsonify(training_status)


@app.route('/auto_collect_page')
def auto_collect_page():
    """자동 이미지 수집 페이지 (비활성화)"""
    return jsonify({
        'success': False,
        'error': '자동 이미지 수집 기능은 현재 비활성화되어 있습니다.'
    }), 503


@app.route('/auto_collect', methods=['POST'])
def auto_collect():
    """자동 이미지 수집 API (비활성화)"""
    return jsonify({
        'success': False,
        'error': '자동 이미지 수집 기능은 현재 비활성화되어 있습니다. 수동으로 이미지를 업로드해주세요.'
    }), 503


if __name__ == '__main__':
    print("\n" + "="*50)
    print("🐾 반려동물 에겐 vs 테토 테스트 서버 시작!")
    print("="*50)
    print("서버 주소: http://localhost:5000")
    print("브라우저에서 위 주소로 접속하세요!")
    print("="*50 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
