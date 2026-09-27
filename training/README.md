# 모델 재학습 기록 (2026-09)

기존 가중치·데이터셋이 소실되어 공개 데이터셋과 사람 검수로 커스텀 모델을 다시 만들었다.

## 정의
- **에겐** = 차분·신중·매력적 / **테토** = 활발·적극·야성적
- 라벨 기준(설계): 품종 성향 > 차분한 모습 > 나이. 실제 사람 판정은 "어리고 귀여울수록 에겐" 쪽으로 기울었다 (검수 결과).

## 데이터
- [Oxford-IIIT Pet Dataset](https://www.robots.ox.ac.uk/~vgg/data/pets/) 7,349장, 고양이 12종 + 개 25종 (Parkhi et al., 2012), **CC BY-SA 4.0**
- 받은 경로: HuggingFace `timm/oxford-iiit-pet` (같은 라이선스)
- 사람 검수 300장 (품종별 8장 + 무작위, 자동 라벨은 숨기고 판정) — 데이터·검수 결과는 저장소에 넣지 않는다

## 파이프라인 (`training/`)
| 순서 | 스크립트 | 내용 |
|---|---|---|
| 1 | `extract_parquet.py` | parquet → `images/<Breed>_<n>.jpg` |
| 2 | `label_oxford.py` + `breed_temperament.csv` | 품종 성향(0.6) + CLIP 모습(0.3) + CLIP 나이(0.1) 약한 라벨 |
| 3 | `review_server.py` | 정답 세트 300장 검수 화면 (127.0.0.1 전용) |
| 4 | `gold_stats.py`, `learnability.py` | 자동 라벨 vs 사람 판정 일치도, 사람 판정의 학습 가능성(5-fold CV) |
| 5 | `train_pipeline.py` | 240장으로 취향 모델(CLIP ViT-L/14 + 신호) → 의사 라벨 6,262장 → ResNet50 10 epoch |
| 6 | `holdout_list.py`, `eval_service.py` | 홀드아웃 60장을 실제 서비스 경로로 평가 |
| 7 | `calibrate.py` | 온도 보정 T (240장으로 적합) |

## 결과 (홀드아웃 60장, 학습에 쓰지 않음)
| 항목 | 값 |
|---|---|
| 서비스 앙상블 / 커스텀 ResNet | **78.3%** (47/60, 95% 66~87%) |
| BLIP 단독 | 51.7% |
| 찍기(다수 클래스) | 51.7% |
| 자동 규칙 라벨 vs 사람 | 53.7% |
| 온도 보정 T | 3.078 — ECE 0.173 → 0.075, 정확도 불변 |

표본이 60장이라 구간이 넓다. 이 수치는 "사람 1명의 판정과 얼마나 일치하는가"이며 반려동물의 실제 성격을 잰 것이 아니다.

## 가중치
`trained_model_v2.pth` (ResNet50, fc=2, 0=aegen 1=teto) 는 git 에 넣지 않고 GitHub Release 에 첨부한다. 서비스는 `MODEL_TEMPERATURE` 환경변수로 보정값을 받는다.
