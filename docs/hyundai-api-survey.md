# Hyundai API Survey

## 조사 일시
2026-05-26

## 인증 환경

| 항목 | 상태 |
|---|---|
| Portal 가입 | 완료 |
| Bluelink 연동 | 완료 |
| 본인 API key 보유 | yes |
| 본인 차량 모델 및 연식 | [확인 필요] |

---

## 공식 Hyundai Developers Portal 개요

- URL: https://developers.hyundai.com
- **한국 전용** 플랫폼 (공식 FAQ 명시: "국내 커넥티드카 데이터만 제공")
- 제공 API 카테고리 5종

| 카테고리 | 설명 |
|---|---|
| 제원정보 API | 브랜드, 모델, 트림, 색상, 옵션 |
| 운행정보 API | 경로, 시간, 속도 (시동 ON~OFF 구간) |
| 주행거리 API | 총 누적 거리, 잔여 주행거리 |
| 차량상태 API | 최근 주차 위치, 연료/배터리 상태 |
| 운전습관 API | 90일 기반 안전운전 점수 |

출처: https://developers.hyundai.com/web/v1/hyundai/data_api

---

## 인증 방식

### OAuth 2.0 Authorization Code Flow (3단계)

```
# 1. 로그인 인증 요청
GET /oauth/authorize
  ?client_id=...
  &redirect_uri=...
  &response_type=code
  &state=...
→ Hyundai 통합 계정 로그인 페이지 표시

# 2. 사용자 차량 접근 권한 동의 (consent 필수)

# 3. Authorization Code → Token 교환
POST /oauth/token
  grant_type=authorization_code (초기) | refresh_token (갱신)
  Authorization: Basic {base64(client_id:client_secret)}

# 이후 모든 API 호출
Authorization: Bearer {access_token}
```

| 항목 | 상태 |
|---|---|
| 토큰 유효 기간 | [확인 필요] 포털 로그인 후 확인 |
| 토큰 갱신 방법 | refresh_token grant |
| Rate limit 정확한 수치 | [확인 필요] 비공개, developers@hyundai.com 문의 필요 |

출처: https://developers.hyundai.com/web/v1/hyundai/guide_api

---

## 가용 API 매트릭스

| 카테고리 | 항목 | 가용 | 호출 방법 (Portal 경로) | 응답 예시 | 제한 |
|---|---|---|---|---|---|
| 차량 상태 | 연료 잔여 주행거리 (DTE) | **yes** | `/specification/data/status_dte` | `{"dte": {"value": 450, "unit": 1}}` | 일별 제한 (수치 미공개) |
| 차량 상태 | EV 배터리 잔량 | **yes (EV/PHEV)** | `/specification/data/status_evbattery` | `{"evStatus": {"batteryStatus": 80}}` | 상동 |
| 차량 상태 | EV 충전 상태 | **yes (EV/PHEV)** | `/specification/data/status_evcharging` | `{"evStatus": {"batteryCharge": false, "batteryPlugin": 0}}` | 상동 |
| 차량 상태 | 연료 경고등 | **yes** | `/specification/data/statuswarning_lowfuellight` | `{"lowFuelLight": false}` | 상동 |
| 차량 상태 | 연료 잔량 (리터/%) | [확인 필요] | 포털 Sample Test로 확인 필요 | — | — |
| 차량 상태 | 시동 상태 (ON/OFF) | [확인 필요] | 포털 Sample Test로 확인 필요 | — | — |
| 차량 상태 | 도어 잠금 상태 | [확인 필요] | 포털 Sample Test로 확인 필요 | — | — |
| 차량 상태 | 12V 배터리 상태 | [확인 필요] | 포털 Sample Test로 확인 필요 | — | — |
| 위치 정보 | 최근 주차 위치 (GPS) | **yes** | 차량상태 API 내 포함 | `{"lat": 37.xxx, "lng": 127.xxx}` | 지하 주차장 미지원 가능 |
| 위치 정보 | 실시간 위치 | [확인 필요] | 별도 location endpoint | — | 지하 신호 없음 |
| 주행 기록 | 누적 주행거리 | **yes** | 주행거리 API | `{"odometer": 12345}` | 상동 |
| 주행 기록 | 운행 이력 (경로/시간/속도) | **yes** | 운행정보 API | 시동 ON~OFF 단위 구간 | 상동 |
| 주행 기록 | 평균 연비 | [확인 필요] | 운행정보 API 내 가능성 있음 | — | — |
| 운전습관 | 안전운전 점수 | **yes** | 운전습관 API | 90일 집계 | — |
| 원격 제어 | 시동 | [확인 필요] | 포털에 데이터 API만 명시됨, 제어 API 별도 확인 필요 | — | — |
| 원격 제어 | 공조 제어 | [확인 필요] | 상동 | — | — |
| 원격 제어 | 도어 잠금/해제 | [확인 필요] | 상동 | — | — |
| 알림/진단 | 타이어 공기압 경고 | **yes** | 차량상태 API 내 | `{"tirePressureLampAll": false}` | 경고등 수준 (정확한 수치 아님) |
| 알림/진단 | 에러 코드 / 정비 알림 | [확인 필요] | 포털 Sample Test로 확인 필요 | — | — |

