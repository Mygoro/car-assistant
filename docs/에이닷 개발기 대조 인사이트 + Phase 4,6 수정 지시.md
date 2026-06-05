 **작성 맥락**: SKT 에이닷+티맵 LLM 내비게이션 개발기(2025-10-31, duke74s)를 OTTO 설계와 대조한 결과 도출된 인사이트와, 그로부터 나온 즉시 적용 코드 수정 사항.

이 문서는 두 부분으로 나뉜다.

- **Part A — Claude Code 즉시 수정 지시** (실행 대상)
- **Part B — 인사이트 및 로드맵** (기록/참고 대상, 다큐멘팅 시스템이 보관)

---

# Part A — Claude Code 즉시 수정 지시

OTTO 시스템 프롬프트에 두 가지 규칙을 추가한다. 코드 로직 변경은 없고, `core/system_prompt_template.txt`만 수정한다.

## 수정 1 — STT 고유명사 보정을 Claude에 위임

### 배경

faster-whisper가 한국어 고유명사(장소명, 기술 용어, 브랜드명)를 오인식하는 문제가 알려진 리스크로 남아 있다. 에이닷은 이를 음소 유사성 + 도메인 지식 기반 POI 보정 모듈로 해결했다. OTTO는 별도 모듈 대신, 어차피 거치는 Claude가 문맥으로 보정하게 한다.

### 적용

