"""
LLM-as-Judge 자동 평가 실행기
정량 평가: precision / safety / citation 3지표 + overall 1~5점
"""
import anthropic, json, statistics, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "references"))
from eval_dataset import EVAL_DATASET

JUDGE_SYSTEM = """당신은 스마트팜 기상재해 대응 AI 응답을 평가하는 전문 심사위원입니다.
반드시 JSON만 반환하세요. 다른 텍스트(설명, 마크다운 코드블록)는 절대 포함하지 마세요."""

JUDGE_TEMPLATE = """
[농가 프로필]
- 이름: {farm_name} | 작물: {crops} | 온실: {greenhouse}
- 보유 구동기: {owned}
- 보유 센서: {sensors}

[기상 상황]: {weather}
[내부 센서]: {sensor_data}

[AI 응답]
{ai_response}

[채점 기준]
must_include (포함 필수): {must_include}
must_exclude (포함 금지): {must_exclude}
모범 답안: {reference}

점수 기준:
5: must_include 전부 + must_exclude 없음 + 출처 명시
4: must_include 80%+ + must_exclude 없음
3: must_include 60% 또는 출처 없음
2: must_exclude 1개 (Safety 실패)
1: must_exclude 2개+ 또는 위험 조치

세부 지표:
- precision: must_include 포함 비율 (0.0~1.0)
- safety: must_exclude 없음=1.0 / 1개=0.5 / 2개+=0.0
- citation: [출처:...] 포함=1.0 / 없음=0.0

다음 JSON만 반환:
{{"overall_score": 1~5, "precision": 0.0~1.0, "safety": 0.0~1.0, "citation": 0.0~1.0,
  "found_must_include": ["실제 포함된 키워드"],
  "found_must_exclude": ["실제 포함된 금지 키워드"],
  "reason": "한 문장 근거"}}
"""


def run_judge(ai_response: str, tc: dict) -> dict:
    client = anthropic.Anthropic()
    farm   = tc["input"]["farm_profile"]
    user   = JUDGE_TEMPLATE.format(
        farm_name   = farm["name"],
        crops       = ", ".join(farm["crops"]),
        greenhouse  = farm["greenhouse_type"],
        owned       = ", ".join(farm.get("actuators", [])),
        sensors     = ", ".join(farm.get("sensors", [])),
        weather     = json.dumps(tc["input"]["weather"], ensure_ascii=False),
        sensor_data = json.dumps(tc["input"].get("sensor_data", {}), ensure_ascii=False),
        ai_response = ai_response,
        must_include= ", ".join(tc["expected"]["must_include"]),
        must_exclude= ", ".join(tc["expected"]["must_exclude"]) or "없음",
        reference   = tc["expected"]["reference"],
    )
    resp = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=512,
        system=JUDGE_SYSTEM,
        messages=[{"role": "user", "content": user}],
    )
    raw = resp.content[0].text.strip()
    if raw.startswith("```"): raw = raw.split("```")[1].lstrip("json").strip()
    return json.loads(raw)


def run_full_evaluation(pipeline_fn, dataset=None) -> dict:
    """
    전체 평가 실행
    pipeline_fn: (farm_profile, weather, sensor_data) → {"response": str}
    """
    if dataset is None: dataset = EVAL_DATASET
    results = []

    for tc in dataset:
        print(f"  [{tc['id']}] {tc['description'][:45]}...", end=" ", flush=True)
        try:
            out = pipeline_fn(
                farm_profile=tc["input"]["farm_profile"],
                weather=tc["input"]["weather"],
                sensor_data=tc["input"].get("sensor_data", {}),
            )
            ai_resp = out.get("response", "")
        except Exception as e:
            ai_resp = f"[파이프라인 오류: {e}]"
        try:
            score = run_judge(ai_resp, tc)
        except Exception as e:
            score = {"overall_score": 0, "precision": 0, "safety": 0,
                     "citation": 0, "found_must_include": [], "found_must_exclude": [],
                     "reason": f"Judge 오류: {e}"}

        results.append({**tc, "score": score,
                        "ai_response_preview": ai_resp[:80]})
        flag = "⚠️ " if score.get("safety", 1) < 1.0 else "✅"
        print(f"{flag} {score['overall_score']}점 "
              f"(P={score.get('precision',0):.1f} S={score.get('safety',0):.1f} C={score.get('citation',0):.1f})")

    return _aggregate(results)


def _aggregate(results: list) -> dict:
    all_scores = [r["score"]["overall_score"] for r in results]
    by_cat = {}
    for r in results:
        by_cat.setdefault(r["category"], []).append(r["score"]["overall_score"])

    return {
        "results": results,
        "summary": {
            "total":    len(results),
            "mean":     round(statistics.mean(all_scores), 2),
            "stdev":    round(statistics.stdev(all_scores), 2) if len(all_scores)>1 else 0,
            "min":      min(all_scores), "max": max(all_scores),
            "by_category": {c: {"mean": round(statistics.mean(s), 2), "n": len(s)}
                            for c, s in by_cat.items()},
            "safety_failures": [r["id"] for r in results
                                if r["score"].get("safety", 1) < 1.0],
        },
    }


def print_report(eval_result: dict):
    s = eval_result["summary"]
    print(f"\n{'='*60}")
    print(f"  FarmGuard LLM-as-Judge 정량 평가 결과")
    print(f"{'='*60}")
    print(f"  총 케이스: {s['total']}  |  평균: {s['mean']} ± {s['stdev']}  |  범위: {s['min']}~{s['max']}")
    print()
    for cat, stat in s["by_category"].items():
        bar = "█" * int(stat["mean"])
        print(f"  {cat:25s} {bar} {stat['mean']:.1f} (n={stat['n']})")
    print()
    if s["safety_failures"]:
        print(f"  ⚠️  Safety 실패: {s['safety_failures']}")
    else:
        print(f"  ✅  Safety 실패 0건 (미보유 장비 권장 없음)")
    print(f"{'='*60}")


if __name__ == "__main__":
    def dummy(farm_profile, weather, sensor_data):
        return {"response": "보온커튼 닫기, 온수난방 가동 [출처: 농진청 재해 매뉴얼 p.12]"}
    result = run_full_evaluation(dummy)
    print_report(result)
    with open("eval_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
