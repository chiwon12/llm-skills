"""
내부 센서 알람 모듈 — 온습도 센서 중심
Farm Profile의 sensors 필드 확인 후 알람 활성화 결정 (결정론적)
"""
from dataclasses import dataclass


@dataclass
class SensorAlert:
    alert_id:  str
    sensor:    str    # "indoor_temp_humidity" | "co2" | ...
    field:     str    # "temp" | "humidity" | "co2"
    message:   str
    measured:  float
    threshold: float
    level:     str    # "warning" | "critical"


# ── 내부 센서 임계값 ─────────────────────────────────────────────────
# 온도·습도: indoor_temp_humidity 센서 하나에서 temp, humidity 두 값 출력
INTERNAL_THRESHOLDS: list[dict] = [
    # 온도 경보 (critical)
    {"id": "temp_critical_high", "sensor": "indoor_temp_humidity", "field": "temp",
     "op": ">=", "value": 36.0, "level": "critical",
     "msg": "🚨 내부 온도 위험 (≥36°C) → 즉시 환기·차광·포그 가동"},
    # 온도 주의 (warning)
    {"id": "temp_warn_high",     "sensor": "indoor_temp_humidity", "field": "temp",
     "op": ">=", "value": 32.0, "level": "warning",
     "msg": "⚠️  내부 온도 상승 (≥32°C) → 환기팬·차광커튼 확인"},
    {"id": "temp_warn_low",      "sensor": "indoor_temp_humidity", "field": "temp",
     "op": "<=", "value":  8.0, "level": "warning",
     "msg": "⚠️  저온 장해 위험 (≤8°C) → 보온커튼·난방 가동"},
    {"id": "temp_critical_low",  "sensor": "indoor_temp_humidity", "field": "temp",
     "op": "<=", "value":  4.0, "level": "critical",
     "msg": "🚨 동해 위험 (≤4°C) → 긴급 가온 조치"},
    # 습도 경보
    {"id": "hum_high",           "sensor": "indoor_temp_humidity", "field": "humidity",
     "op": ">=", "value": 90.0, "level": "warning",
     "msg": "⚠️  과습 위험 (≥90%) → 환기팬 가동·차광커튼 개방"},
    {"id": "hum_low",            "sensor": "indoor_temp_humidity", "field": "humidity",
     "op": "<=", "value": 40.0, "level": "warning",
     "msg": "⚠️  건조 위험 (≤40%) → 포그시스템 또는 관수"},
    # CO₂
    {"id": "co2_high",           "sensor": "co2",                  "field": "co2",
     "op": ">=", "value": 1500, "level": "warning",
     "msg": "⚠️  CO₂ 과잉 (≥1500ppm) → 환기 즉시"},
    {"id": "co2_low",            "sensor": "co2",                  "field": "co2",
     "op": "<=", "value":  400, "level": "warning",
     "msg": "⚠️  CO₂ 부족 (≤400ppm) → CO₂ 발생기 또는 환기 감소"},
]

OPS = {"<=": lambda a, b: a <= b, ">=": lambda a, b: a >= b}


def check_internal_alerts(sensor_data: dict, farm_profile: dict) -> dict:
    """
    내부 센서 알람 확인 (결정론적)

    Args:
        sensor_data: {
            "indoor_temp_humidity": {"temp": 34.5, "humidity": 85.0},
            "co2": {"co2": 1600},
            ...
        }
        farm_profile: Farm Profile JSON (sensors 필드 포함)

    Returns:
        {
            "active_alerts":   [SensorAlert, ...],   # 발동된 알람
            "inactive_sensors":[str, ...],           # 미보유/미설치 센서
            "critical_count":  int,                  # 긴급 알람 수
        }
    """
    owned_sensors = set(farm_profile.get("sensors", []))
    active, inactive = [], []

    for rule in INTERNAL_THRESHOLDS:
        sensor_key = rule["sensor"]

        # 센서 미보유 → 알람 비활성 + 경고 메시지
        if sensor_key not in owned_sensors:
            if sensor_key not in inactive:
                inactive.append(sensor_key)
            continue

        # 센서 데이터 없음 → 스킵
        sensor_reading = sensor_data.get(sensor_key)
        if sensor_reading is None:
            continue

        # 필드 값 추출 (dict 또는 단일 값 모두 지원)
        if isinstance(sensor_reading, dict):
            val = sensor_reading.get(rule["field"])
        else:
            val = sensor_reading

        if val is None:
            continue

        if OPS[rule["op"]](float(val), rule["value"]):
            active.append(SensorAlert(
                alert_id=rule["id"], sensor=sensor_key,
                field=rule["field"], message=rule["msg"],
                measured=float(val), threshold=rule["value"],
                level=rule["level"],
            ))

    return {
        "active_alerts":    active,
        "inactive_sensors": inactive,
        "critical_count":   sum(1 for a in active if a.level == "critical"),
    }


def format_sensor_summary(result: dict) -> str:
    """알람 결과를 농가용 요약 텍스트로 변환"""
    lines = []
    if not result["active_alerts"] and not result["inactive_sensors"]:
        return "✅ 내부 센서 정상 — 이상 없음"
    for alert in sorted(result["active_alerts"],
                         key=lambda a: 0 if a.level == "critical" else 1):
        lines.append(f"{alert.message} (측정값: {alert.measured})")
    for s in result["inactive_sensors"]:
        lines.append(f"📡 {s} 미설치 → 해당 알람 비활성 (육안 점검 권장)")
    return "\n".join(lines)
