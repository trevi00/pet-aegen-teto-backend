"""
Flask 애플리케이션 팩토리
MVC 패턴을 적용한 Flask 앱 생성
"""

import os
import warnings
from flask import Flask, jsonify
from PIL import Image
from werkzeug.exceptions import HTTPException

Image.MAX_IMAGE_PIXELS = 40_000_000
warnings.simplefilter('error', Image.DecompressionBombWarning)
from flask_cors import CORS
import logging


def create_app(config_name='default'):
    """
    Flask 애플리케이션 팩토리

    Args:
        config_name: 설정 이름 ('default', 'development', 'production')

    Returns:
        Flask 앱 인스턴스
    """
    # Flask 앱 생성
    static_folder = 'static' if os.path.exists('static') else None
    app = Flask(__name__, static_folder=static_folder, static_url_path='')

    # CORS 설정
    origins = [o for o in os.environ.get('ALLOWED_ORIGINS', 'https://agtt.cloud').split(',') if o]
    CORS(app, origins=origins)

    # 기본 설정
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['RESULT_FOLDER'] = 'results'
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB (nginx 와 동일)
    app.config['MAX_FORM_PARTS'] = 5
    app.config['MAX_FORM_MEMORY_SIZE'] = 64 * 1024
    app.config['PROPAGATE_EXCEPTIONS'] = False

    # 폴더 생성
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # AI 모델 초기화
    analyzer, classifier = _init_ai_models()

    # Services 초기화
    from app.services import AnalyzerService, FileService

    analyzer_service = AnalyzerService(analyzer=analyzer, classifier=classifier)
    file_service = FileService(upload_folder=app.config['UPLOAD_FOLDER'])

    # Controllers에 의존성 주입
    from app.controllers import analysis_bp, main_bp
    from app.controllers.analysis_controller import init_analysis_controller

    init_analysis_controller(analyzer_service, file_service)

    # Blueprints 등록
    app.register_blueprint(main_bp)
    app.register_blueprint(analysis_bp)

    @app.errorhandler(Exception)
    def _handle_error(e):
        if isinstance(e, HTTPException):
            return jsonify({'success': False, 'error': e.name}), e.code
        app.logger.exception('unhandled error')
        return jsonify({'success': False, 'error': '서버 오류가 발생했습니다.'}), 500

    # 모니터링 초기화
    from app.monitoring import init_monitoring
    init_monitoring(app)

    app.logger.info("="*60)
    app.logger.info("Flask app initialized with MVC pattern")
    app.logger.info("="*60)

    return app


def _init_ai_models():
    """AI 모델 초기화"""
    print("="*60)
    print("Loading AI models...")
    print("="*60)

    analyzer = None
    classifier = None

    try:
        # AI 모델 import
        from app.ai.ensemble_analyzer import EnsembleAnalyzer
        from app.ai.classifier import AegenTetoClassifier

        analyzer = EnsembleAnalyzer()
        classifier = AegenTetoClassifier()

        print("="*60)
        print("All modules loaded successfully!")
        print("="*60)

    except Exception as e:
        print(f"Model loading failed: {e}")
        import traceback
        print(traceback.format_exc())

    return analyzer, classifier
