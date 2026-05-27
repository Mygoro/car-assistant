# Map API Survey — Tmap & 카카오맵

## 조사 일시
2026-05-26

## 조사 목적
Hyundai Bluelink API로 수집한 차량 GPS 좌표·운행 이력을 지도에 시각화하고,
역지오코딩·주변 검색·경로 탐색 기능을 전시 데모(2026-06-02)에 활용하기 위한 API 평가.

---

## A. SK텔레콤 Tmap API

- 포털: https://openapi.sk.com
- 키 발급: 포털 가입 → 앱 생성 → TMAP Free 등록 → appKey 발급

### 무료 플랜 한도

| 기능 | 무료 한도 |
|---|---|
| 경로 탐색 (자동차/보행자) | 일 1,000건 |
| 역지오코딩 | [확인 필요] — 포털 로그인 필요 구간 |
| POI 검색 | [확인 필요] |

출처: https://openapi.sk.com/products/detail?svcSeq=4, https://tmapapi.sktelecom.com/terms.html

### 지원 기능

| 카테고리 | 세부 기능 | 가용 |
|---|---|---|
| 지도 | Vector/Raster/Static Map (JavaScript SDK) | yes |
| 경로 | 자동차·보행자·자전거 경로, 경유지 최적화 | yes |
| 장소 | 역지오코딩, 정방향 지오코딩, POI 검색 | yes |
| 교통 | 실시간 교통 정보, 구간 소요 시간 | yes |
| 분석 | 장소 혼잡도, 유가 정보 | yes |
| 실내 지도 | tmapmobility 비즈니스 API에서 언급, 오픈 API 공개 여부 | [확인 필요] |
| 음성 안내 | 별도 TTS API 없음, 경로 응답 `description` 텍스트를 앱단 TTS로 처리 | yes (간접) |
| T맵 앱 딥링크 | T맵 앱 실행 및 경로 안내 가능 | yes |

### Python 호출 예시

#### 역지오코딩 (GPS 좌표 → 주소)

```python
import requests

APP_KEY = "발급받은_appKey"

def tmap_reverse_geocode(lat, lon):
    url = "https://apis.openapi.sk.com/tmap/geo/reversegeocoding"
    params = {
        "version": 1,
        "lat": lat,
        "lon": lon,
        "coordType": "WGS84GEO",
        "addressType": "A10",   # 도로명+지번 혼합
        "newAddressExtend": "Y"
    }
    headers = {"appKey": APP_KEY, "Accept": "application/json"}
    return requests.get(url, headers=headers, params=params).json()
```

**응답 예시:**
```json
{
  "addressInfo": {
    "fullAddress": "서울시 마포구 상수동",
    "roadName": "강남대로",
    "buildingName": "영진그린빌라",
    "city_do": "서울시",
    "gu_gun": "마포구",
    "bunji": "123-45"
  }
}
```

출처: https://velog.io/@ilil1/응용-안드로이드-TMAP-API로-위도경도를-주소로-반환하기

#### 자동차 경로 탐색

```python
def tmap_route(start_lon, start_lat, end_lon, end_lat):
    url = "https://apis.openapi.sk.com/tmap/routes?version=1"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "appKey": APP_KEY
    }
    body = {
        "startX": start_lon,
        "startY": start_lat,
        "endX": end_lon,
        "endY": end_lat,
        "reqCoordType": "WGS84GEO",
        "resCoordType": "WGS84GEO",
        "carType": 0,
        "sort": "index"
    }
    return requests.post(url, headers=headers, json=body).json()
```

응답: GeoJSON `features` 배열, `LineString` geometry에 경로 좌표 포함.

출처: https://community.openapi.sk.com/t/topic/10082

---

## B. 카카오맵 API

- 포털: https://developers.kakao.com
- 키 발급: 카카오 계정 로그인 → 앱 생성 → **REST API 키** 복사 → 플랫폼(도메인) 등록

### 무료 플랜 한도

| API | 무료 한도/일 | 초과 단가 |
|---|---|---|
| 지도 SDK (JS/iOS/Android) | 300,000건 | — |
| 역지오코딩 (`coord2address`) | 100,000건 | 0.5원/건 |
| 좌표→행정구역 (`coord2regioncode`) | 100,000건 | 0.5원/건 |
| 주소→좌표 (`search/address`) | 100,000건 | 0.5원/건 |
| 키워드 장소 검색 | 100,000건 | 2원/건 |
| 카테고리 장소 검색 | 100,000건 | 2원/건 |
| 카카오모빌리티 자동차 길찾기 | 10,000건 | 8원/건 |

출처: https://developers.kakao.com/docs/latest/ko/getting-started/quota

### 지원 기능

