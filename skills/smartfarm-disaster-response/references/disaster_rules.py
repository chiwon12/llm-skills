"""재해 판정 임계값 + 농진청 매뉴얼 조치 + 장비 필터링 (결정론적)"""
from dataclasses import dataclass
from typing import Callable

@dataclass
class DisasterAlert:
    type: str; level: str; value: float; threshold: float; field: str

DISASTER_THRESHOLDS = {
    "한파": [
        {"level":"경보",   "field":"min_temp",   "op":"<=","value":-15.0},
        {"level":"주의보", "field":"min_temp",   "op":"<=","value":-12.0},
    ],
    "폭염": [
        {"level":"경보",   "field":"max_temp",   "op":">=","value":38.0},
        {"level":"주의보", "field":"max_temp",   "op":">=","value":33.0},
    ],
    "강풍": [
        {"level":"경보",   "field":"wind_speed", "op":">=","value":21.0},
        {"level":"주의보", "field":"wind_speed", "op":">=","value":14.0},
    ],
    "대설": [
        {"level":"경보",   "field":"snow_depth", "op":">=","value":20.0},
        {"level":"주의보", "field":"snow_depth", "op":">=","value": 5.0},
    ],
}
OPS: dict[str, Callable] = {"<=": lambda a,b: a<=b, ">=": lambda a,b: a>=b}

def classify_disasters(weather: dict) -> list[DisasterAlert]:
    alerts=[]
    for dtype, rules in DISASTER_THRESHOLDS.items():
        for rule in rules:
            raw=weather.get(rule["field"])
            if raw is None: continue
            try: val=float(str(raw).replace("cm","").strip())
            except ValueError: continue
            if OPS[rule["op"]](val, rule["value"]):
                alerts.append(DisasterAlert(dtype, rule["level"], val, rule["value"], rule["field"]))
                break
    return alerts

MANUAL_ACTIONS = {
    "한파": [
        {"action":"보온커튼 닫기 (일몰 전)",       "requires":"thermal_curtain",   "priority":1,"greenhouse":None,         "source":"농진청 재해 매뉴얼 p.12"},
        {"action":"온수난방 설정온도 2°C 상향",     "requires":"hot_water_heating", "priority":1,"greenhouse":None,         "source":"농진청 재해 매뉴얼 p.12"},
        {"action":"HAF팬 정지 (냉기 순환 방지)",    "requires":"haf_fan",           "priority":2,"greenhouse":None,         "source":"농진청 재해 매뉴얼 p.13"},
        {"action":"천창 완전 닫기",                 "requires":"roof_window",       "priority":1,"greenhouse":"venlo_glass","source":"농진청 재해 매뉴얼 p.12"},
        {"action":"측창 완전 닫기",                 "requires":"side_window",       "priority":1,"greenhouse":"venlo_glass","source":"농진청 재해 매뉴얼 p.12"},
        {"action":"다음날 오전 9시 이전 관수 완료", "requires":None,                "priority":3,"greenhouse":None,         "source":"농진청 재해 매뉴얼 p.14"},
    ],
    "폭염": [
        {"action":"차광커튼 전개 (50~70%)",         "requires":"shade_curtain",     "priority":1,"greenhouse":None,         "source":"농진청 재해 매뉴얼 p.22"},
        {"action":"천창 100% 개방",                 "requires":"roof_window",       "priority":1,"greenhouse":"venlo_glass","source":"농진청 재해 매뉴얼 p.22"},
        {"action":"환기팬 최대 가동",               "requires":"exhaust_fan",       "priority":1,"greenhouse":None,         "source":"농진청 재해 매뉴얼 p.22"},
        {"action":"포그시스템 가동 (≥32°C 기준)",   "requires":"fog_system",        "priority":1,"greenhouse":None,         "source":"농진청 재해 매뉴얼 p.23"},
        {"action":"HAF팬 연속 가동",                "requires":"haf_fan",           "priority":2,"greenhouse":None,         "source":"농진청 재해 매뉴얼 p.22"},
        {"action":"오전 9시 이전 관수 완료",        "requires":None,                "priority":2,"greenhouse":None,         "source":"농진청 재해 매뉴얼 p.23"},
        {"action":"오후 관수 금지",                 "requires":None,                "priority":1,"greenhouse":None,         "source":"농진청 재해 매뉴얼 p.23"},
    ],
    "강풍": [
        {"action":"천창·측창 완전 닫기",            "requires":"roof_window",       "priority":1,"greenhouse":"venlo_glass","source":"농진청 재해 매뉴얼 p.32"},
        {"action":"측창 완전 닫기",                 "requires":"side_window",       "priority":1,"greenhouse":"venlo_glass","source":"농진청 재해 매뉴얼 p.32"},
        {"action":"보온커튼 피복재 2차 고정",       "requires":"thermal_curtain",   "priority":2,"greenhouse":None,         "source":"농진청 재해 매뉴얼 p.32"},
        {"action":"HAF팬 정지 (부하 감소)",         "requires":"haf_fan",           "priority":2,"greenhouse":None,         "source":"농진청 재해 매뉴얼 p.33"},
        {"action":"지주대 및 고정 줄 점검",         "requires":None,                "priority":1,"greenhouse":None,         "source":"농진청 재해 매뉴얼 p.32"},
    ],
    "대설": [
        {"action":"천창 즉시 닫기",                 "requires":"roof_window",       "priority":1,"greenhouse":"venlo_glass","source":"농진청 재해 매뉴얼 p.42"},
        {"action":"온수난방 최대 가동 (제설 목적)", "requires":"hot_water_heating", "priority":1,"greenhouse":None,         "source":"농진청 재해 매뉴얼 p.42"},
        {"action":"보온커튼 유지 (열 보존)",        "requires":"thermal_curtain",   "priority":2,"greenhouse":None,         "source":"농진청 재해 매뉴얼 p.43"},
        {"action":"적설 하중 수시 확인 및 제설",    "requires":None,                "priority":1,"greenhouse":None,         "source":"농진청 재해 매뉴얼 p.42"},
    ],
}

def filter_actions_by_profile(disaster_type: str, farm_profile: dict) -> dict:
    owned=set(farm_profile.get("actuators",[])); sensors=set(farm_profile.get("sensors",[]))
    gh_type=farm_profile.get("greenhouse_type","")
    exe,always,miss,alt=[],[],set(),[]
    for item in sorted(MANUAL_ACTIONS.get(disaster_type,[]),key=lambda x:x["priority"]):
        req=item["requires"]; gh_req=item.get("greenhouse")
        if gh_req and gh_req not in gh_type: continue
        if req is None: always.append({"action":item["action"],"source":item["source"]})
        elif req in owned: exe.append({"action":item["action"],"source":item["source"]})
        else: miss.add(req); alt.append({"action":item["action"],"missing":req,"source":item["source"]})
    return {
        "executable":        exe,
        "always_required":   always,
        "missing_equipment": list(miss),
        "alternative_needed":alt,
        "sensor_warnings":   [f"{s} 미설치 → 관련 알람 비활성" for s in ["indoor_temp_humidity","wind_speed"] if s not in sensors],
    }
