"""
결과 이미지 생성 모듈
분석 결과를 시각화하여 이미지로 생성합니다.
"""

from PIL import Image, ImageDraw, ImageFont
import os


class ResultImageGenerator:
    def __init__(self):
        """이미지 생성기 초기화"""
        # 색상 팔레트 (앱 디자인과 일치)
        self.colors = {
            'aegen': {
                'primary': '#FF9EC8',  # 핑크
                'gradient_start': '#FFB8E6',
                'gradient_end': '#A5C8FF',
                'bg': '#E8D5F5',  # 보라
                'bar_bg': '#F5E0FF'
            },
            'teto': {
                'primary': '#7B9EFF',  # 블루
                'gradient_start': '#FFB8E6',
                'gradient_end': '#A5C8FF',
                'bg': '#E8D5F5',  # 보라
                'bar_bg': '#F5E0FF'
            }
        }

    def create_result_image(self, original_image_path, classification_result, output_path):
        """
        분석 결과를 포함한 결과 이미지를 생성합니다.

        Args:
            original_image_path: 원본 이미지 경로
            classification_result: classifier의 분류 결과
            output_path: 저장할 파일 경로

        Returns:
            str: 생성된 이미지 경로
        """
        # 원본 이미지 로드 (webp 등 다양한 형식 지원을 위해 RGB로 변환)
        img = Image.open(original_image_path).convert('RGB')

        # 이미지 크기 조정 (최대 500px)
        max_size = 500
        if img.width > max_size or img.height > max_size:
            if img.width > img.height:
                new_width = max_size
                new_height = int(img.height * (max_size / img.width))
            else:
                new_height = max_size
                new_width = int(img.width * (max_size / img.height))
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 결과 영역을 추가할 캔버스 생성
        # 최소 폭 설정 (텍스트가 잘리지 않도록)
        min_width = 450
        canvas_width = max(img.width, min_width)

        # 코멘트 길이에 따라 높이 동적 계산
        comment = classification_result['comment']
        max_chars_per_line = 25
        # 실제 줄 수 정확히 계산
        actual_comment_lines = (len(comment) + max_chars_per_line - 1) // max_chars_per_line
        # 실제 레이아웃 기반 정확한 높이 계산
        # 헤더(50) + 간격(15) + 에겐라벨(30) + 에겐바(25) + 간격(15) + 테토라벨(30) + 테토바(25) + 코멘트여백(30) + 코멘트줄(40*n) + 하단여백(70)
        result_height = 50 + 15 + 30 + 25 + 15 + 30 + 25 + 30 + (actual_comment_lines * 40) + 70

        canvas_height = img.height + result_height

        classification = classification_result['classification']
        colors = self.colors[classification]

        # 새 캔버스 생성
        canvas = Image.new('RGB', (canvas_width, canvas_height), colors['bg'])

        # 원본 이미지 붙이기 (중앙 정렬)
        img_x = (canvas_width - img.width) // 2
        canvas.paste(img, (img_x, 0))

        # 그리기 객체 생성
        draw = ImageDraw.Draw(canvas)

        # 결과 영역 그리기
        result_y_start = img.height

        # 배경 그리기
        draw.rectangle(
            [(0, result_y_start), (canvas_width, canvas_height)],
            fill=colors['bg']
        )

        # 헤더 영역 (그라데이션 효과를 위해 간단히 단색으로)
        header_height = 60
        draw.rectangle(
            [(0, result_y_start), (canvas_width, result_y_start + header_height)],
            fill='#FFFFFF'
        )

        try:
            # 폰트 로드 시도 (한글 지원 폰트) - 크기 축소
            title_font_size = 32
            text_font_size = 18
            small_font_size = 14

            # Windows 기본 한글 폰트
            font_paths = [
                'C:\\Windows\\Fonts\\malgun.ttf',  # 맑은 고딕
                'C:\\Windows\\Fonts\\gulim.ttc',   # 굴림
            ]

            title_font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    title_font = ImageFont.truetype(font_path, title_font_size)
                    text_font = ImageFont.truetype(font_path, text_font_size)
                    small_font = ImageFont.truetype(font_path, small_font_size)
                    break

            if title_font is None:
                # 폰트를 찾지 못한 경우 기본 폰트 사용
                title_font = ImageFont.load_default()
                text_font = ImageFont.load_default()
                small_font = ImageFont.load_default()

        except:
            # 폰트 로드 실패 시 기본 폰트
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # 타이틀 텍스트
        if classification == 'aegen':
            title_text = "에겐 인증!"
            emoji = "💪"
        else:
            title_text = "테토 인증!"
            emoji = "🥰"

        # 타이틀 그리기 (중앙 정렬)
        title_full = f"{emoji} {title_text} {emoji}"
        title_bbox = draw.textbbox((0, 0), title_full, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (canvas_width - title_width) // 2
        title_y = result_y_start + 10

        draw.text(
            (title_x, title_y),
            title_full,
            fill=colors['primary'],
            font=title_font
        )

        # 퍼센티지 바 그리기
        bar_y = result_y_start + header_height + 15  # 헤더와 첫 바 사이 간격
        bar_height = 25  # 바 높이
        bar_margin = 30  # 좌우 여백

        # 에겐 바
        aegen_percent = classification_result['aegen_percentage']
        draw.text(
            (bar_margin, bar_y),  # 라벨을 바 위에 배치
            "에겐 💪",
            fill='#333333',
            font=text_font
        )

        bar_width = canvas_width - (bar_margin * 2) - 60  # 퍼센트 표시 공간 확보
        aegen_bar_width = int((bar_width * aegen_percent) / 100)
        aegen_bar_y = bar_y + 30  # 라벨 아래 30px에 바 배치

        # 배경 바 (둥근 모서리)
        draw.rounded_rectangle(
            [(bar_margin, aegen_bar_y), (bar_margin + bar_width, aegen_bar_y + bar_height)],
            radius=15,
            fill=colors['bar_bg']
        )
        # 에겐 바 (둥근 모서리)
        if aegen_bar_width > 0:
            draw.rounded_rectangle(
                [(bar_margin, aegen_bar_y), (bar_margin + aegen_bar_width, aegen_bar_y + bar_height)],
                radius=15,
                fill='#FF9EC8'  # 에겐 색상
            )
        draw.text(
            (bar_margin + bar_width + 10, aegen_bar_y + 5),
            f"{int(aegen_percent)}%",
            fill='#333333',
            font=small_font
        )

        # 테토 바
        teto_percent = classification_result['teto_percentage']
        teto_bar_y = aegen_bar_y + bar_height + 15  # 에겐 바 다음에 15px 간격

        draw.text(
            (bar_margin, teto_bar_y),  # 라벨을 바 위에 배치
            "테토 🥰",
            fill='#333333',
            font=text_font
        )

        teto_bar_width = int((bar_width * teto_percent) / 100)
        teto_actual_bar_y = teto_bar_y + 30  # 라벨 아래 30px에 바 배치

        # 배경 바 (둥근 모서리)
        draw.rounded_rectangle(
            [(bar_margin, teto_actual_bar_y), (bar_margin + bar_width, teto_actual_bar_y + bar_height)],
            radius=15,
            fill=colors['bar_bg']
        )
        # 테토 바 (둥근 모서리)
        if teto_bar_width > 0:
            draw.rounded_rectangle(
                [(bar_margin, teto_actual_bar_y), (bar_margin + teto_bar_width, teto_actual_bar_y + bar_height)],
                radius=15,
                fill='#7B9EFF'  # 테토 색상
            )
        draw.text(
            (bar_margin + bar_width + 10, teto_actual_bar_y + 5),
            f"{int(teto_percent)}%",
            fill='#333333',
            font=small_font
        )

        # 코멘트 그리기
        comment_y = teto_actual_bar_y + bar_height + 30

        # 한글 텍스트 줄바꿈 (글자 수 기준) - 위에서 정의한 max_chars_per_line 사용
        lines = []
        for i in range(0, len(comment), max_chars_per_line):
            lines.append(comment[i:i + max_chars_per_line])

        # 각 줄을 중앙 정렬하여 그리기
        for i, line in enumerate(lines):
            try:
                line_bbox = draw.textbbox((0, 0), line, font=text_font)
                line_width = line_bbox[2] - line_bbox[0]
            except:
                # textbbox가 없는 경우 대략적인 계산
                line_width = len(line) * 15

            line_x = (canvas_width - line_width) // 2
            draw.text(
                (line_x, comment_y + (i * 40)),
                line,
                fill='#333333',
                font=text_font
            )

        # 이미지 저장
        canvas.save(output_path, quality=95)

        return output_path


if __name__ == "__main__":
    # 테스트
    generator = ResultImageGenerator()
    print("Result Image Generator 초기화 완료!")
