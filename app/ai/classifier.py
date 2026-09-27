"""
에겐/테토 분류와 코멘트 생성.

코멘트 = 유형 한 줄 + (닮은 품종의 알려진 성향 × 사진 속 자세) 한 줄.
유형 경계(80/60/40/20)는 웹의 src/content/types.json 과 같다.
"""
import random

# 에겐 비율 하한 → 유형
TYPES = [
    (80, 'pure-aegen', '순수 에겐', [
        "고요함 그 자체, 보고만 있어도 마음이 느긋해지는 순수 에겐이에요 🌙",
        "차분하고 신중한 매력이 가득한 순수 에겐이에요 🌙",
        "서두르지 않는 여유가 사진 가득 담긴 순수 에겐이에요 🌙",
    ]),
    (60, 'aegen', '에겐', [
        "차분함 속에 은은한 매력이 있는 에겐이에요 😌",
        "조용히 지켜보다 천천히 다가오는 에겐 타입이에요 😌",
        "편안하고 신중한 분위기가 먼저 보이는 에겐이에요 😌",
    ]),
    (40, 'balanced', '균형', [
        "차분함과 활발함을 반반 품은 균형 타입이에요 ⚖️",
        "쉴 땐 느긋하고 놀 땐 신나는, 균형 잡힌 타입이에요 ⚖️",
        "에겐과 테토의 매력을 고루 가진 균형 타입이에요 ⚖️",
    ]),
    (20, 'teto', '테토', [
        "호기심과 에너지가 먼저 달려 나가는 테토예요 🔥",
        "활발하고 적극적인 매력이 돋보이는 테토예요 🔥",
        "새로운 건 먼저 확인해야 직성이 풀리는 테토 타입이에요 🔥",
    ]),
    (-1, 'pure-teto', '순수 테토', [
        "야성미 넘치는 에너지 덩어리, 순수 테토예요 ⚡",
        "힘 있고 적극적인 모습이 사진 밖으로 넘쳐 나는 순수 테토예요 ⚡",
        "가만히 있는 게 더 어려운 순수 테토예요 ⚡",
    ]),
]

BREED_MIN_PROB = 0.35   # 이보다 낮으면 '닮은 품종'을 말하지 않는다
KNOWN_CUT = 0.3         # 품종 성향 점수 -1(차분) ~ +1(활발)
POSE_CUT = 0.25         # 자세 점수 -1(차분) ~ +1(활발)


def _eul(word):
    """'을/를' — 마지막 글자에 받침이 있으면 '을'."""
    ch = word[-1]
    if '가' <= ch <= '힣' and (ord(ch) - 0xAC00) % 28:
        return '을'
    return '를'


def _level(v, cut):
    return 'calm' if v <= -cut else 'active' if v >= cut else 'mid'


BREED_LINES = {
    ('calm', 'calm'): "{b} 닮은 느긋한 얼굴에, 자세까지 편안해요.",
    ('calm', 'active'): "{b} 닮은 순한 인상인데, 사진 속에선 신나는 순간이 담겼어요!",
    ('calm', 'mid'): "{b} 닮은 순한 인상이에요.",
    ('active', 'calm'): "{b} 닮은 에너지 넘치는 얼굴이지만, 지금은 잠시 쉬는 중이네요.",
    ('active', 'active'): "{b} 닮은 활발한 인상에 자세까지 에너지가 가득해요!",
    ('active', 'mid'): "{b} 닮은 씩씩한 인상이에요.",
    ('mid', 'calm'): "{b} 닮은 얼굴에, 사진 속 자세는 차분해요.",
    ('mid', 'active'): "{b} 닮은 얼굴에, 사진 속 자세는 활발해요.",
    ('mid', 'mid'): "{b} 닮은 얼굴이에요.",
}
MIXED_POSE = {
    'calm': "사진 속 자세는 차분하고 편안해요.",
    'active': "사진 속 자세에서 에너지가 느껴져요.",
    'mid': "쉬는 모습과 노는 모습 사진을 각각 넣어 보면 더 재미있어요.",
}


class AegenTetoClassifier:
    def classify(self, r):
        aegen = float(r['aegen_percentage'])
        _, slug, name, lines = next(t for t in TYPES if aegen >= t[0])
        headline = random.choice(lines)

        top = r['breeds'][0]
        pose = _level(r['pose'], POSE_CUT)
        if top['prob'] >= BREED_MIN_PROB:
            b = top['ko'] + _eul(top['ko'])
            detail = BREED_LINES[(_level(top['known'], KNOWN_CUT), pose)].format(b=b)
            breed_match = {'key': top['key'], 'ko': top['ko'], 'prob': round(top['prob'] * 100, 1)}
        else:
            species = '고양이' if r['species'] == 'cat' else '강아지'
            detail = f"여러 품종의 매력이 섞인 {species} 얼굴이에요. {MIXED_POSE[pose]}"
            breed_match = None

        return {
            'classification': 'aegen' if aegen >= 50 else 'teto',
            'aegen_percentage': round(aegen, 1),
            'teto_percentage': round(100 - aegen, 1),
            'type': slug,
            'type_name': name,
            'comment': f"{headline} {detail}",
            'breed_match': breed_match,
            'species': r['species'],
            'pose': round(r['pose'], 2),
        }
