---
name: research-paper-assistant
description: >
  스마트팜·농업 도메인 논문을 작성하거나 AI/ML 실험 코드를 구현할 때 사용하는 스킬.
  Use when: writing or reviewing paper sections (introduction, methods, results,
  discussion), implementing sensor time-series models, designing ablation studies,
  generating result tables for publication, or improving academic writing.
  Triggers on: 논문 작성, 논문 수정, introduction 작성, 서론, 관련 연구,
  연구 방법, 실험 설계, 모델링, 시계열, LSTM, 회귀, 분류, 이상탐지, 재현성,
  train test split, data leakage, k-fold, cross validation, ablation study,
  결과 테이블, figure, 시각화, 논문 영작, academic writing, paper writing.
allowed-tools: Read, Write, Bash
---

# Research Paper Assistant

## 논문 섹션별 구조 (5개 섹션 — 농학·공학 표준)

**Introduction** — 깔때기 구조(점진적 논리 전개): ① 배경(3~5문장) → ② 기존 연구·한계(Related Work 흡수) → ③ Gap → ④ 기여 3~4 bullet → ⑤ 논문 구성  
**Materials & Methods (M&M)** — ① 시스템 개요 → ② 데이터셋(결측 처리 방법 명시 필수) → ③ 피처 → ④ 데이터 분리 → ⑤ 모델 → ⑥ 학습 설정·평가지표  
**Results** — ① 메인 테이블(CV 점수 + Test 점수 병기) → ② 그림 → ③ Ablation study  
**Discussion** — ① 해석 → ② 기존 연구 비교 → ③ 한계 → ④ 향후 방향  
**Conclusion** — ① 연구 요약 → ② 핵심 기여 재확인 → ③ 확장 방향 (간결하게)

→ Read `assets/paper_template_ko.md` — 섹션별 한국어 문장 템플릿 전체  
→ Read `assets/paper_template_en.md` — 영문 저널 투고용 영어 템플릿 (동일 5섹션 구조)

## 데이터 전처리 및 분리

→ Read `references/data_preprocessing.py` — 결측 처리, 클리핑, 피처, time_based_split, get_timeseries_cv

**분리 전략**:
- Train:Test = **7:3** 시간 기준 고정 분리 (`time_based_split(train_ratio=0.70)`)
- Validation은 고정 분리 없이 Train 내 **TimeSeriesSplit 5-fold CV** 사용
- Scaler는 Train 전용 `fit`, Val/Test는 `transform`만 (leakage 방지)

**절대 금지**: `train_test_split(df, random_state=42)` → 시계열 누수 발생

## 실험 코드 실행

→ Run `scripts/run_experiment.py` — 재현성 보장 파이프라인 (7:3 분리 + 5-fold CV)  
→ Run `scripts/evaluate_and_plot.py` — 평가지표 계산 + 논문용 그림 생성

## 결과 테이블 형식

CV MAE/RMSE/R² (5-fold 평균) + Test MAE/RMSE/R² 를 병기  
Best 값 **bold** | ↓ 낮을수록 / ↑ 높을수록 표기 | Baseline 항상 포함 | ± std 권장

## 작성 체크리스트

- [ ] 결측 처리 방법 Methods에 명시 (점 결측: 보간 / 구간: 제거)
- [ ] Train:Test = 7:3 시간 기준 분리 명시
- [ ] Val = TimeSeriesSplit 5-fold CV on Train 명시
- [ ] Scaler fit은 Train 전용 명시
- [ ] `set_seed(42)` 코드 최상단 + `random_state=42` 모든 sklearn 함수
- [ ] Ablation study 포함 (각 구성마다 5-fold CV 수행)
- [ ] 평가지표 수식 포함 (MAE/RMSE/R² 또는 F1/P/R)
