"""
LLM-as-Judge 평가 데이터셋 — 10개 테스트케이스
normal(3) + edge_no_equip(3) + edge_extreme(2) + edge_compound(2)
"""

EVAL_DATASET = [
    # ══════════════════════════════════════════════════════════════════
    # Normal Cases — 전체 장비 보유, 일반 기상
    # ══════════════════════════════════════════════════════════════════
    {
        "id": "TC-01", "category": "normal",
        "description": "한파경보 + Venlo 전체 장비 보유",
        "input": {
            "farm_profile": {
                "name": "완전장비 농가", "crops": ["방울토마토"],
                "greenhouse_type": "venlo_glass",
                "sensors":   ["indoor_temp_humidity", "outdoor_temp", "wind_speed"],
                "actuators": ["thermal_curtain", "hot_water_heating", "haf_fan",
                              "roof_window", "side_window"],
            },
            "weather":     {"min_temp": -16.0, "max_temp": 2.0},
            "sensor_data": {"indoor_temp_humidity": {"temp": 10.0, "humidity": 70.0}},
        },
        "expected": {
            "must_include": ["보온커튼", "온수난방", "닫기"],
            "must_exclude": ["포그시스템", "차광커튼"],
            "reference": "보온커튼 닫기, 온수난방 2°C 상향, HAF팬 정지, 천창·측창 닫기 [출처: 농진청 재해 매뉴얼]",
        },
        "scoring_weights": {"precision": 0.4, "safety": 0.4, "citation": 0.2},
    },
    {
        "id": "TC-02", "category": "normal",
        "description": "폭염경보 + 전체 장비 보유",
        "input": {
            "farm_profile": {
                "name": "파프리카 농가", "crops": ["파프리카"],
                "greenhouse_type": "venlo_glass",
                "sensors":   ["indoor_temp_humidity", "solar_radiation"],
                "actuators": ["shade_curtain", "exhaust_fan", "fog_system",
                              "haf_fan", "roof_window"],
            },
            "weather":     {"min_temp": 26.0, "max_temp": 39.0},
            "sensor_data": {"indoor_temp_humidity": {"temp": 34.0, "humidity": 55.0}},
        },
        "expected": {
            "must_include": ["차광커튼", "환기팬", "관수"],
            "must_exclude": ["보온커튼", "온수난방"],
            "reference": "차광커튼 전개, 환기팬 최대, 천창 100% 개방, 포그시스템 가동, 오전 9시 이전 관수",
        },
        "scoring_weights": {"precision": 0.4, "safety": 0.4, "citation": 0.2},
    },
    {
        "id": "TC-03", "category": "normal",
        "description": "강풍주의보 + 전체 장비 보유",
        "input": {
            "farm_profile": {
                "name": "딸기 농가", "crops": ["딸기"],
                "greenhouse_type": "venlo_glass",
                "sensors":   ["indoor_temp_humidity", "wind_speed"],
                "actuators": ["roof_window", "side_window", "thermal_curtain", "haf_fan"],
            },
            "weather":     {"min_temp": 15.0, "max_temp": 22.0, "wind_speed": 16.0},
            "sensor_data": {"indoor_temp_humidity": {"temp": 22.0, "humidity": 65.0}},
        },
        "expected": {
            "must_include": ["천창", "닫기", "점검"],
            "must_exclude": ["포그시스템", "온수난방"],
            "reference": "천창·측창 완전 닫기, 보온커튼 2차 고정, HAF팬 정지, 지주대 점검",
        },
        "scoring_weights": {"precision": 0.4, "safety": 0.4, "citation": 0.2},
    },

    # ══════════════════════════════════════════════════════════════════
    # Edge Cases: 장비 미보유 — must_exclude 안전성 검증 핵심
    # ══════════════════════════════════════════════════════════════════
    {
        "id": "TC-04", "category": "edge_no_equip",
        "description": "한파경보 + 보온커튼·난방 완전 미보유 (소규모 비닐)",
        "input": {
            "farm_profile": {
                "name": "소규모 비닐농가", "crops": ["상추"],
                "greenhouse_type": "vinyl_single",
                "sensors":   ["indoor_temp_humidity"],
                "actuators": ["haf_fan"],         # 최소 장비
            },
            "weather":     {"min_temp": -14.0, "max_temp": 0.0},
            "sensor_data": {"indoor_temp_humidity": {"temp": 5.0, "humidity": 80.0}},
        },
        "expected": {
            "must_include": ["대체", "임시"],
            "must_exclude": ["보온커튼", "온수난방", "천창", "측창"],
            "reference": "HAF팬 정지. 보온커튼·난방 미보유 → 비닐 이중 피복 임시 조치 권장",
        },
        "scoring_weights": {"precision": 0.2, "safety": 0.6, "citation": 0.2},
    },
    {
        "id": "TC-05", "category": "edge_no_equip",
        "description": "폭염주의보 + 포그·차광커튼 미보유",
        "input": {
            "farm_profile": {
                "name": "기본장비 농가", "crops": ["토마토"],
                "greenhouse_type": "venlo_glass",
                "sensors":   ["indoor_temp_humidity", "solar_radiation"],
                "actuators": ["exhaust_fan", "haf_fan", "roof_window"],
            },
            "weather":     {"min_temp": 24.0, "max_temp": 35.0},
            "sensor_data": {"indoor_temp_humidity": {"temp": 33.0, "humidity": 60.0}},
        },
        "expected": {
            "must_include": ["환기팬", "천창", "관수"],
            "must_exclude": ["포그시스템", "차광커튼"],
            "reference": "환기팬 최대, 천창 100% 개방, 오전 9시 이전 관수. 차광망 임시 설치 권장",
        },
        "scoring_weights": {"precision": 0.3, "safety": 0.5, "citation": 0.2},
    },
    {
        "id": "TC-06", "category": "edge_no_equip",
        "description": "대설주의보 + 온수난방 미보유 + 온습도 센서 미설치",
        "input": {
            "farm_profile": {
                "name": "센서부족 농가", "crops": ["상추"],
                "greenhouse_type": "venlo_glass",
                "sensors":   [],                  # 센서 없음 → 알람 비활성
                "actuators": ["thermal_curtain", "roof_window"],
            },
            "weather":     {"min_temp": -5.0, "max_temp": 0.0, "snow_depth": "7"},
            "sensor_data": {},
        },
        "expected": {
            "must_include": ["보온커튼", "천창", "제설", "센서"],
            "must_exclude": ["온수난방"],
            "reference": "천창 닫기, 보온커튼 유지, 적설 하중 제설. 온습도 센서 미설치 → 육안 점검 권장",
        },
        "scoring_weights": {"precision": 0.3, "safety": 0.4, "citation": 0.3},
    },

    # ══════════════════════════════════════════════════════════════════
    # Edge Cases: 극단 기상 — 장비 대응 한계 검증
    # ══════════════════════════════════════════════════════════════════
    {
        "id": "TC-07", "category": "edge_extreme",
        "description": "태풍 수준 강풍 30m/s — 장비 대응 한계",
        "input": {
            "farm_profile": {
                "name": "남부 첨단농가", "crops": ["딸기"],
                "greenhouse_type": "venlo_glass",
                "sensors":   ["indoor_temp_humidity", "wind_speed"],
                "actuators": ["roof_window", "side_window", "thermal_curtain", "haf_fan"],
            },
            "weather":     {"min_temp": 18.0, "max_temp": 25.0, "wind_speed": 30.0},
            "sensor_data": {"indoor_temp_humidity": {"temp": 22.0, "humidity": 68.0}},
        },
        "expected": {
            "must_include": ["닫기", "점검", "대피"],
            "must_exclude": [],
            "reference": "장비 대응 한계 명시. 천창·측창 닫기, 구조 안전 점검, 인명 대피 우선",
        },
        "scoring_weights": {"precision": 0.2, "safety": 0.6, "citation": 0.2},
    },
    {
        "id": "TC-08", "category": "edge_extreme",
        "description": "폭염 극한값 42°C + 내부 온도 이미 36°C 초과",
        "input": {
            "farm_profile": {
                "name": "남부 파프리카", "crops": ["파프리카"],
                "greenhouse_type": "venlo_glass",
                "sensors":   ["indoor_temp_humidity", "solar_radiation"],
                "actuators": ["shade_curtain", "exhaust_fan", "fog_system",
                              "haf_fan", "roof_window"],
            },
            "weather":     {"min_temp": 30.0, "max_temp": 42.0},
            "sensor_data": {"indoor_temp_humidity": {"temp": 37.0, "humidity": 50.0}},
        },
        "expected": {
            "must_include": ["차광커튼", "포그시스템", "환기"],
            "must_exclude": ["보온커튼", "온수난방"],
            "reference": "차광커튼·포그·환기 최대. 내부 37°C → 긴급 대응. 수분 스트레스 모니터링",
        },
        "scoring_weights": {"precision": 0.4, "safety": 0.4, "citation": 0.2},
    },

    # ══════════════════════════════════════════════════════════════════
    # Edge Cases: 복합 재해 — 상충 조치 처리 검증
    # ══════════════════════════════════════════════════════════════════
    {
        "id": "TC-09", "category": "edge_compound",
        "description": "한파경보 + 대설경보 동시 발령",
        "input": {
            "farm_profile": {
                "name": "중부 농가", "crops": ["방울토마토"],
                "greenhouse_type": "venlo_glass",
                "sensors":   ["indoor_temp_humidity", "outdoor_temp"],
                "actuators": ["thermal_curtain", "hot_water_heating",
                              "roof_window", "haf_fan"],
            },
            "weather":     {"min_temp": -16.0, "max_temp": -2.0, "snow_depth": "22"},
            "sensor_data": {"indoor_temp_humidity": {"temp": 7.0, "humidity": 75.0}},
        },
        "expected": {
            "must_include": ["보온커튼", "난방", "제설", "적설"],
            "must_exclude": [],
            "reference": "한파: 보온커튼·난방 상향. 대설: 난방 최대(제설 목적)·적설 하중 점검. 우선순위 병기 필수",
        },
        "scoring_weights": {"precision": 0.4, "safety": 0.3, "citation": 0.3},
    },
    {
        "id": "TC-10", "category": "edge_compound",
        "description": "폭염 + 강풍 동시 (창 열기 vs 닫기 상충)",
        "input": {
            "farm_profile": {
                "name": "상충 테스트 농가", "crops": ["파프리카"],
                "greenhouse_type": "venlo_glass",
                "sensors":   ["indoor_temp_humidity", "wind_speed"],
                "actuators": ["roof_window", "side_window", "exhaust_fan",
                              "shade_curtain", "fog_system"],
            },
            "weather":     {"min_temp": 25.0, "max_temp": 37.0, "wind_speed": 15.0},
            "sensor_data": {"indoor_temp_humidity": {"temp": 34.0, "humidity": 58.0}},
        },
        "expected": {
            "must_include": ["차광커튼", "강풍"],
            "must_exclude": [],
            "reference": "강풍 우선: 천창 부분 제한 개방(완전 개방 금지). 차광커튼 차선 대응. 상충 조치 명시 필수",
        },
        "scoring_weights": {"precision": 0.3, "safety": 0.4, "citation": 0.3},
    },
]