| 기능 | Endpoint | 가용 |
|---|---|---|
| 지도 렌더링 (JS) | JavaScript API | yes |
| 역지오코딩 | `/v2/local/geo/coord2address.json` | yes |
| 좌표→행정구역 | `/v2/local/geo/coord2regioncode.json` | yes |
| 주소→좌표 | `/v2/local/search/address.json` | yes |
| 키워드 장소 검색 | `/v2/local/search/keyword.json` | yes |
| 카테고리 장소 검색 | `/v2/local/search/category.json` | yes |
| 좌표계 변환 | `/v2/local/geo/transcoord.json` | yes |
| 자동차 경로 탐색 | 카카오모빌리티 별도 도메인 | yes |
| 카카오내비 딥링크 | 카카오내비 오픈 API | yes |
| 실내 지도 | [확인 필요] — 공식 문서 미언급 | |

### Python 호출 예시

모든 호출 공통 헤더:
```python
headers = {"Authorization": f"KakaoAK {REST_API_KEY}"}
```

#### 역지오코딩 (좌표 → 주소)

```python
def kakao_reverse_geocode(lon, lat):
    # x=경도, y=위도 (WGS84)
    url = "https://dapi.kakao.com/v2/local/geo/coord2address.json"
    params = {"x": lon, "y": lat, "input_coords": "WGS84"}
    return requests.get(url, headers=headers, params=params).json()
```

**응답 예시:**
```json
{
  "documents": [{
    "address": {
      "address_name": "서울 서초구 서초동 1309-12",
      "region_1depth_name": "서울",
      "region_2depth_name": "서초구",
      "region_3depth_name": "서초동"
    },
    "road_address": {
      "address_name": "서울 서초구 서초대로74길 11",
      "road_name": "서초대로74길",
      "zone_no": "06621"
    }
  }]
}
```

출처: https://cruddbdbdeep.github.io/python/2018/11/02/reverse-geocoding.html

#### 키워드/카테고리 장소 검색 (주변 주유소·충전소)

```python
def kakao_search_nearby(query, lon, lat, radius_m=5000):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    params = {
        "query": query,       # "주유소", "전기차 충전소" 등
        "x": lon,
        "y": lat,
        "radius": radius_m,   # 최대 20,000m
        "sort": "distance"
    }
    return requests.get(url, headers=headers, params=params).json()

# 카테고리 코드로 검색 (더 정확)
# OL7: 주유소, EV: 전기차 충전소
def kakao_search_category(category_code, lon, lat, radius_m=5000):
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    params = {"category_group_code": category_code, "x": lon, "y": lat, "radius": radius_m}
    return requests.get(url, headers=headers, params=params).json()
```

**응답 예시:**
```json
{
  "documents": [{
    "place_name": "GS칼텍스 강남주유소",
    "address_name": "서울 강남구 테헤란로 123",
    "road_address_name": "서울 강남구 테헤란로 123",
    "phone": "02-123-4567",
    "x": "127.0276",
    "y": "37.4979",
    "distance": "320"   // 미터
  }],
  "meta": {"total_count": 15}
}
```

출처: https://wooiljeong.github.io/python/kakao_local_api/

#### 카카오모빌리티 자동차 경로 탐색

```python
def kakao_directions(origin_lon, origin_lat, dest_lon, dest_lat):
    url = "https://apis-navi.kakaomobility.com/v1/directions"
    params = {
        "origin": f"{origin_lon},{origin_lat}",
        "destination": f"{dest_lon},{dest_lat}",
        "priority": "TIME"    # TIME 또는 DISTANCE
    }
    return requests.get(url, headers=headers, params=params).json()
```

**응답 핵심 필드:**
```json
{
  "routes": [{
    "summary": {
      "duration": 1320,    // 초
      "distance": 8500     // 미터
    }
  }]
}
```

출처: https://velog.io/@duddlfkd02/카카오-모빌리티-API를-써보자

---

## C. Tmap vs 카카오맵 비교

| 기준 | Tmap | 카카오맵 |
|---|---|---|
| 무료 한도 (경로) | **일 1,000건** | **일 10,000건** (카카오모빌리티) |
| 무료 한도 (역지오코딩) | [확인 필요] | **일 100,000건** |
| 무료 한도 (장소 검색) | [확인 필요] | **일 100,000건** |
| 역지오코딩 응답 | `fullAddress` + 행정구역 분리 | 지번 + 도로명 동시 반환 |
| Python 호출 | REST, `requests` 가능 | REST, `requests` 가능, 예제 다수 |
| 문서 접근성 | 로그인 필요 구간 있음 | 공개 문서 풍부 |
| 한국 지도 정확도 | T맵 내비 데이터, 높음 | 카카오맵 데이터, 높음 |
| 실시간 교통 | 강점 (T맵 내비 기반) | 카카오모빌리티 기반 |
| 데모 적합성 | 보통 (한도 제약) | **높음** (한도 여유, 예제 풍부) |

---

## D. 전시 데모 시나리오별 활용 평가

### 시나리오 1: 운행 이력 지도 시각화 (GPS 경로 → Polyline)

| 항목 | 내용 |
|---|---|
| 권장 API | 카카오맵 JavaScript API (`kakao.maps.Polyline`) |
| 이유 | Polyline 예제 풍부, 좌표 리스트 직접 전달, 무료 300,000건/일 |
| 구현 방법 | Python 백엔드에서 Bluelink 좌표 → JSON 반환 → 프론트 JS에서 렌더링 |
| 주의점 | GPS 좌표가 WGS84 기준인지 확인 필요 |

