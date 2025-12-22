"""
에겐/테토 분류 및 코멘트 생성 모듈
"""

import random


class AegenTetoClassifier:
    def __init__(self):
        """분류기 초기화"""
        self.aegen_comments = {
            'high': [
                "완벽한 에겐이에요! 🥰 너무너무 귀엽고 사랑스럽습니다!",
                "에겐 그 자체! 💕 포근하고 부드러운 느낌이 최고예요!",
                "진정한 에겐의 정석! ✨ 평화롭고 온화한 모습에 힐링됩니다!",
                "에겐 끝판왕! 🌸 너무 사랑스러워서 계속 보게 되네요!",
            ],
            'medium': [
                "에겐 스타일입니다! 🐱 귀엽고 차분한 매력이 넘쳐요!",
                "에겐 기질 확실해요! 💗 온순하고 사랑스러운 모습이에요!",
                "에겐 인증완료! 🎀 포근한 느낌이 정말 좋습니다!",
            ],
            'low': [
                "에겐 성향이 보여요! 귀여운 면이 돋보이네요!",
                "에겐에 가깝지만 테토의 활발함도 조금 보입니다!",
            ]
        }
        self.teto_comments = {
            'high': [
                "완벽한 테토입니다! 💪 늠름하고 듬직한 모습이 정말 멋지네요!",
                "이야... 진정한 테토의 위엄! 👑 카리스마가 넘쳐흐릅니다!",
                "대단한 테토예요! 🦁 활동량도 많아 보이고 정말 건강해 보입니다!",
                "완벽한 테토 포스! ⚡ 강인하고 아름다운 모습에 감탄이 나옵니다!",
            ],
            'medium': [
                "테토 기질이 보입니다! 💪 활발하고 에너지 넘치는 모습이 인상적이에요!",
                "테토 스타일이네요! 🌟 듬직한 면모가 돋보입니다!",
                "테토 확정! 💯 건강하고 활동적인 모습이 멋져요!",
            ],
            'low': [
                "약한 테토 기질이 보여요! 활동적인 면이 조금 보이네요!",
                "테토에 가깝지만 에겐의 귀여움도 살짝 보입니다!",
            ]
        }

    def classify(self, analysis_result):
        """
        분석 결과를 바탕으로 에겐/테토를 분류하고 코멘트를 생성합니다.

        Args:
            analysis_result: pet_analyzer의 분석 결과

        Returns:
            dict: 분류 결과, 점수, 코멘트
        """
        aegen_score = analysis_result['aegen_score']
        teto_score = analysis_result['teto_score']
        classification = analysis_result['classification']
        confidence = analysis_result['confidence']

        # 점수 정규화 (0-100 스케일)
        total_score = aegen_score + teto_score
        if total_score > 0:
            aegen_percentage = (aegen_score / total_score) * 100
            teto_percentage = (teto_score / total_score) * 100
        else:
            # 특징이 없으면 중립
            aegen_percentage = 50
            teto_percentage = 50

        # 퍼센트 기반 세밀한 코멘트 생성
        comment = self._get_comment_by_percentage(aegen_percentage)

        # 특징 설명 추가
        features_desc = self._generate_features_description(analysis_result)

        return {
            'classification': classification,
            'aegen_percentage': round(aegen_percentage, 1),
            'teto_percentage': round(teto_percentage, 1),
            'comment': comment,
            'features_description': features_desc,
            'raw_description': analysis_result['description']
        }

    def _get_comment_by_percentage(self, aegen_percentage):
        """
        에겐 퍼센트에 따라 세밀하고 다양한 코멘트를 반환합니다.

        Args:
            aegen_percentage: 에겐 퍼센트 (0-100)

        Returns:
            str: 해당 구간의 랜덤 코멘트
        """
        teto_percentage = 100 - aegen_percentage

        if aegen_percentage >= 90:
            # 에겐 90-100% (극도로 귀여운)
            comments = [
                "천상천하 유아독존! 연예인 해도 될 외모에요!",
                "완벽한 에겐입니다! 이보다 더 귀여울 순 없어요! 🥰",
                "세상 모든 귀여움을 다 가져간 비주얼! 반칙이에요!",
                "에겐 중의 에겐! 심장이 녹아내려요... 💕",
                "이 정도면 인스타그램 셀럽감! 찐 에겐입니다!",
                "천사가 따로 없네요! 순수함 그 자체에요!",
                "세상에서 가장 사랑스러운 모습! 완벽한 에겐!",
                "귀여움 과다 주의보! 보는 것만으로도 힐링돼요!",
                "이 정도면 에겐의 교과서! 완벽한 비주얼!",
                "애교 덩어리! 누가 봐도 에겐이에요!",
                "포근함이 느껴지는 완벽한 에겐 스타일!",
                "세상 모든 사랑을 받아야 할 외모! 진짜 에겐!",
            ]
            return random.choice(comments)

        elif aegen_percentage >= 70:
            # 에겐 70-90% (매우 귀여운)
            comments = [
                "츤데레같은 느낌! 수려한 외모에 도도하게 있을 것 같지만 반려자님께 항상 의지하고 있을 것 같아요!",
                "완전 사랑둥이! 귀여움이 가득한 스타일이에요!",
                "포근한 매력이 넘쳐나요! 진정한 에겐 스타일!",
                "애교쟁이! 보호본능을 자극하는 비주얼이에요!",
                "복슬복슬 귀여운 매력! 안아주고 싶은 비주얼!",
                "순수함이 가득! 천진난만한 에겐이에요!",
                "사랑스러움 폭발! 누구나 좋아할 스타일!",
                "귀요미 인증! 힐링되는 비주얼이에요!",
                "차분하면서도 사랑스러운 완벽한 에겐!",
                "보드라운 매력! 포근함이 느껴져요!",
            ]
            return random.choice(comments)

        elif aegen_percentage >= 50:
            # 에겐 50-70% (균형잡힌, 에겐 우세)
            comments = [
                "빙구미 가득한 느낌! 약간 도도함이 있는 것 같지만 반려자님께 항상 의지하고 있을 것 같아요!",
                "귀여움과 늠름함의 조화! 균형잡힌 매력이에요!",
                "에겐 기질이 강하지만 테토의 활발함도 있어요!",
                "귀엽지만 기품있는 스타일! 완벽한 조화!",
                "애교와 당당함을 동시에 가진 매력!",
                "사랑스러우면서도 자신감 있는 비주얼!",
                "귀여운데 의외로 활발할 것 같은 느낌!",
                "에겐 우세! 귀염과 씩씩함이 공존해요!",
                "포근하면서도 활기찬 매력!",
                "차분한 듯 활발한! 완벽한 밸런스!",
            ]
            return random.choice(comments)

        elif aegen_percentage >= 30:
            # 에겐 30-50% (균형잡힌, 테토 우세)
            comments = [
                "미공자와 같은 잘생쁨! 주인바라기에 충직함도 있을 것 같아요!",
                "테토지만 에겐의 매력도 있어요! 완벽한 조화!",
                "늠름하면서도 사랑스러운 독특한 매력!",
                "활동적이지만 귀여움도 놓치지 않았어요!",
                "씩씩하면서도 포근한 분위기!",
                "테토 우세! 하지만 애교도 만점!",
                "강인함 속에 숨겨진 다정함!",
                "잘생김과 귀여움의 완벽한 믹스!",
                "활발하면서도 온순한 매력!",
                "테토지만 츤데레 같은 매력이 있어요!",
            ]
            return random.choice(comments)

        elif aegen_percentage >= 10:
            # 에겐 10-30% (매우 활동적)
            comments = [
                "살짝쿵 에겐감성 섞인 테토예요! 늠름함 속에 가려진 세심함이 있을 것 같아요!",
                "완전 테토! 활기차고 에너지 넘쳐요!",
                "늠름한 비주얼! 테토의 카리스마!",
                "활동적이고 씩씩한 진정한 테토!",
                "강인한 외모에 활발한 성격! 찐 테토!",
                "에너지 폭발! 운동을 좋아할 것 같아요!",
                "당당하고 자신감 넘치는 테토 스타일!",
                "테토 인증! 늠름함이 가득해요!",
                "활발하고 건강미 넘치는 비주얼!",
                "테토지만 가끔 애교도 부릴 것 같아요!",
            ]
            return random.choice(comments)

        else:
            # 에겐 0-10% (극도로 활동적)
            comments = [
                "완벽한 테토예요! 너무 늠름하고 멋있는데요?",
                "테토 중의 테토! 카리스마가 넘쳐흐릅니다!",
                "진정한 테토의 위엄! 완벽한 비주얼!",
                "이보다 더 테토일 순 없어요! 찐 테토!",
                "늠름함의 정석! 강인한 매력 가득!",
                "완전 운동선수 스타일! 활동량 MAX!",
                "세상 모든 에너지를 가진 테토!",
                "테토의 교과서! 완벽한 활동파!",
                "카리스마 폭발! 누가 봐도 테토!",
                "건강미와 활력이 넘치는 완벽한 테토!",
                "늠름하고 강인한 진정한 테토의 모습!",
                "테토 끝판왕! 에너지가 느껴져요!",
            ]
            return random.choice(comments)

    def _generate_features_description(self, analysis_result):
        """특징 설명을 생성합니다."""
        features = analysis_result['features']
        description = analysis_result['description']

        # 주요 특징 추출
        traits = []

        full_text = description.lower()
        for feature_text in features.values():
            # 문자열인 경우에만 lower() 호출 (ensemble 정보는 딕셔너리이므로 제외)
            if isinstance(feature_text, str):
                full_text += " " + feature_text.lower()

        # 키워드 매칭
        if any(word in full_text for word in ['strong', 'powerful', 'muscular']):
            traits.append('강인함')
        if any(word in full_text for word in ['cute', 'adorable', 'sweet']):
            traits.append('귀여움')
        if any(word in full_text for word in ['active', 'energetic', 'playful']):
            traits.append('활발함')
        if any(word in full_text for word in ['calm', 'lazy', 'relaxed']):
            traits.append('차분함')
        if any(word in full_text for word in ['beautiful', 'elegant', 'graceful']):
            traits.append('우아함')
        if any(word in full_text for word in ['brave', 'confident', 'bold']):
            traits.append('용감함')

        if traits:
            return ', '.join(traits) + '이(가) 돋보입니다!'
        else:
            return '독특한 매력이 있습니다!'


if __name__ == "__main__":
    # 테스트
    classifier = AegenTetoClassifier()
    test_result = {
        'description': 'a strong and powerful dog',
        'features': {
            'q1': 'yes, very strong',
            'q2': 'dignified',
            'q3': 'active and energetic',
            'q4': 'not lazy',
            'q5': 'muscular dog'
        },
        'aegen_score': 5,
        'teto_score': 1,
        'classification': 'aegen',
        'confidence': 4
    }
    result = classifier.classify(test_result)
    print("테스트 결과:", result)
