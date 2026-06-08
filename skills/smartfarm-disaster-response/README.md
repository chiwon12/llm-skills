# smartfarm-disaster-response

FarmGuard — 스마트팜 기상재해(한파·폭염·강풍·대설) 대응 파이프라인 구현 스킬

LLM에게 재해 판정·장비 판단을 **시키지 않고**, 결정론적 코드가 모든 판정을 끝낸 뒤
LLM은 "필터링된 대응책을 농가 언어로 설명"하는 역할만 하도록 설계된 스킬입니다.

---

## 이 스킬이 담고 있는 것

```
smartfarm-disaster-response/
├── SKILL.md                          # 스킬 진입점 (Claude가 가장 먼저 읽음)
├── README.md                         # 본 문서
├── references/                       # 핵심 로직 (Claude가 → Read로 펼쳐봄)
│   ├── weather_api.py                # KMA 단기예보 API + 위경도→격자 변환
│   ├── disaster_rules.py             # 재해 임계값 판정 + 농가별 장비 필터링
│   ├── sensor_alarm.py               # 내부 온습도 센서 알람
│   └── eval_dataset.py               # LLM-as-Judge 10개 테스트케이스
├── scripts/                          # 실행 스크립트 (Claude가 → Run으로 실행)
│   ├── main_pipeline.py              # Chaining Workflow 전체 조립
│   └── run_judge.py                  # 정량 평가 자동 집계
└── assets/
    └── farm_profile_sample.json      # Farm Profile 입력 스키마 샘플
```

| 파일 | 핵심 함수 | 역할 |
|------|-----------|------|
| `weather_api.py` | `latlon_to_grid(lat, lon)`, `get_weather_forecast()`, `get_mock_weather()` | 농가 위경도 점좌표 → 기상청 격자(nx, ny) 변환 후 단기예보 호출 |
| `disaster_rules.py` | `classify_disasters()`, `filter_actions_by_profile()` | 임계값 if/else 판정 + 보유 장비 기준 대응책 4종 분류 |
| `sensor_alarm.py` | `check_internal_alerts()`, `simulate_sensor_data()` | `sensors[]` 보유 시에만 온습도·CO₂ 알람 활성화 |
| `eval_dataset.py` | `EVAL_DATASET` | normal 3 + edge_no_equip 3 + edge_extreme 2 + edge_compound 2 |
| `run_judge.py` | `run_judge()`, `run_full_evaluation()` | Precision / Safety / Citation 3지표 자동 채점 |

---

## 핵심 설계 원칙

> **"LLM에게 판단을 시키지 않는다 — 판단은 코드가, 말하기는 LLM이."**

```
사용자 질의
  → STEP 1  Farm Profile 로드            (결정론적)
  → STEP 2  기상 API 호출 + 재해 판정     (결정론적)
  → STEP 3  구동기/센서 장비 필터링       (결정론적)
  → STEP 4  내부 센서 알람 확인           (결정론적)
  → STEP 5  Claude 자연어 생성            (LLM — 여기서만)
  → STEP 6  LLM-as-Judge 정량 평가        (결정론적)
```

- 임계값 비교·재해 판정은 `if`문이 100% 정확 → LLM 환각 배제
- 농가가 **보유한 장비(executable)만** Claude에 전달, 미보유 장비는 언급 금지
- "안전하다"를 주장이 아니라 **Safety 지표 0건**으로 증명

---

## 사용 방법

### 1) Claude Code 스킬로 사용 (권장)

이 폴더를 `~/.claude/skills/` 또는 프로젝트의 `.claude/skills/` 아래에 두면 자동 인식됩니다.

```
프로젝트/
└── .claude/
    └── skills/
        └── smartfarm-disaster-response/   ← 이 폴더 전체를 복사
```

그 후 Claude Code에서 아래와 같은 요청을 하면 스킬이 자동 로드됩니다.

```
"한파 경보 상황에서 박농부 농가 대응 파이프라인 만들어줘"
"기상청 API 위경도 격자 변환 코드 구현해줘"
"LLM-as-Judge로 재해 대응 응답 정량 평가하고 싶어"
```

(트리거 키워드: 한파·폭염·강풍·대설, 재해 대응, Farm Profile, 장비 필터링,
KMA API, 점좌표, LLM-as-Judge, edge case, FarmGuard 등)

### 2) 코드를 직접 실행

```bash
# 의존성 설치
pip install anthropic requests python-dotenv

# API 키 설정 (생성용)
set ANTHROPIC_API_KEY=sk-ant-...      # Windows
export ANTHROPIC_API_KEY=sk-ant-...   # macOS/Linux

# 전체 파이프라인 실행
python scripts/main_pipeline.py

# 정량 평가 (10개 테스트케이스)
python scripts/run_judge.py
```

기상청 API 키가 없으면 `get_mock_weather(scenario)` Fallback이 동작하므로
키 없이도 한파경보/폭염경보/복합재해 등 시나리오로 테스트할 수 있습니다.

---

## 입력 — Farm Profile 스키마

```json
{
  "farm_id": "farm_001",
  "name": "박농부 농가",
  "location": { "lat": 36.35, "lon": 127.38, "nx": 67, "ny": 100, "region": "대전" },
  "greenhouse_type": "venlo_glass",
  "crops": ["방울토마토"],
  "sensors":   ["indoor_temp_humidity", "outdoor_temp", "soil_moisture"],
  "actuators": ["roof_window", "side_window", "haf_fan"]
}
```

- `sensors[]`에 `indoor_temp_humidity`가 있어야 온습도 알람이 켜집니다.
- `actuators[]`에 없는 장비는 Claude가 절대 추천하지 않습니다.

---

## 평가 지표 (LLM-as-Judge)

| 지표 | 측정 | 통과 기준 |
|------|------|-----------|
| Precision | 필수 조치(must_include) 포함 비율 | 높을수록 좋음 |
| Safety | 미보유 장비(must_exclude) 미언급 | **0건 = 1.0 (목표)** |
| Citation | `[출처:...]` 명시 여부 | 포함 = 1.0 |

채점 모델: `claude-haiku-4-5-20251001` / 생성 모델: `claude-sonnet-4-5-20251001`
