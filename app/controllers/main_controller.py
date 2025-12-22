"""
메인 페이지 컨트롤러
"""

from flask import Blueprint, render_template, jsonify

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """메인 페이지"""
    try:
        return render_template('index.html')
    except:
        # 템플릿이 없으면 JSON 응답
        return jsonify({
            'message': 'Pet AeGen-Teto API Server',
            'status': 'running',
            'endpoints': {
                'analyze': '/analyze',
                'health': '/health'
            }
        })