> 출처: https://developers.hyundai.com, https://github.com/Hacksore/bluelinky (EU/USA 응답 구조 참고)

---

## 응답 Latency 및 실시간성

| 모드 | 동작 | Latency | 배터리 영향 |
|---|---|---|---|
| 캐시 조회 | Hyundai 클라우드 서버에서 마지막 저장 데이터 반환 | ~1-3초 (추정) | 없음 |
| 강제 갱신 | 차량에 직접 명령 → 차량이 응답 | 5-30초 (추정) | 12V 배터리 소모 |

- **권장 폴링 간격**: 30분 (배터리·rate limit 절약)
- **지하 주차장**: 셀룰러 신호 약하면 강제 갱신 실패 가능성 있음. 캐시 데이터는 마지막 통신 시점 값 유지.
- 강제 갱신 성공 여부는 차량 안테나 수신 상태에 따라 다름.

---

## 비공식 라이브러리 평가 (hyundai_kia_connect_api)

| 항목 | 상태 |
|---|---|
| 라이브러리 | `hyundai-kia-connect-api` (PyPI) |
| GitHub | https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api |
| 한국 Region 지원 | **미지원** (Issue #701, "not planned"으로 종료) |
| EU/USA 지원 | 광범위 지원 (lock/unlock, climate, 위치, 상태 등) |
| Windows 10 동작 | 확인됨 (Discussion #987) |

**결론**: 한국 사용자는 이 라이브러리 직접 사용 불가. 공식 Hyundai Developers Portal API를 직접 호출해야 함.

출처:
- https://github.com/Hyundai-Kia-Connect/kia_uvo/issues/701
- https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api/discussions/987

---

## Windows Python 호출 가능 여부

**가능** — 공식 포털 API는 표준 HTTP REST이므로 Python `requests` 라이브러리로 호출 가능.

```python
import requests

# 토큰 발급
token_resp = requests.post(
    "https://prd.kr-ccapi.hyundai.com/api/v1/user/oauth2/token",  # [확인 필요] 실제 endpoint
    headers={"Authorization": f"Basic {base64_credentials}"},
    data={
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": redirect_uri
    }
)
access_token = token_resp.json()["access_token"]

# 차량 상태 조회 (예시, 실제 endpoint는 포털 규격서 확인 필요)
status_resp = requests.get(
    "https://prd.kr-ccapi.hyundai.com/api/v1/spa/vehicles/{vehicle_id}/status",
    headers={"Authorization": f"Bearer {access_token}"}
)
print(status_resp.json())
```

> **주의**: 위 base URL 및 endpoint 경로는 역분석 자료 기반 추정. 포털 규격서의 실제 URL로 교체 필요.

---

## 전시 데모 활용 가능성 평가

### P0 (반드시 시연 가능한 것)

- **누적 주행거리 조회**: 주행거리 API 가용 확인됨. 숫자 시각화로 임팩트 있음.
- **연료/배터리 잔여 주행거리 (DTE)**: `status_dte` 확인됨. "앞으로 450km 갈 수 있어요" 같은 자연어 응답 가능.
- **운행 이력 (오늘 어디 갔는지)**: 운행정보 API 확인됨. 시동 ON~OFF 구간 이력 제공.

### P1 (가능하면 시연)

- **EV 배터리 % + 충전 상태**: 차량이 EV/PHEV인 경우. 시각적으로 명확한 데이터.
- **타이어 공기압 경고**: 경고등 수준이지만 "타이어 이상 없음" 확인은 가능.
- **안전운전 점수 (90일)**: 운전습관 API. "이번 달 점수 몇 점" 형식 시연 가능.

### P2 (시간 남으면)

- **실시간 주차 위치**: 지하 주차장 제약 있음. 마지막 지상 GPS 위치로 "여기 주차했어요" 정도 가능.
- **연료 경고등 상태**: DTE로 이미 커버되므로 부가 정보 수준.

### Not feasible

- **원격 시동/공조 제어**: 공식 포털에 제어 API 명시 없음. 데이터 조회 API만 확인됨. 개발자 문의 필요. 전시까지 구현 리스크 높음.
- **도어 잠금/해제 원격 제어**: 상동.
- **정확한 연료 리터 수치**: DTE(주행 가능 거리)는 있지만 리터 단위 정확한 잔량은 [확인 필요].
- **실시간 GPS (지하 주차장 내)**: 셀룰러 불가 환경에서 갱신 불가.

---

## 시연 시나리오 후보

### 시나리오 1: "지금 기름 얼마나 남았어? 가득 채우려면 얼마 들지?"

| 항목 | 내용 |
|---|---|
| 필요한 API | `status_dte` (잔여 주행거리) + 연료 잔량 % [확인 필요] |
| 가용 여부 | DTE는 **가능**, 리터 단위 잔량 및 탱크 용량은 [확인 필요] |
| 응답 latency | 캐시 조회 ~1-3초 (추정) |
| 주의점 | 유가 계산은 외부 유가 API 별도 필요 (오피넷 API 등). 차량 탱크 용량은 제원정보 API에서 확보 가능한지 확인 필요. |
| 시연 가능성 | **Partial** — "앞으로 450km 갈 수 있어, 남은 연료로" 수준은 가능. 리터 계산은 추가 확인 필요. |

### 시나리오 2: "오늘 어디어디 들렀어? 총 몇 km 운전했어?"

| 항목 | 내용 |
|---|---|
| 필요한 API | 운행정보 API (시동 ON~OFF 구간 이력) |
| 가용 여부 | **가능** — 운행 이력 API 확인됨 |
| 응답 latency | 캐시 조회 ~1-3초 (추정) |
| 주의점 | 응답에 경위도 포함 시 지도 표시 가능. GPS 경유지 세밀도는 포털 Sample Test로 확인 필요. 지하 주차장 최종 위치는 불정확할 수 있음. |
| 시연 가능성 | **High** — 가장 신뢰도 높은 시나리오. 데모 임팩트도 큼. |

### 시나리오 3: "차 시동 걸어줘. 공조 25도로 맞춰두고."

| 항목 | 내용 |
|---|---|
| 필요한 API | 원격 제어 API (시동, 공조) |
| 가용 여부 | **[확인 필요]** — 공식 포털에 제어 API 명시 없음 |
| 응답 latency | 강제 명령 전송 → 차량 응답 5-30초 (추정) |
| 주의점 | 제어 API 존재 여부 자체가 불확실. 존재해도 사용자 consent 범위, 보안 정책 별도 검토 필요. 지하 주차장에서 셀룰러 신호 약하면 명령 도달 실패. |
| 시연 가능성 | **Low** — 전시 전 개발자 문의 및 테스트 필수. 현재 데모 시나리오로 포함 시 리스크 높음. |

---

## 미확인 / 추가 조사 필요

| 항목 | 이유 |
|---|---|
| 토큰 유효 기간 및 refresh 주기 | 포털 공식 문서가 JavaScript SPA로 크롤링 불가. 포털 로그인 후 직접 확인 필요. |
| Rate limit 정확한 수치 | 공식 비공개. developers@hyundai.com 문의 또는 실제 호출 테스트로 확인 필요. |
| 원격 제어 API 존재 여부 | 데이터 조회 API만 포털에서 확인됨. 제어 API(시동, 공조, 잠금)는 별도 문의 필요. |
| 정확한 API base URL | `prd.kr-ccapi.hyundai.com` 추정이나 포털 규격서에서 실제 URL 확인 필요. |
| 연료 잔량 리터/% 필드 | 경고등(bool) 외에 정확한 수치 제공 여부 확인 필요. |
| 도어/창문 잠금 상태 상세 | 포털 Sample Test로 실제 응답 필드 확인 필요. |
| 운전 패턴 세부 데이터 | 급가속/급감속 등 운전습관 API 상세 필드 확인 필요. |
| 차량 모델 및 연식 | ICE/HEV/PHEV/EV 여부에 따라 가용 API 다름. 확인 후 매트릭스 업데이트 필요. |

---

## 다음 액션 아이템

1. **포털 로그인 → Sample Test** 기능으로 실제 JSON 응답 확인 (`status_dte`, 운행정보, 차량상태)
2. **developers@hyundai.com 문의** — 원격 제어 API 존재 여부, rate limit 수치, 토큰 유효 기간
3. **Python 직접 호출 테스트** — OAuth flow → Bearer 토큰 → 상태 조회 end-to-end 검증
4. **차량 모델 확인** — ICE인 경우 EV battery API 제외, 연료 DTE API 집중
5. **시나리오 2 우선 구현** — 운행 이력은 가장 확실한 가용 API. 지도 시각화 방안 병행 검토

---

## 출처

| 출처 | URL |
|---|---|
| Hyundai Developers - Data API | https://developers.hyundai.com/web/v1/hyundai/data_api |
| Hyundai Developers - API 가이드 | https://developers.hyundai.com/web/v1/hyundai/guide_api |
| Hyundai Developers - FAQ | https://developers.hyundai.com/web/v1/hyundai/faqs |
| Hyundai Developers - EV 배터리 규격서 | https://developers.hyundai.com/web/v1/hyundai/specification/data/status_evbattery |
| Hyundai Developers - EV 충전 규격서 | https://developers.hyundai.com/web/v1/hyundai/specification/data/status_evcharging |
| hyundai_kia_connect_api GitHub | https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api |
| kia_uvo Home Assistant Integration | https://github.com/Hyundai-Kia-Connect/kia_uvo |
| Korea Region Issue #701 (not planned) | https://github.com/Hyundai-Kia-Connect/kia_uvo/issues/701 |
| Token Setup Guide 2026 Discussion | https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api/discussions/987 |
| bluelinky - Vehicle Status API | https://bluelinky.readme.io/reference/status |
| bluelinky Rate Limit Issue #80 | https://github.com/Hacksore/bluelinky/issues/80 |
| hyundai-kia-connect-api PyPI | https://pypi.org/project/hyundai-kia-connect-api/ |