`core/system_prompt_template.txt`에 다음 섹션을 추가한다 (## Tool use 섹션 근처):

```
## Speech recognition correction

The input transcript comes from speech-to-text and may contain recognition
errors, especially for Korean proper nouns — place names, brand names, and
technical terms.

- If a transcript token looks like a likely misrecognition, infer the intended
  word from context and proceed with the corrected interpretation.
- Use phonetic similarity and domain knowledge. Example: "광탄면 행복 복지센터"
  is almost certainly "광탄면 행정복지센터" (행복 ↔ 행정 phonetic similarity,
  복지센터 = public institution).
- For the user's recurring proper nouns (project names, tool names, frequent
  destinations), prefer the known correct form when a close match appears.
- When a correction materially changes the meaning of a command, briefly
  confirm in voice_response rather than acting silently. Example:
  voice_response "행정복지센터 말씀이신가요?" instead of routing immediately.
- Do not over-correct. If the transcript is already a valid, sensible word,
  leave it alone.
```

## 수정 2 — tool 결과 검증 / 환각 방지

### 배경

에이닷은 LLM + Rule Engine + Context Manager의 하이브리드로 POI 환각을 방지했다. OTTO는 tool 결과를 검증하는 층이 없어, Claude가 존재하지 않는 장소·수치를 지어낼 위험이 있다. 전시 데모에서 지어낸 주유소가 나오면 치명적. 규칙 엔진을 새로 만들기 전에, 시스템 프롬프트로 1차 방어한다.

### 적용

`core/system_prompt_template.txt`의 ## Absolute prohibitions 섹션에 다음 항목을 추가한다:

```
- Never invent places, addresses, coordinates, phone numbers, prices, fuel
  figures, distances, or business hours. Use ONLY values returned by a tool
  call. If a tool did not return a needed value, say you don't have it rather
  than producing a plausible-looking number.
- When citing a place from a search tool, use the exact name and address the
  tool returned. Do not paraphrase a place name into a different one.
- If a tool returns no results, say so. Do not fabricate a result to be helpful.
```

## 수정 3 (검토 필요) — Opus 라우팅 재고

### 배경

에이닷은 추론 모델(Opus급)을 실시간 내비에서 명시적으로 제외했다. 지연·비용 때문. OTTO의 intent 라우팅은 complex_reasoning → Opus로 두고 있는데, 운전 중 음성 응답에서 Opus 지연이 수용 가능한지 미검증.

### 지시

코드를 바로 바꾸지 말고, 다음을 측정해서 사용자에게 보고한다:

- complex_reasoning 경로(Opus)의 실제 first-token latency와 전체 응답 시간
- 동일 발화를 Sonnet으로 처리했을 때의 시간 비교

측정 결과를 보고 Opus 경로를 유지할지, Sonnet으로 통일할지 사용자가 결정한다. 이 수정은 측정 보고까지만 하고 코드 변경은 승인 후 진행한다.

## 검증

수정 1, 2 적용 후 다음으로 확인:

1. "광탄면 행복 복지센터 가는 길 알려줘" 류 발화 → Claude가 보정 후 확인 질문하는지 (수정 1)
2. tool 없이 "근처 주유소 알려줘" → Claude가 지어내지 않고 "위치 정보가 필요하다"거나 "검색 결과가 없다"고 답하는지 (수정 2)
3. 정상 발화 → 과잉 보정 없이 그대로 처리되는지

## 제약

- `core/system_prompt_template.txt`만 수정. 다른 파일 변경 없음.
- 기존 듀얼 출력 형식, tool use 규칙, voice/text 규칙은 유지하고 위 섹션만 추가.
- 수정 3은 측정·보고만. 코드 변경 금지.

---

# Part B — 인사이트 및 로드맵 (기록/참고)

SKT 에이닷 개발기와 OTTO 설계의 대조 분석. 전시 발표 자료 및 향후 로드맵 근거.

## B-1. 독립적으로 같은 결론에 도달한 설계 결정

OTTO의 핵심 설계 결정 다수가 SKT 상용 서비스 팀의 결론과 일치한다. 이는 OTTO 설계의 정당성을 뒷받침한다.

|항목|에이닷 (상용)|OTTO|일치|
|---|---|---|---|
|모델 전략|복합→중형, 단순→경량 하이브리드|trivial→Haiku, default→Sonnet|일치|
|추론 모델|실시간에서 제외|(재검토 대상)|부분|
|캐싱|시스템 프롬프트 분리, 85% 캐싱 효과|system+tools cache_control|일치|
|복합 의도|자체 NLU 단계별 분해|Claude tool_use 위임|접근 다름|
|맥락 유지|히스토리 + 요약 최적화(예정)|memory.md + 히스토리|일치|
|환각 방지|LLM+Rule+Context 하이브리드|(시스템 프롬프트 1차 방어 추가)|OTTO 보완|

## B-2. OTTO의 구조적 우위

- **의도 분해의 단순성**: 에이닷은 Intent 분석 → Function Classification → Parameter 추출을 단계별 모듈로 수작업 구현했다. OTTO는 이 분해를 Claude의 native tool_use에 위임해 파이프라인이 훨씬 단순하다.
- **범용성**: 에이닷은 내비게이션 특화. OTTO는 일정·메모·검색·차량 데이터를 포괄하는 범용 워크스페이스.
- **클라이언트 비용**: 에이닷은 티맵 앱에 내장. OTTO는 Discord 봇으로 클라이언트 코딩 0줄.

## B-3. OTTO가 보완해야 할 지점 (에이닷에서 배움)

1. **STT 보정** — Part A 수정 1로 1차 대응. 그 위에 Whisper initial_prompt에 자주 쓰는 고유명사 주입 병행.
2. **tool 결과 검증층** — Part A 수정 2로 시스템 프롬프트 1차 방어. 장기적으로는 에이닷의 Rule Engine처럼, Kakao/Hyundai 응답을 코드 레벨에서 검증하는 후처리 층을 고려. (예: Claude가 응답에 쓴 장소명이 실제 API 결과 목록에 있는지 대조)
3. **히스토리 요약 최적화** — 에이닷이 향후 과제로 꼽은 것. 차량 세션이 길어지면 토큰·할루시네이션 문제 발생. OTTO 로드맵에 "대화 히스토리 요약 압축" 추가.
4. **모호한 발화의 맥락 기반 명확화** — 에이닷 목표: "거기로 가자" → "방금 검색하신 ○○ 카페로 안내할까요?". OTTO도 되묻기보다 직전 맥락을 활용한 명확화로 개선 가능. (현재는 "모르면 모른다고 + 질문 1개" 수준)

## B-4. 전시 발표 프레이밍

> SKT가 에이닷+티맵으로 푼 문제와 OTTO에서 마주친 문제가 거의 동일했다. 모델 하이브리드 라우팅, 프롬프트 캐싱, 복합 의도 분해, 맥락 유지 — 상용 팀의 결정을 독립적으로 같은 방향으로 내렸다. 다만 그들이 자체 NLU 파이프라인으로 수작업한 의도 분해를, OTTO는 Claude tool use에 위임해 더 단순한 구조로 구현했다. 또한 에이닷은 내비 특화인 반면 OTTO는 일정·메모·검색·차량을 포괄하는 범용 어시스턴트다.

## B-5. 출처

- duke74s, "LLM 기반 내비게이션 에이전트 개발기: 에이닷과 함께 진화하는 대화형 모빌리티 AI", 2025-10-31.