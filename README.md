# Claude Code Skills — 스마트팜 & 논문 작성

대형언어모델활용건축공학인공지능구현 기말 프로젝트로 제작한 **Claude Code Skill 2종**입니다.
각 스킬은 특정 작업 시 Claude가 자동으로 펼쳐보는 "전문 매뉴얼 + 도구 묶음"입니다.

---

## 수록 스킬

| 스킬 | 한 줄 설명 | 도메인 |
|------|-----------|--------|
| [`smartfarm-disaster-response`](skills/smartfarm-disaster-response) | 스마트팜 기상재해(한파·폭염·강풍·대설) 대응 파이프라인 구현 | 농업 AI |
| [`research-paper-assistant`](skills/research-paper-assistant) | 농업·AI 논문 작성 + 시계열 실험(누수 차단) 구현 | 논문 작성 |

각 스킬 폴더의 `README.md`에 담긴 내용과 사용법이 자세히 정리되어 있습니다.

---

## 디렉터리 구조

```
.
├── README.md                              ← 본 문서
├── .gitignore
└── skills/
    ├── smartfarm-disaster-response/
    │   ├── SKILL.md                       ← 스킬 진입점 (Claude가 먼저 읽음)
    │   ├── README.md                      ← 상세 설명 + 사용법
    │   ├── references/                    ← 핵심 로직 (→ Read로 펼쳐봄)
    │   ├── scripts/                       ← 실행 스크립트 (→ Run으로 실행)
    │   └── assets/                        ← 입력 스키마 샘플
    └── research-paper-assistant/
        ├── SKILL.md
        ├── README.md
        ├── assets/                        ← 논문 섹션 한국어 템플릿
        ├── references/                    ← 전처리·분리·5-fold CV
        └── scripts/                       ← 실험·시각화
```

---

## 설치 및 사용

원하는 스킬 폴더를 자신의 Claude Code 스킬 디렉터리에 복사하면 끝입니다.

```bash
# 전역 설치 (모든 프로젝트에서 사용)
cp -r skills/smartfarm-disaster-response ~/.claude/skills/
cp -r skills/research-paper-assistant   ~/.claude/skills/

# 또는 특정 프로젝트에만 설치
cp -r skills/research-paper-assistant <프로젝트>/.claude/skills/
```

Windows(PowerShell):

```powershell
Copy-Item skills\smartfarm-disaster-response $HOME\.claude\skills\ -Recurse
Copy-Item skills\research-paper-assistant   $HOME\.claude\skills\ -Recurse
```

설치 후 Claude Code에서 관련 요청을 하면 스킬이 **자동 로드**됩니다.

```
"한파 경보 상황에서 농가 대응 파이프라인 만들어줘"     → smartfarm-disaster-response
"스마트팜 센서 데이터로 온도 예측 논문 서론 써줘"      → research-paper-assistant
```

---

## 설계 원칙

두 스킬 모두 **"AI/통계가 틀리기 쉬운 지점에 명시적 규칙(울타리)을 박아둔다"**는 철학을 공유합니다.

- **smartfarm-disaster-response** — LLM이 재해 판정·장비 판단을 하지 못하게 코드로 분리.
  판단은 결정론적 코드가, 자연어 설명만 LLM이 담당.
- **research-paper-assistant** — 시계열 데이터 누수가 생기는 지점(무작위 분리, Test 포함 정규화)을
  분리 규칙(7:3 + 5-fold CV)으로 차단.

---

## 라이선스

교육·연구 목적 자유 사용. (MIT 권장)
