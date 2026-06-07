# 사용자 컨텍스트

## 기본
- 호칭: 없음 (이름·호칭 부르지 않고 바로 본론)
- 차량: 현대 아반떼 (차량 API 제공값 = 잔여 주행거리·주행거리뿐, 연료%·위치 없음)
- 소속: 연세대 UIC, Creative Technology Management(CTM) 전공, 영어강의 환경

## 현재 학기 (2026-1)  ※학기마다 갱신
- 수강: AI Agents, ISM, RDQM, IT Foundation, Freshman Writing, 기독교와세계문화 (+비교과)
- 수업: 월·화·수·목 (송도 국제캠퍼스, 항상 차로 통학)

## 운전 패턴
- 주유 기준: 잔여주행거리 150km 이하 시 주유
- 주 운전 상황: ① 월~목 통학 ② 여자친구 픽업·드롭 ③ 원거리 이동
- 내비: TMAP 상시 사용

## 관심사 / 진행 중
- car-assistant(차량용 음성봇) 직접 개발 중 — 이 봇 자체
- 강의 녹음 자동화 파이프라인 운영
- 음성 AI·MCP 생태계 전반에 관심

## 페르소나 힌트
- 말투: 존댓말, simple and polite — 리액션·수식 없이 필요한 정보만 간결하게
- 여자친구는 이름 대신 "여자친구"로 호칭

## 응답 개인화 힌트
- 운전 중 되묻기 최소화: 명확화는 꼭 필요할 때만, 아니면 합리적으로 가정하고 진행한 뒤 가정을 한 줄로 고지

<!--
유지 규칙 (build_system_prompt가 주입 전 HTML 주석을 제거하므로 이 메모는 모델에 가지 않음):
- 민감 정보(거주지·동행인·식이 제약 등)는 이 파일이 아니라 core/memory.local.md에 [개인전용] 태그로 둔다. 이 파일은 커밋해도 안전한 비민감 정보만 유지.
- 말투(존댓말)·소스 라우팅·출력 형식은 system_prompt_template.txt가 담당 → 여기 중복 금지.
- 길이 예산 ≤50줄. 휘발성 진행상태("Phase X 중")는 박지 말 것.
- 전시 데모: OTTO_PROFILE=exhibition 으로 실행 → 오버레이 미로드 + [개인전용] 제거.
-->

<!-- stt-hints (Whisper 고유명사 보정용 한 줄. build가 주석을 제거하므로 LLM엔 안 가고
STT initial_prompt에만 병합됨. 학기·관심사 바뀌면 본문과 함께 여기도 갱신):
stt-hints: AI Agents, ISM, RDQM, IT Foundation, Freshman Writing, 기독교와세계문화, 송도 국제캠퍼스, 아반떼, TMAP, 여자친구
-->
