"""
FarmGuard Chaining Workflow
결정론적 5단계 파이프라인 + LLM 자연어 생성
"""
import anthropic, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "references"))
from weather_api import get_weather_forecast
from disaster_rules import classify_disasters, filter_actions_by_profile
from sensor_alarm import check_internal_alerts, format_sensor_summary

SYSTEM_PROMPT = """당신은 스마트팜 기상재해 대응 AI 어시스턴트입니다.

절대 규칙:
1. executable 목록의 조치만 권장한다. missing_equipment 장비는 절대 언급하지 않는다.
2. alternative_needed 항목은 대체 방법을 제안한다. RAG 컨텍스트가 있으면 우선 활용.
3. 모든 조치에 [출처: source 필드] 형태로 출처를 명시한다.
4. sensor_warnings가 있으면 마지막에 별도 안내한다.
5. 응답은 우선순위 순 체크리스트 (① ② ③...) 형식으로 작성한다."""

def load_farm_profile(farm_id: str, assets_dir: str | None = None) -> dict:
    if assets_dir is None:
        assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
    with open(os.path.join(assets_dir, f"{farm_id}.json"), encoding="utf-8") as f:
        return json.load(f)

def run_farmguard_pipeline(
    farm_id: str | None = None,
    farm_profile: dict | None = None,
    weather: dict | None = None,
    sensor_data: dict | None = None,
    api_key: str | None = None,
) -> dict:
    """
    FarmGuard Chaining Workflow

    STEP 1: Farm Profile 로드
    STEP 2: 기상 API 호출 (결정론적)
    STEP 3: 재해 판정 (결정론적)
    STEP 4: 장비/센서 필터링 (결정론적)
    STEP 5: 내부 센서 알람 (결정론적)
    STEP 6: Claude 자연어 생성 (LLM)
    """
    # STEP 1
    if farm_profile is None:
        farm_profile = load_farm_profile(farm_id)

    # STEP 2
    if weather is None:
        api_key = api_key or os.environ.get("KMA_API_KEY", "")
        weather = get_weather_forecast(
            farm_profile["location"]["lat"],
            farm_profile["location"]["lon"],
            api_key,
        )

    # STEP 3 (결정론적)
    alerts = classify_disasters(weather)
    if not alerts:
        sensor_result = check_internal_alerts(sensor_data or {}, farm_profile)
        return {
            "alerts": [], "filtered_actions": {},
            "response": "현재 발령된 기상재해 특보가 없습니다.\n" +
                        format_sensor_summary(sensor_result),
            "sensor_result": sensor_result,
        }

    # STEP 4 (결정론적)
    all_filtered = {a.type: filter_actions_by_profile(a.type, farm_profile) for a in alerts}

    # STEP 5 (결정론적)
    sensor_result = check_internal_alerts(sensor_data or {}, farm_profile)
    sensor_summary = format_sensor_summary(sensor_result)

    # STEP 6 (LLM)
    client = anthropic.Anthropic()
    alert_list = [{"유형": a.type, "단계": a.level, "측정값": f"{a.value} (기준: {a.threshold})"}
                  for a in alerts]
    user_msg = f"""
[농가] {farm_profile['name']} | 작물: {', '.join(farm_profile['crops'])} | {farm_profile['greenhouse_type']}

[발령 재해]
{json.dumps(alert_list, ensure_ascii=False, indent=2)}

[장비 필터링 결과] ← 이것만 참고하여 응답
{json.dumps(all_filtered, ensure_ascii=False, indent=2)}

[내부 센서 현황]
{sensor_summary}

우선순위 체크리스트를 작성해 주세요.
"""
    resp = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=1024,
        system=SYSTEM_PROMPT, messages=[{"role": "user", "content": user_msg}],
    )
    return {
        "alerts":          alerts,
        "filtered_actions": all_filtered,
        "response":        resp.content[0].text,
        "sensor_result":   sensor_result,
    }

if __name__ == "__main__":
    result = run_farmguard_pipeline(
        farm_id="farm_sample",
        sensor_data={"indoor_temp_humidity": {"temp": 34.0, "humidity": 88.0}, "co2": {"co2": 1600}},
    )
    for a in result["alerts"]:
        print(f"🚨 {a.type} {a.level}: {a.value}")
    print("\n" + result["response"])
