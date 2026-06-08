# research-paper-assistant

스마트팜·농업 도메인 AI 논문을 작성하고 실험 코드를 구현하는 스킬

두 가지 역할을 한 스킬에서 수행합니다:
**① 논문 작성 지원**(섹션·문장 템플릿, 표·그림 자동 생성)과
**② 실험 엄밀성 보장**(시계열 데이터 누수 차단, 재현성).

---

## 이 스킬이 담고 있는 것

```
research-paper-assistant/
├── SKILL.md                       # 스킬 진입점
├── README.md                      # 본 문서
├── assets/
│   └── paper_template_ko.md       # 6개 섹션(서론~결론) 한국어 문장 템플릿
├── references/
│   └── data_preprocessing.py      # 결측 처리·피처·시간분리·5-fold CV
└── scripts/
    ├── run_experiment.py          # 재현성 실험 파이프라인 (7:3 + 5-fold CV)
    └── evaluate_and_plot.py       # 평가지표 계산 + 논문용 Figure 생성
```

| 파일 | 핵심 내용 | 역할 |
|------|-----------|------|
| `paper_template_ko.md` | 서론·관련연구·방법·결과·토론·결론 빈칸 템플릿 + Table 양식 | 빈 화면 대신 채워 넣을 문장 골격 제공 |
| `data_preprocessing.py` | `time_based_split(0.70)`, `get_timeseries_cv(5)` | 결측 처리·클리핑·피처 엔지니어링·시계열 분리 |
| `run_experiment.py` | `set_seed(42)`, `run_regression_experiment()`, `run_ablation_study()` | Train 5-fold CV + Test(30%) 성능 보고 |
| `evaluate_and_plot.py` | `plot_prediction()`, `plot_ablation()`, `plot_feature_importance()` | Table 1·2 / Figure 2·3·4 자동 생성 |

---

## 기둥 ① — 논문을 어떻게 작성하는가

빈 화면이 아니라 **빈칸 채우기 템플릿**에서 시작합니다.
섹션 구조는 농학·공학 논문 표준인 **5개 섹션**입니다 (Related Work는 Introduction에 흡수).

```
1. Introduction          배경 → 기존 연구·한계 → Gap → 기여 (깔때기 구조)
2. Materials & Methods    데이터셋(결측 처리 명시) → 피처 → 분리 → 모델 → 지표
3. Results               Table 1(성능 비교) + Table 2(Ablation) + Figure
4. Discussion            해석 → 기존 연구 비교 → 한계 → 향후 연구
5. Conclusion            연구 요약 + 핵심 기여 재확인 + 확장 방향
```

실험 코드를 돌리면 논문에 바로 넣을 수 있는 산출물이 자동 생성됩니다:

- **Table 1** 모델 성능 비교 (MAE/RMSE/R²/MAPE)
- **Table 2** Ablation Study
- **Figure 2** 예측 vs 실제 (시계열 + 산점도)
- **Figure 3** Ablation 막대그래프
- **Figure 4** Feature Importance Top-15

## 기둥 ② — 실험 엄밀성 (데이터 누수 차단)

> **"시계열 데이터는 미래를 훔쳐보면 안 된다 (No Data Leakage)."**

| 규칙 | 이유 |
|------|------|
| Train:Test = **7:3 시간 기준** 분리 | 앞 70%로 학습, 뒤 30%(미래)로 평가 → 실제 운영과 동일 |
| Val = Train 내 **TimeSeriesSplit 5-fold CV** | 고정 Val을 떼지 않아 데이터 효율↑ + 성능 분산 확인 |
| Scaler는 **Train 전용 `fit`** | Test 포함해 정규화하면 그것도 미래 정보 누수 |
| `set_seed(42)` + `random_state=42` | 재현 가능해야 심사자가 검증 가능 |

**절대 금지**: `train_test_split(df, random_state=42)` — 무작위 분리는 시계열 누수 발생

---

## 사용 방법

### 1) Claude Code 스킬로 사용 (권장)

이 폴더를 `~/.claude/skills/` 또는 프로젝트의 `.claude/skills/` 아래에 둡니다.

```
프로젝트/
└── .claude/
    └── skills/
        └── research-paper-assistant/   ← 이 폴더 전체를 복사
```

그 후 Claude Code에서 아래처럼 요청하면 스킬이 자동 로드됩니다.

```
"스마트팜 센서 데이터로 온도 예측 논문 서론 써줘"
"시계열 데이터 누수 없이 train/test 분리하는 코드 만들어줘"
"Ablation study 표랑 Figure 생성해줘"
```

(트리거 키워드: 논문 작성, 서론, 연구 방법, 실험 설계, 시계열, 재현성,
train test split, data leakage, k-fold, cross validation, ablation study,
결과 테이블, figure, 시각화 등)

### 2) 코드를 직접 실행

```bash
# 의존성 설치
pip install pandas numpy scikit-learn matplotlib

# 실험 실행 (7:3 분리 + 5-fold CV)
python scripts/run_experiment.py

# 평가지표 + 논문용 그림 생성
python scripts/evaluate_and_plot.py
```

`run_experiment.py`는 `results/regression_results.json`에 결과를 저장하므로
같은 seed로 재실행하면 동일 결과가 재현되는지 검증할 수 있습니다.

---

## 작성 체크리스트

- [ ] 결측 처리 방법 Methods에 명시 (점 결측: 보간 / 구간: 제거)
- [ ] Train:Test = 7:3 시간 기준 분리 명시
- [ ] Val = TimeSeriesSplit 5-fold CV on Train 명시
- [ ] Scaler `fit`은 Train 전용 명시
- [ ] `set_seed(42)` 최상단 + `random_state=42` 모든 sklearn 함수
- [ ] Ablation study 포함 (각 구성마다 5-fold CV)
- [ ] 평가지표 수식 포함 (MAE/RMSE/R² 또는 F1/P/R)
