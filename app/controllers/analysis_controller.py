"""
이미지 분석 API 컨트롤러
"""

from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

analysis_bp = Blueprint('analysis', __name__)

# 서비스는 app factory에서 주입됨
_analyzer_service = None
_file_service = None


def init_analysis_controller(analyzer_service, file_service):
    """컨트롤러 초기화 (의존성 주입)"""
    global _analyzer_service, _file_service
    _analyzer_service = analyzer_service
    _file_service = file_service


@analysis_bp.route('/analyze', methods=['POST'])
def analyze():
    """이미지 분석 API"""
    try:
        # 파일 체크
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': '이미지 파일이 없습니다.'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': '파일이 선택되지 않았습니다.'}), 400
        
        # 모델 체크
        if not _analyzer_service or not _analyzer_service.is_ready():
            return jsonify({'success': False, 'error': 'AI 모델이 로드되지 않았습니다.'}), 500
        
        # 파일 저장
        success, filepath, error = _file_service.save_uploaded_file(file, file.filename)
        if not success:
            return jsonify({'success': False, 'error': error}), 400
        
        logger.info(f"이미지 업로드 완료: {filepath}")
        
        # AI 분석
        result = _analyzer_service.analyze_image(filepath)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"분석 중 오류: {e}", exc_info=True)
        return jsonify({'success': False, 'error': f'분석 중 오류가 발생했습니다: {str(e)}'}), 500


@analysis_bp.route('/health', methods=['GET'])
def health():
    """서버 상태 체크"""
    is_ready = _analyzer_service and _analyzer_service.is_ready()
    return jsonify({
        'status': 'ok',
        'models_loaded': is_ready
    })