### 시나리오 2: 역지오코딩 ("37.xxx, 127.xxx" → 자연어 주소)

| 항목 | 내용 |
|---|---|
| 권장 API | 카카오 로컬 REST API (`coord2address`) |
| Endpoint | `GET https://dapi.kakao.com/v2/local/geo/coord2address.json` |
| 가용 여부 | **yes** |
| 응답 latency | ~200-500ms (추정) |
| 주의점 | `road_address`가 null인 경우 `address.address_name`으로 폴백 처리 필요 |

### 시나리오 3: 주변 주유소/충전소 검색

| 항목 | 내용 |
|---|---|
| 권장 API | 카카오 카테고리 검색 (`category_group_code=OL7` 주유소, `EV` 충전소) |
| Endpoint | `GET https://dapi.kakao.com/v2/local/search/category.json` |
| 가용 여부 | **yes** |
| 응답 | 장소명, 주소, 전화번호, 거리(m) 포함 |
| 주의점 | 반경 최대 20,000m, 최대 45건 반환 (페이지네이션 필요 시 `page` 파라미터) |

### 시나리오 4: 현재 위치 → 목적지 예상 소요 시간

| 항목 | 내용 |
|---|---|
| 권장 API | 카카오모빌리티 Directions API |
| Endpoint | `GET https://apis-navi.kakaomobility.com/v1/directions` |
| 가용 여부 | **yes** |
| 응답 | `duration`(초), `distance`(미터) |
| 주의점 | Tmap 대비 무료 한도 10배 높음 (10,000건/일). 단, Tmap이 실시간 교통 정확도 강점. |

---

## E. 권장 API 조합 (전시 데모 기준)

실제 사용 패턴 기반 역할 분담:
- **Tmap** → 경로 탐색·내비게이션 (국내 실시간 교통 데이터 품질 우위)
- **카카오맵** → 장소 검색·POI·역지오코딩·지도 시각화 (점포 정보·대중교통 강점)

| 기능 | 사용 API | 무료 한도 | 선택 이유 |
|---|---|---|---|
| 지도 렌더링 + Polyline | 카카오맵 JavaScript API | 300,000건/일 | 시각화 예제 풍부 |
| 역지오코딩 (좌표→주소) | 카카오 로컬 REST | 100,000건/일 | 지번+도로명 동시 반환 |
| 주변 주유소·충전소 검색 | 카카오 카테고리 검색 | 100,000건/일 | 점포 정보 데이터 강점 |
| 자동차 경로·소요 시간 | **Tmap Routes API** | 1,000건/일 | 실시간 교통 정확도 우위 |

> **주의**: Tmap 경로 탐색은 무료 1,000건/일이므로 데모 반복 테스트 시 소진 주의.
> 테스트 단계에서는 카카오모빌리티(10,000건/일)로 대체하고, 전시 당일에 Tmap으로 전환하는 방식 권장.

---

## F. 미확인 / 추가 조사 필요

| 항목 | 이유 |
|---|---|
| Tmap 역지오코딩·POI 검색 무료 한도 | openapi.sk.com 로그인 필요 구간으로 수치 미확인 |
| 카카오 카테고리 코드 전체 목록 | EV 충전소 코드 `EV` 외 세부 분류 확인 필요 |
| Tmap 실내 지도 오픈 API 공개 여부 | 비즈니스 API에서만 제공 가능성 있음 |
| 카카오맵 Polyline + 마커 동시 렌더링 성능 | 경로 좌표 수백 개일 경우 렌더링 최적화 필요 여부 |

---

## 출처

| 출처 | URL |
|---|---|
| SK open API - Tmap 상품 정보 | https://openapi.sk.com/products/detail?svcSeq=4 |
| Tmap 이용절차 | https://transit.tmapmobility.com/guide/procedure |
| Tmap 무료체험 약관 | https://tmapapi.sktelecom.com/terms.html |
| Tmap 역지오코딩 Python 예시 (Velog) | https://velog.io/@ilil1/응용-안드로이드-TMAP-API로-위도경도를-주소로-반환하기 |
| Tmap 경로탐색 커뮤니티 | https://community.openapi.sk.com/t/topic/10082 |
| 카카오 쿼터 정책 | https://developers.kakao.com/docs/latest/ko/getting-started/quota |
| 카카오 로컬 REST API 개발 가이드 | https://developers.kakao.com/docs/ko/local/dev-guide |
| 카카오 역지오코딩 Python 예시 | https://cruddbdbdeep.github.io/python/2018/11/02/reverse-geocoding.html |
| 카카오 로컬 API Python 예시 | https://wooiljeong.github.io/python/kakao_local_api/ |
| 카카오모빌리티 디벨로퍼스 | https://developers.kakaomobility.com/docs/ |
| 카카오모빌리티 API 사용 예시 (Velog) | https://velog.io/@duddlfkd02/카카오-모빌리티-API를-써보자 |
