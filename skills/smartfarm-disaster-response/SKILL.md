---
name: smartfarm-disaster-response
description: >
  FarmGuard 스마트팜 기상재해 대응 파이프라인을 구현할 때 사용하는 스킬.
  Use when implementing disaster classification, Farm Profile actuator/sensor
  filtering, KMA weather API (위경도→격자 변환), internal sensor alarm,
  LLM-as-Judge evaluation, edge-case test dataset, or Streamlit UI assembly.
  Triggers on: 한파, 폭염, 강풍, 대설, 재해 대응, 기상재해, 기상 알람, 알람 구현,
  Farm Profile, 장비 필터링, 구동기, 센서, 온습도, KMA API, 기상청 API, 점좌표,
  LLM-as-Judge, 정량 평가, edge case, FarmGuard, 스마트팜, 파이프라인 구현.
allowed-tools: Read, Write, Bash
---

# FarmGuard — SmartFarm Disaster Response

## 핵심 원칙

LLM이 해서는 안 되는 것: 재해 판정, 장비 보유 판단, 임계값 비교  
LLM이 해야 하는 것: 필터링 완료된 구조를 농가 언어로만 설명

```
사용자 질의
  → STEP 1 Farm Profile 로드
  → STEP 2 기상 API 호출 + 재해 임계값 판정  (결정론적)
  → STEP 3 구동기/센서 필터링               (결정론적)
  → STEP 4 내부 센서 알람 확인              (결정론적)
  → STEP 5 Claude 자연어 생성              (LLM — 여기만)
  → STEP 6 LLM-as-Judge 정량 평가          (결정론적)
```

## 기상 API 구현

→ Read `references/weather_api.py` — latlon_to_grid + KMA 단기예보 API 호출 전체

Farm Profile의 `location.lat` / `location.lon` → `latlon_to_grid()` → `nx, ny` 격자  
API 키 없을 때 → `get_mock_weather(scenario)` Fallback 사용

## 재해 판정 + 장비 필터링

→ Read `references/disaster_rules.py` — 임계값 테이블, MANUAL_ACTIONS, filter_actions_by_profile()

`filter_actions_by_profile()` 반환: `executable` / `always_required` / `missing_equipment` / `alternative_needed`  
Claude에게는 `executable`만 전달. `missing_equipment` 장비는 절대 언급 금지.

## 내부 센서 알람

→ Read `references/sensor_alarm.py` — 온습도 임계값, check_internal_alerts(), Streamlit polling 패턴

`farm_profile["sensors"]`에 `indoor_temp_humidity` 있어야 알람 활성화  
센서 미보유 → "육안 점검 권장" 메시지로 대체

## LLM-as-Judge 정량 평가

→ Read `references/eval_dataset.py` — 10개 테스트케이스 (normal 3 + edge_no_equip 3 + edge_extreme 2 + edge_compound 2)  
→ Run `scripts/run_judge.py` — precision / safety / citation 3지표 자동 집계

safety 실패(score ≤ 2) 0건 목표: 미보유 장비를 권장하면 safety = 실패

## 전체 파이프라인

→ Read `scripts/main_pipeline.py` — Chaining Workflow 조립 전체

## Farm Profile 샘플

→ Read `assets/farm_profile_sample.json` — Venlo 유리온실 완전 장비 샘플
