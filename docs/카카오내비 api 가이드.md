# 자동차 길찾기

하나의 출발지에서 하나의 목적지까지로의 경로에 대한 상세 정보를 제공합니다. 경유지는 최대 5개까지 추가할 수 있으며 모든 경유지를 포함한 경로의 총 거리는 1,500 km 미만으로 설정해야 합니다.

DANGER

해당 API를 사용하기 위해서는 REST API 키 값이 반드시 필요합니다. [시작하기](https://developers.kakaomobility.com/guide/navi-api/start/)에서 앱 등록과 REST API 키 값 확인 방법을 참고하세요.

## Request

요청 호출 방식과 각 요청 헤더에 포함될 내용을 안내합니다. 요청이 실패할 경우 [문제 해결하기](https://developers.kakaomobility.com/guide/navi-api/solution/)에서 에러에 대한 상세 내용을 확인하세요.

### 호출 방식

**표 1 호출 방식**

|Method|URL|
|---|---|
|`GET`|[https://apis-navi.kakaomobility.com/v1/directions](https://apis-navi.kakaomobility.com/v1/directions)|

### 요청 헤더(Header)

**표 2 요청 헤더**

|Parameter|Description|
|---|---|
|Authorization|KakaoAK ${REST_API_KEY}  <br>  <br>{REST_API_KEY}: 카카오디벨로퍼스에서 발급 받은 REST API 키|
|Content-Type|`application/json`|

### 요청 코드 예제

```
curl -v -X GET "https://apis-navi.kakaomobility.com/v1/directions?origin=127.10764191124568,37.402464820205246,angle=270&destination=127.11056336672839,37.39419693653072&summary=false&waypoints=127.17354989857544,37.36629687436494&priority=RECOMMEND&car_fuel=GASOLINE&car_hipass=false&alternatives=false&road_details=false" \
    -H "Authorization: KakaoAK ${REST_API_KEY}" // 카카오디벨로퍼스에서 발급 받은 API 키 값
```

요청에 대한 파라미터는 다음과 같습니다.

**표 3 요청 파라미터**

|Name|Type|Description|Required|
|---|---|---|---|
|`origin`|String|출발지  <br>  <br>다음 중 하나의 형식으로 요청:  <br>1. `${X좌표},${Y좌표},name=${출발지명}`  <br>(예: "`127.111202,37.394912,name=판교역`")  <br>  <br>2. `${X좌표},${Y좌표}`  <br>(예: "`127.111202,37.394912`")  <br>  <br>3.`${X좌표},${Y좌표},${angle}`  <br>(예:"`127.111202,37.394912,angle=90`")  <br>  <br>`angle`: 출발지의 초기 진행 방향 지정. 0~360 범위의 정수를 입력  <br>(각도에 따른 방향: 0 = 북쪽, 90 = 동쪽, 180 = 남쪽, 270 = 서쪽 등 시계 방향으로 반영. 범위를 벗어난 값은 무시)|필수|
|`destination`|String|목적지  <br>  <br>다음 중 하나의 형식으로 요청:  <br>`${X좌표},${Y좌표},name=${목적지명}` 또는 `${X좌표},${Y좌표}`  <br>(예: "`127.111202,37.394912,name=판교역`" 또는 "`127.111202,37.394912`")|필수|
|`waypoints`|String|경유지, 최대 5개까지 허용  <br>모든 경유지를 포함한 경로의 총 거리는 1,500 km 미만으로 설정해야 함.  <br>  <br>경유지 수만큼 `${X좌표},${Y좌표},name=${경유지명}` 또는 `${X좌표},${Y좌표}`를 `\|`(또는 인코딩 된 문자인 `%7C`)로 연결하여 입력  <br>(예: "`127.111202,37.394912,name=판교역 \| 127.112275,37.392815`")|선택|
|`priority`|String|경로 탐색 우선순위 옵션  <br>  <br>다음 중 하나:  <br>`RECOMMEND`: 추천 경로  <br>`TIME`: 최단 시간  <br>`DISTANCE`: 최단 경로  <br>(기본값: `RECOMMEND`)|선택|
|`avoid`|String|경로 탐색 제한 옵션  <br>  <br>다음 값 사용 가능:  <br>`ferries`: 페리 항로  <br>`toll`: 유료 도로  <br>`motorway`: 자동차 전용 도로  <br>`schoolzone`: 어린이 보호 구역  <br>`uturn`: 유턴  <br>(기본값: `null`)  <br>  <br>여러 개의 제한 옵션을 사용하려면 `\|`(또는 인코딩 된 문자인 `%7C`)로 연결  <br>(예: `avoid=motorway\|ferries`)|선택|
|`roadevent`|Int|유고(교통사고, 행사, 재난, 도로 공사 등의 교통 장애)로 인한 도로 통제 정보 반영 옵션  <br>  <br>`0`: 전체 차선 통제(도로 전체 통제) 정보를 반영  <br>`1`: 출발지 및 목적지 주변의 전체 차선 통제 정보 반영 안 함  <br>`2`: 모든 구간의 전체 차선 통제 정보 반영 안 함  <br>(기본값: `0`)|선택|
|`alternatives`|Boolean|대안 경로 제공 여부  <br>  <br>`true`: 대안 경로 제공  <br>`false`: 대안 경로 미제공  <br>(기본값: `false`)|선택|
|`road_details`|Boolean|상세 도로 정보 제공 여부  <br>  <br>`true`: 상세 도로 정보 제공  <br>`false`: 상세 도로 정보 미제공  <br>(기본값: `false`)|선택|
|`car_type`|Int|[차종](https://developers.kakaomobility.com/guide/navi-api/reference/#car_type-%EC%B0%A8%EC%A2%85)  <br>  <br>(기본값: `1`)|선택|
|`car_fuel`|String|차량 유종 정보  <br>  <br>다음 중 하나:  <br>`GASOLINE`: 휘발유  <br>`DIESEL`: 경유  <br>`LPG`: LPG  <br>(기본값: `GASOLINE`)|선택|
|`car_hipass`|Boolean|하이패스 장착 여부  <br>  <br>`true`: 하이패스 장착  <br>`false`: 하이패스 미장착  <br>(기본값: `false`)|선택|
|`summary`|Boolean|경로 정보 응답 범위 설정  <br>  <br>`true`: 요약 정보만 반환 (`sections`의 `bound`, `roads`, `guides` 정보 제외)  <br>`false`: 요약 정보와 상세 정보 반환(`sections`의 `bound`, `roads`, `guides` 정보 포함)  <br>(기본값: `false`)|선택|

## Response

응답 성공 시 요청에 대한 성공 여부를 [HTTP 상태 코드](https://developers.kakaomobility.com/guide/navi-api/solution/#http-%EC%83%81%ED%83%9C-%EC%BD%94%EB%93%9C)로, 요청 본문은 `JSON` 포맷으로 전달합니다.

### 응답 코드 예제

```
{
  "trans_id": "01948280a50d700d945a8ec5c132709d",
  "routes": [
      {
          "result_code": 0,
          "result_msg": "길찾기 성공",
          "summary": {
              "origin": {
                  "name": "",
                  "x": 127.10763058573032,
                  "y": 37.40246478787756
              },
              "destination": {
                  "name": "",
                  "x": 127.1098265381582,
                  "y": 37.394425724914576
              },
              "waypoints": [
                  {
                      "name": "",
                      "x": 127.17353858063272,
                      "y": 37.3662968484953
                  }
              ],
              "priority": "RECOMMEND",
              "bound": {
                  "min_x": 127.10699672876241,
                  "min_y": 37.35782058991495,
                  "max_x": 127.17437025337696,
                  "max_y": 37.40371556711698
              },
              "fare": {
                  "taxi": 22200,
                  "toll": 0
              },
              "distance": 19032,
              "duration": 3494
          },
          "sections": [
              {
                  "distance": 10035,
                  "duration": 1880,
                  "bound": {
                      "min_x": 127.16765984810529,
                      "min_y": 37.35821336047281,
                      "max_x": 127.17352998262038,
                      "max_y": 37.40325103149278
                  },
                  "roads": [
                      {
                          "name": "판교역로241번길",
                          "distance": 186,
                          "duration": 47,
                          "traffic_speed": 14.0,
                          "traffic_state": 2,
                          "vertexes": [
                              127.10763122680424,
                              37.40241072822385,
                              // 코드 생략
                              127.10645821495126,
                              37.40322184743522
                          ]
                      },
                      ...
                      {
                          "name": "문형산길",
                          "distance": 596,
                          "duration": 104,
                          "traffic_speed": 16.0,
                          "traffic_state": 0,
                          "vertexes": [
                              127.16765984810529,
                              37.36601233289304,
                              // 코드 생략
                              127.17352998262038,
                              37.36708073181059
                          ]
                      }
                  ],
                  "guides": [
                      {
                          "name": "출발지",
                          "x": 127.10763122680424,
                          "y": 37.40241072822385,
                          "distance": 0,
                          "duration": 0,
                          "type": 100,
                          "guidance": "출발지",
                          "road_index": 0
                      },
                      // 코드 생략
                      {
                          "name": "경유지",
                          "x": 127.17352998262038,
                          "y": 37.36708073181059,
                          "distance": 596,
                          "duration": 104,
                          "type": 1000,
                          "guidance": "경유지",
                          "road_index": -1
                      }
                  ]
              },
              {
                  "distance": 8997,
                  "duration": 1614,
                  "bound": {
                      "min_x": 127.10966790676201,
                      "min_y": 37.35832776837687,
                      "max_x": 127.17475981481635,
                      "max_y": 37.39447077471427
                  },
                  "roads": [
                      {
                          "name": "문형산안길1번길",
                          "distance": 85,
                          "duration": 19,
                          "traffic_speed": 16.0,
                          "traffic_state": 0,
                          "vertexes": [
                              127.17352998262038,
                              37.36708073181059,
                              127.17357513799075,
                              37.36708104732421,
                              127.17372149772216,
                              37.367118113235804,
                              127.1739231164781,
                              37.36726369503417,
                              127.17434992149448,
                              37.36746491368941
                          ]
                      },
                      // 코드 생략
                      {
                          "name": "",
                          "distance": 14,
                          "duration": 3,
                          "traffic_speed": 16.0,
                          "traffic_state": 0,
                          "vertexes": [
                              127.10966790676201,
                              37.394469584427156,
                              127.10982600539788,
                              37.39447077471427
                          ]
                      }
                  ],
                  "guides": [
                      {
                          "name": "경유지",
                          "x": 127.17352998262038,
                          "y": 37.36708073181059,
                          "distance": 0,
                          "duration": 0,
                          "type": 1000,
                          "guidance": "경유지",
                          "road_index": 0
                      },
                      // 코드 생략
                      {
                          "name": "",
                          "x": 127.10966790676201,
                          "y": 37.394469584427156,
                          "distance": 81,
                          "duration": 50,
                          "type": 2,
                          "guidance": "우회전",
                          "road_index": 11
                      },
                      {
                          "name": "목적지",
                          "x": 127.10982600539788,
                          "y": 37.39447077471427,
                          "distance": 14,
                          "duration": 3,
                          "type": 101,
                          "guidance": "목적지",
                          "road_index": -1
                      }
                  ]
              }
          ]
      }
  ]
}
```

요청 응답에 대한 객체 정보는 다음과 같습니다.

**표 4 응답 객체**

|Name|Type|Description|Required|
|---|---|---|---|
|`trans_id`|String|경로 요청 ID|필수|
|`routes`|Object[]|경로 정보  <br>  <br>`alternatives`가 `true`인 경우 한 개 이상의 경로 제공 가능|필수|
|`result_code`|Int|[경로 탐색 결과 코드](https://developers.kakaomobility.com/guide/navi-api/reference/)|필수|
|`result_msg`|String|경로 탐색 결과 메시지|필수|
|`summary`|Object|경로 요약 정보|필수|
|`origin`|Object|출발지 정보|필수|
|`name`|String|출발지 이름|필수|
|`x`|Double|X 좌표(경도)|필수|
|`y`|Double|Y 좌표(위도)|필수|
|`destination`|Object|목적지 정보|필수|
|`name`|String|목적지 이름|필수|
|`x`|Double|X 좌표(경도)|필수|
|`y`|Double|Y 좌표(위도)|필수|
|`waypoints`|Object[]|경유지 정보|필수|
|`name`|String|경유지 이름|필수|
|`x`|Double|X 좌표(경도)|필수|
|`y`|Double|Y 좌표(위도)|필수|
|`priority`|String|경로 탐색 우선순위 옵션|필수|
|`bound`|Object|모든 경로를 포함하는 사각형의 바운딩 박스(Bounding box)|선택|
|`min_x`|Double|바운딩 박스 왼쪽 하단의 X 좌표|필수|
|`min_y`|Double|바운딩 박스 왼쪽 하단의 Y 좌표|필수|
|`max_x`|Double|바운딩 박스 오른쪽 상단의 X 좌표|필수|
|`max_y`|Double|바운딩 박스 오른쪽 상단의 Y 좌표|필수|
|`fare`|Object|요금 정보|필수|
|`taxi`|Int|택시 요금(원)|필수|
|`toll`|Int|통행 요금(원)|필수|
|`distance`|Int|전체 검색 결과 거리(미터)|필수|
|`duration`|Int|목적지까지 소요 시간(초)|필수|
|`sections`|Object[]|구간별 경로 정보  <br>  <br>경유지가 존재할 경우 {경유지 수 + 1} 만큼의 섹션(경로 구간) 생성  <br>(예: 경유지 수가 2개인 경우 총 3개의 섹션 정보가 생성,  <br>section1: 출발지 → 경유지 1  <br>section2: 경유지 1 → 경유지 2  <br>section3: 경유지 2 → 목적지)|필수|
|`distance`|Int|섹션 거리(미터)|필수|
|`duration`|Int|전체 검색 결과 이동 시간(초)|필수|
|`bound`|Object|모든 경로를 포함하는 사각형의 바운딩 박스(Bounding box)  <br>  <br>`summary`가 `false`인 경우에만 제공|선택|
|`min_x`|Double|바운딩 박스 왼쪽 하단의 X 좌표|필수|
|`min_y`|Double|바운딩 박스 왼쪽 하단의 Y 좌표|필수|
|`max_x`|Double|바운딩 박스 오른쪽 상단의 X 좌표|필수|
|`max_y`|Double|바운딩 박스 오른쪽 상단의 Y 좌표|필수|
|`roads`|Object[]|도로 정보  <br>  <br>`summary`가 `false`인 경우에만 제공|선택|
|`name`|String|도로명|필수|
|`distance`|Int|도로 길이(미터)|필수|
|`duration`|Int|예상 이동 시간(초)  <br>  <br>현재 예상 이동 시간 및 실제 이동 시간은 동일한 값으로 설정|필수|
|`traffic_speed`|Double|현재 교통 정보 속도(km/h)|필수|
|`traffic_state`|Int|[현재 교통 정보 상태](https://developers.kakaomobility.com/guide/navi-api/reference/)|필수|
|`vertexes`|Double[]|X, Y 좌표로 구성된 1차원 배열  <br>  <br>(예: [127.10966790676201, 37.394469584427156, 127.10967141980313, 37.39512739646385] )|필수|
|`guides`|Object[]|안내 정보  <br>  <br>`summary`가 `false`인 경우에만 제공|선택|
|`name`|String|명칭|필수|
|`x`|Double|X 좌표(경도)|필수|
|`y`|Double|Y 좌표(위도)|필수|
|`distance`|Int|이전 가이드 지점부터 현재 가이드 지점까지 거리(미터)|필수|
|`duration`|Int|이전 가이드 지점부터 현재 가이드 지점까지 시간(초)|필수|
|`type`|Int|[안내 타입](https://developers.kakaomobility.com/guide/navi-api/reference/#type-%EC%95%88%EB%82%B4-%ED%83%80%EC%9E%85)|필수|
|`guidance`|String|안내 문구|필수|
|`road_index`|Int|현재 가이드에 대한 링크 인덱스|필수|
# 다중 경유지 길찾기

하나의 출발지에서 여러 개의 경유지를 지나 하나의 목적지까지의 경로 상세 정보를 제공합니다. 경유지는 최대 30개까지 추가할 수 있으며 모든 경유지를 포함한 경로의 총 거리는 1,500 km 미만으로 설정해야 합니다.

DANGER

해당 API를 사용하기 위해서는 REST API 키 값이 반드시 필요합니다. [시작하기](https://developers.kakaomobility.com/guide/navi-api/start/)에서 앱 등록과 REST API 키 값 확인 방법을 참고하세요.

## Request

요청 호출 방식과 각 요청 헤더에 포함될 내용을 안내합니다. 요청이 실패할 경우 [문제 해결하기](https://developers.kakaomobility.com/guide/navi-api/solution/)에서 에러에 대한 상세 내용을 확인하세요.

### 호출 방식

**표 1 호출 방식**

|Method|URL|
|---|---|
|`POST`|[https://apis-navi.kakaomobility.com/v1/waypoints/directions](https://apis-navi.kakaomobility.com/v1/waypoints/directions)|

### 요청 헤더(Header)

**표 2 요청 헤더**

|Parameter|Description|
|---|---|
|Authorization|KakaoAK ${REST_API_KEY}  <br>  <br>{REST_API_KEY}: 카카오디벨로퍼스에서 발급 받은 REST API 키|
|Content-Type|`application/json`|

### 요청 코드 예제

```
curl -v -X POST "https://apis-navi.kakaomobility.com/v1/waypoints/directions" \
-H "Content-Type: application/json" \
-H "Authorization: KakaoAK ${REST_API_KEY}" \ // 카카오디벨로퍼스에서 발급 받은 API 키 값
-d '{
  "origin": {
      "x": "127.11024293202674",
      "y": " 37.394348634049784",
      "angle": 270
  },
  "destination": {
      "x": "127.10860518470294",
      "y": "37.401999820065534"
  },
  "waypoints": [
      {
          "name": "name0",
          "x": 127.11341936045922,
          "y": 37.39639094915999
      }
  ],
  "priority": "RECOMMEND",
  "car_fuel": "GASOLINE",
  "car_hipass": false,
  "alternatives": false,
  "road_details": false,
  "summary": false
}'
```

요청에 대한 파라미터는 다음과 같습니다.

**표 3 요청 파라미터**

|Name|Type|Description|Required|
|---|---|---|---|
|`origin`|Object|출발지|필수|
|`name`|String|출발지 이름|선택|
|`x`|Double|X 좌표(경도)|필수|
|`y`|Double|Y 좌표(위도)|필수|
|`angle`|Int|출발지의 초기 진행 방향 지정  <br>  <br>0~360 범위의 정수 입력.  <br>(각도에 따른 방향: 0 = 북쪽, 90 = 동쪽, 180 = 남쪽, 270 = 서쪽 등 시계 방향으로 반영. 범위를 벗어난 값은 무시)|선택|
|`destination`|Object|목적지|필수|
|`name`|String|목적지 이름|선택|
|`x`|Double|X 좌표(경도)|필수|
|`y`|Double|Y 좌표(위도)|필수|
|`waypoints`|Object[]|경유지, 최대 30개까지 허용  <br>모든 경유지를 포함한 경로의 총 거리는 1,500 km 미만으로 설정해야 함.|선택|
|`name`|String|경유지 이름|선택|
|`x`|Double|X 좌표(경도)|필수|
|`y`|Double|Y 좌표(위도)|필수|
|`priority`|String|경로 탐색 우선순위 옵션  <br>  <br>다음 중 하나:  <br>`RECOMMEND`: 추천 경로  <br>`TIME`: 최단 시간  <br>`DISTANCE`: 최단 경로  <br>(기본값: `RECOMMEND`)|선택|
|`avoid`|String[]|경로 탐색 제한 옵션  <br>  <br>다음 값 사용 가능:  <br>`ferries`: 페리 항로  <br>`toll`: 유료 도로  <br>`motorway`: 자동차 전용 도로  <br>`schoolzone`: 어린이 보호 구역  <br>`uturn`: 유턴  <br>(기본값: `null`)  <br>  <br>여러 개의 제한 옵션을 사용하려면 다음과 같이 연결  <br>(예: ["`ferries`", "`motorway`"])|선택|
|`roadevent`|Int|유고(교통사고, 행사, 재난, 도로 공사 등의 교통 장애)로 인한 도로 통제 정보 반영 옵션  <br>  <br>`0`: 전체 차선 통제(도로 전체 통제) 정보를 반영  <br>`1`: 출발지 및 목적지 주변의 전체 차선 통제 정보 반영 안 함  <br>`2`: 모든 구간의 전체 차선 통제 정보 반영 안 함  <br>(기본값: `0`)|선택|
|`alternatives`|Boolean|대안 경로 제공 여부  <br>  <br>`true`: 대안 경로 제공  <br>`false`: 대안 경로 미제공  <br>(기본값: `false`)|선택|
|`road_details`|Boolean|상세 도로 정보 제공 여부  <br>  <br>`true`: 상세 도로 정보 제공  <br>`false`: 상세 도로 정보 미제공  <br>(기본값: `false`)|선택|
|`car_type`|Int|[차종](https://developers.kakaomobility.com/guide/navi-api/reference/#car_type-%EC%B0%A8%EC%A2%85)  <br>  <br>(기본값: `1`)|선택|
|`car_fuel`|String|차량 유종 정보  <br>  <br>다음 중 하나:  <br>`GASOLINE`: 휘발유  <br>`DIESEL`: 경유  <br>`LPG`: LPG  <br>(기본값: `GASOLINE`)|선택|
|`car_hipass`|Boolean|하이패스 장착 여부  <br>  <br>`true`: 하이패스 장착  <br>`false`: 하이패스 미장착  <br>(기본값: `false`)|선택|
|`summary`|Boolean|경로 정보 응답 범위 설정  <br>  <br>`true`: 요약 정보만 반환 (`sections`의 `bound`, `roads`, `guides` 정보 제외)  <br>`false`: 요약 정보와 상세 정보 반환(`sections`의 `bound`, `roads`, `guides` 정보 포함)  <br>(기본값: `false`)|선택|

## Response

응답 성공 시 요청에 대한 성공 여부를 [HTTP 상태 코드](https://developers.kakaomobility.com/guide/navi-api/solution/#http-%EC%83%81%ED%83%9C-%EC%BD%94%EB%93%9C)로, 요청 본문은 `JSON` 포맷으로 전달합니다.

### 응답 코드 예제

```
{
  "trans_id": "0194de353ee97a56a7807b8a505eb4da",
  "routes": [
      {
          "result_code": 0,
          "result_msg": "길찾기 성공",
          "summary": {
              "origin": {
                  "name": "",
                  "x": 127.11023403583478,
                  "y": 37.39434769502827
              },
              "destination": {
                  "name": "",
                  "x": 127.10859622855493,
                  "y": 37.40199450213265
              },
              "waypoints": [
                  {
                      "name": "name0",
                      "x": 127.11341740484119,
                      "y": 37.39639001677204
                  }
              ],
              "priority": "RECOMMEND",
              "bound": {
                  "min_x": 127.10873060789754,
                  "min_y": 37.39446252338457,
                  "max_x": 127.11400101911747,
                  "max_y": 37.402458630852735
              },
              "fare": {
                  "taxi": 6600,
                  "toll": 0
              },
              "distance": 2193,
              "duration": 574
          },
          "sections": [
              {
                  "distance": 1074,
                  "duration": 280,
                  "bound": {
                      "min_x": 127.11341931516797,
                      "min_y": 37.394469584427156,
                      "max_x": 127.11406301821938,
                      "max_y": 37.398332068681995
                  },
                  "roads": [
                      {
                          "name": "",
                          "distance": 22,
                          "duration": 5,
                          "traffic_speed": 16.0,
                          "traffic_state": 0,
                          "vertexes": [
                              127.10991634747967,
                              37.39447145478345,
                              127.10966790676201,
                              37.394469584427156
                          ]
                      },
                      {
                          "name": "판교역로",
                          "distance": 364,
                          "duration": 97,
                          "traffic_speed": 27.0,
                          "traffic_state": 3,
                          "vertexes": [
                              127.10966790676201,
                              37.394469584427156,
                              127.10967141980313,
                              37.39512739646385,
                              127.10968100356395,
                              37.396226781360426,
                              127.10967417816033,
                              37.39775855885587
                          ]
                      },
                      {
                          "name": "판교역로192번길",
                          "distance": 398,
                          "duration": 113,
                          "traffic_speed": 23.0,
                          "traffic_state": 3,
                          "vertexes": [
                              127.10967417816033,
                              37.39775855885587,
                              127.10991144303469,
                              37.39775133437272,
                              127.11030660039278,
                              37.39776331905757,
                              127.11058861237368,
                              37.39779247292587,
                              127.11190492731849,
                              37.39822587238842,
                              127.11217511696259,
                              37.39829998747621,
                              127.11242335797999,
                              37.39831987264784,
                              127.11275097123547,
                              37.39831332063064,
                              127.1130784782746,
                              37.3983157776669,
                              127.11404960021814,
                              37.398332068681995
                          ]
                      },
                      {
                          "name": "",
                          "distance": 233,
                          "duration": 39,
                          "traffic_speed": 42.0,
                          "traffic_state": 0,
                          "vertexes": [
                              127.11404960021814,
                              37.398332068681995,
                              127.11403422576758,
                              37.39771922184463,
                              127.11406301821938,
                              37.39623266200683
                          ]
                      },
                      {
                          "name": "대왕판교로606번길",
                          "distance": 57,
                          "duration": 26,
                          "traffic_speed": 17.0,
                          "traffic_state": 2,
                          "vertexes": [
                              127.11406301821938,
                              37.39623266200683,
                              127.11341931516797,
                              37.39622783738649
                          ]
                      }
                  ],
                  "guides": [
                      {
                          "name": "출발지",
                          "x": 127.10991634747967,
                          "y": 37.39447145478345,
                          "distance": 0,
                          "duration": 0,
                          "type": 100,
                          "guidance": "출발지",
                          "road_index": 0
                      },
                      {
                          "name": "",
                          "x": 127.10966790676201,
                          "y": 37.394469584427156,
                          "distance": 22,
                          "duration": 5,
                          "type": 2,
                          "guidance": "우회전",
                          "road_index": 1
                      },
                      {
                          "name": "",
                          "x": 127.10967417816033,
                          "y": 37.39775855885587,
                          "distance": 364,
                          "duration": 97,
                          "type": 2,
                          "guidance": "광장로 방면으로 우회전",
                          "road_index": 2
                      },
                      {
                          "name": "",
                          "x": 127.11404960021814,
                          "y": 37.398332068681995,
                          "distance": 398,
                          "duration": 113,
                          "type": 2,
                          "guidance": "백현동 방면으로 우회전",
                          "road_index": 3
                      },
                      {
                          "name": "",
                          "x": 127.11406301821938,
                          "y": 37.39623266200683,
                          "distance": 233,
                          "duration": 39,
                          "type": 2,
                          "guidance": "판교테크노밸리 양재 내곡 방면으로 우회전",
                          "road_index": 4
                      },
                      {
                          "name": "경유지",
                          "x": 127.11341931516797,
                          "y": 37.39622783738649,
                          "distance": 57,
                          "duration": 26,
                          "type": 1000,
                          "guidance": "경유지",
                          "road_index": -1
                      }
                  ]
              },
              {
                  "distance": 1119,
                  "duration": 294,
                  "bound": {
                      "min_x": 127.10863660151416,
                      "min_y": 37.39622538141045,
                      "max_x": 127.11341931516797,
                      "max_y": 37.40242613861426
                  },
                  "roads": [
                      {
                          "name": "대왕판교로606번길",
                          "distance": 29,
                          "duration": 6,
                          "traffic_speed": 17.0,
                          "traffic_state": 2,
                          "vertexes": [
                              127.11341931516797,
                              37.39622783738649,
                              127.11309181718316,
                              37.39622538141045
                          ]
                      },
                      {
                          "name": "분당내곡로",
                          "distance": 392,
                          "duration": 62,
                          "traffic_speed": 25.0,
                          "traffic_state": 3,
                          "vertexes": [
                              127.11309181718316,
                              37.39622538141045,
                              127.11307829458244,
                              37.39641450597087,
                              127.1130803894646,
                              37.398153598349445,
                              127.11307964622586,
                              37.39821666808455,
                              127.1130784782746,
                              37.3983157776669,
                              127.11308594924428,
                              37.39864022099831,
                              127.11311303420219,
                              37.39921711263319,
                              127.11313041857109,
                              37.39965877010523,
                              127.11312925062586,
                              37.399757879664605
                          ]
                      },
                      {
                          "name": "대왕판교로644번길",
                          "distance": 124,
                          "duration": 50,
                          "traffic_speed": 20.0,
                          "traffic_state": 3,
                          "vertexes": [
                              127.11312925062586,
                              37.399757879664605,
                              127.11274420726458,
                              37.39984509856906,
                              127.11173886656147,
                              37.39985557194009
                          ]
                      },
                      {
                          "name": "",
                          "distance": 559,
                          "duration": 173,
                          "traffic_speed": 13.0,
                          "traffic_state": 2,
                          "vertexes": [
                              127.11173886656147,
                              37.39985557194009,
                              127.11175987981302,
                              37.40094603107842,
                              127.11174254485269,
                              37.40241465350646,
                              127.11170855662199,
                              37.402423408918274,
                              127.10967543155922,
                              37.40242613861426,
                              127.10863660151416,
                              37.40240029023456
                          ]
                      },
                      {
                          "name": "",
                          "distance": 15,
                          "duration": 3,
                          "traffic_speed": 16.0,
                          "traffic_state": 0,
                          "vertexes": [
                              127.10863660151416,
                              37.40240029023456,
                              127.1086494963113,
                              37.402265226201656
                          ]
                      }
                  ],
                  "guides": [
                      {
                          "name": "경유지",
                          "x": 127.11341931516797,
                          "y": 37.39622783738649,
                          "distance": 0,
                          "duration": 0,
                          "type": 1000,
                          "guidance": "판교테크노밸리 양재 내곡 방면으로 경유지",
                          "road_index": 0
                      },
                      {
                          "name": "판교역사거리",
                          "x": 127.11309181718316,
                          "y": 37.39622538141045,
                          "distance": 29,
                          "duration": 6,
                          "type": 2,
                          "guidance": "동판교IC 내곡,서울 방면으로 우회전",
                          "road_index": 1
                      },
                      {
                          "name": "삼평사거리",
                          "x": 127.11312925062586,
                          "y": 37.399757879664605,
                          "distance": 392,
                          "duration": 62,
                          "type": 1,
                          "guidance": "대왕판교로 경기창조경제혁신센터 방면으로 좌회전",
                          "road_index": 2
                      },
                      {
                          "name": "",
                          "x": 127.11173886656147,
                          "y": 37.39985557194009,
                          "distance": 124,
                          "duration": 50,
                          "type": 2,
                          "guidance": "우회전",
                          "road_index": 3
                      },
                      {
                          "name": "",
                          "x": 127.10863660151416,
                          "y": 37.40240029023456,
                          "distance": 559,
                          "duration": 173,
                          "type": 1,
                          "guidance": "좌회전",
                          "road_index": 4
                      },
                      {
                          "name": "목적지",
                          "x": 127.1086494963113,
                          "y": 37.402265226201656,
                          "distance": 15,
                          "duration": 3,
                          "type": 101,
                          "guidance": "목적지",
                          "road_index": -1
                      }
                  ]
              }
          ]
      }
  ]
}
```

요청 응답에 대한 객체 정보는 다음과 같습니다.

**표 4 응답 객체**

|Name|Type|Description|Required|
|---|---|---|---|
|`trans_id`|String|경로 요청 ID|필수|
|`routes`|Object[]|경로 정보  <br>  <br>`alternatives`가 `true`인 경우 한 개 이상의 경로 제공 가능|필수|
|`result_code`|Int|[경로 탐색 결과 코드](https://developers.kakaomobility.com/guide/navi-api/reference/)|필수|
|`result_msg`|String|경로 탐색 결과 메시지|필수|
|`summary`|Object|경로 요약 정보|필수|
|`origin`|Object|출발지 정보|필수|
|`name`|String|출발지 이름|필수|
|`x`|Double|X 좌표(경도)|필수|
|`y`|Double|Y 좌표(위도)|필수|
|`destination`|Object|목적지 정보|필수|
|`name`|String|목적지 이름|필수|
|`x`|Double|X 좌표(경도)|필수|
|`y`|Double|Y 좌표(위도)|필수|
|`waypoints`|Object[]|경유지 정보|필수|
|`name`|String|경유지 이름|필수|
|`x`|Double|X 좌표(경도)|필수|
|`y`|Double|Y 좌표(위도)|필수|
|`priority`|String|경로 탐색 우선순위 옵션|필수|
|`bound`|Object|모든 경로를 포함하는 사각형의 바운딩 박스(Bounding box)|선택|
|`min_x`|Double|바운딩 박스 왼쪽 하단의 X 좌표|필수|
|`min_y`|Double|바운딩 박스 왼쪽 하단의 Y 좌표|필수|
|`max_x`|Double|바운딩 박스 오른쪽 상단의 X 좌표|필수|
|`max_y`|Double|바운딩 박스 오른쪽 상단의 Y 좌표|필수|
|`fare`|Object|요금 정보|필수|
|`taxi`|Int|택시 요금(원)|필수|
|`toll`|Int|통행 요금(원)|필수|
|`distance`|Int|전체 검색 결과 거리(미터)|필수|
|`duration`|Int|목적지까지 소요 시간(초)|필수|
|`sections`|Object[]|구간별 경로 정보  <br>  <br>경유지가 존재할 경우 {경유지 수 + 1} 만큼의 섹션(경로 구간) 생성  <br>(예: 경유지 수가 2개인 경우 총 3개의 섹션 정보가 생성,  <br>section1: 출발지 → 경유지 1  <br>section2: 경유지 1 → 경유지 2  <br>section3: 경유지 2 → 목적지)|필수|
|`distance`|Int|섹션 거리(미터)|필수|
|`duration`|Int|전체 검색 결과 이동 시간(초)|필수|
|`bound`|Object|모든 경로를 포함하는 사각형의 바운딩 박스(Bounding box)  <br>  <br>`summary`가 `false`인 경우에만 제공|선택|
|`min_x`|Double|바운딩 박스 왼쪽 하단의 X 좌표|필수|
|`min_y`|Double|바운딩 박스 왼쪽 하단의 Y 좌표|필수|
|`max_x`|Double|바운딩 박스 오른쪽 상단의 X 좌표|필수|
|`max_y`|Double|바운딩 박스 오른쪽 상단의 Y 좌표|필수|
|`roads`|Object[]|도로 정보  <br>  <br>`summary`가 `false`인 경우에만 제공|선택|
|`name`|String|도로명|필수|
|`distance`|Int|도로 길이(미터)|필수|
|`duration`|Int|예상 이동 시간(초)  <br>  <br>현재 예상 이동 시간 및 실제 이동 시간은 동일한 값으로 설정|필수|
|`traffic_speed`|Double|현재 교통 정보 속도(km/h)|필수|
|`traffic_state`|Int|[현재 교통 정보 상태](https://developers.kakaomobility.com/guide/navi-api/reference/)|필수|
|`vertexes`|Double[]|X, Y 좌표로 구성된 1차원 배열  <br>  <br>(예: [127.10966790676201, 37.394469584427156, 127.10967141980313, 37.39512739646385] )|필수|
|`guides`|Object[]|안내 정보  <br>  <br>`summary`가 `false`인 경우에만 제공|선택|
|`name`|String|명칭|필수|
|`x`|Double|X 좌표(경도)|필수|
|`y`|Double|Y 좌표(위도)|필수|
|`distance`|Int|이전 가이드 지점부터 현재 가이드 지점까지 거리(미터)|필수|
|`duration`|Int|이전 가이드 지점부터 현재 가이드 지점까지 시간(초)|필수|
|`type`|Int|[안내 타입](https://developers.kakaomobility.com/guide/navi-api/reference/#type-%EC%95%88%EB%82%B4-%ED%83%80%EC%9E%85)|필수|
|`guidance`|String|안내 문구|필수|
|`road_index`|Int|현재 가이드에 대한 링크 인덱스|필수|
# 다중 출발지 길찾기

한 개 이상의 출발지에서 하나의 목적지까지의 경로 요약 정보를 제공합니다. 다중 출발지 길찾기의 경우 경로의 요약 정보를 제공하기 때문에 상세 정보를 받으려면 [자동차 길찾기](https://developers.kakaomobility.com/guide/navi-api/directions/)를 추가적으로 요청해야 합니다.

출발지는 최대 30개까지 설정할 수 있으며 30개를 초과하여 출발지를 설정하려면 제휴 문의에서 제휴를 신청하세요.

DANGER

해당 API를 사용하기 위해서는 REST API 키 값이 반드시 필요합니다. [시작하기](https://developers.kakaomobility.com/guide/navi-api/start/)에서 앱 등록과 REST API 키 값 확인 방법을 참고하세요.

## Request

요청 호출 방식과 각 요청 헤더에 포함될 내용을 안내합니다. 요청이 실패할 경우 [문제 해결하기](https://developers.kakaomobility.com/guide/navi-api/solution/)에서 에러에 대한 상세 내용을 확인하세요.

### 호출 방식

**표 1 호출 방식**

|Method|URL|
|---|---|
|`POST`|[https://apis-navi.kakaomobility.com/v1/origins/directions](https://apis-navi.kakaomobility.com/v1/origins/directions)|

### 요청 헤더(Header)

**표 2 요청 헤더**

|Parameter|Description|
|---|---|
|Authorization|KakaoAK ${REST_API_KEY}  <br>  <br>{REST_API_KEY}: 카카오디벨로퍼스에서 발급 받은 REST API 키|
|Content-Type|`application/json`|

### 요청 코드 예제

```
curl -v -X POST "https://apis-navi.kakaomobility.com/v1/origins/directions" \
-H "Content-Type: application/json" \
-H "Authorization: KakaoAK ${REST_API_KEY}" \ // 카카오디벨로퍼스에서 발급 받은 API 키 값
-d '{
"origins": [
  {
    "x": "127.1331694942593",
    "y": "37.4463137562622",
    "key": "0"
  },
  {
    "x": "127.13243772760565",
    "y": "37.44148514309502",
    "key": "1"
  }
],
"destination": {
  "x": "127.14816492905383",
  "y": "37.4401690139602"
},
"radius": 5000
}'
```

요청에 대한 파라미터는 다음과 같습니다.

**표 3 요청 파라미터**

|Name|Type|Description|Required|
|---|---|---|---|
|`origins`|Object[]|출발지, 최대 30개까지 허용|필수|
|`x`|Double|X 좌표(경도)|필수|
|`y`|Double|Y 좌표(위도)|필수|
|`key`|String|각 출발지를 구분하기 위한 임의의 문자열 지정|필수|
|`destination`|Object|목적지|필수|
|`name`|String|목적지 이름|선택|
|`x`|Double|X 좌표(경도)|필수|
|`y`|Double|Y 좌표(위도)|필수|
|`radius`|Int|길찾기 반경(미터)(최대: 10000)|필수|
|`priority`|String|경로 탐색 우선순위 옵션  <br>  <br>다음 중 하나:  <br>`TIME`: 최단 시간  <br>`DISTANCE`: 최단 경로  <br>(기본값: `TIME`)|선택|
|`avoid`|String[]|경로 탐색 제한 옵션  <br>  <br>다음 값 사용 가능:  <br>`ferries`: 페리 항로  <br>`toll`: 유료 도로  <br>`motorway`: 자동차 전용 도로  <br>`schoolzone`: 어린이 보호 구역  <br>`uturn`: 유턴  <br>(기본값: `null`)  <br>  <br>여러 개의 제한 옵션을 사용하려면 다음과 같이 연결  <br>(예: ["`ferries`", "`motorway`"])|선택|
|`roadevent`|Int|유고(교통사고, 행사, 재난, 도로 공사 등의 교통 장애)로 인한 도로 통제 정보 반영 옵션  <br>  <br>`0`: 전체 차선 통제(도로 전체 통제) 정보를 반영  <br>`1`: 출발지 및 목적지 주변의 전체 차선 통제 정보 반영 안 함  <br>`2`: 모든 구간의 전체 차선 통제 정보 반영 안 함  <br>(기본값: `0`)|선택|

## Response

응답 성공 시 요청에 대한 성공 여부를 [HTTP 상태 코드](https://developers.kakaomobility.com/guide/navi-api/solution/#http-%EC%83%81%ED%83%9C-%EC%BD%94%EB%93%9C)로, 요청 본문은 `JSON` 포맷으로 전달합니다.

### 응답 코드 예제

```
{
  "trans_id": "a2653095f26445dba15d736c5714d86a",
  "routes": [
      {
          "result_code": 0,
          "result_msg": "길찾기 성공",
          "key": "0",
          "summary": {
              "distance": 2305,
              "duration": 615
          }
      },
      {
          "result_code": 0,
          "result_msg": "길찾기 성공",
          "key": "1",
          "summary": {
              "distance": 1878,
              "duration": 408
          }
      }
  ]
}
```

요청 응답에 대한 객체 정보는 다음과 같습니다.

**표 4 응답 객체**

|Name|Type|Description|Required|
|---|---|---|---|
|`trans_id`|String|경로 요청 ID|필수|
|`routes`|Object[]|경로 정보, 경로 수만큼 생성|필수|
|`result_code`|Int|[경로 탐색 결과 코드](https://developers.kakaomobility.com/guide/navi-api/reference/)|필수|
|`result_msg`|String|경로 탐색 결과 메시지|필수|
|`key`|String|`origins`의 `key` 값으로 지정한 각 출발지의 키 값|필수|
|`summary`|Object|경로 요약 정보|필수|
|`distance`|Int|전체 검색 결과 거리(미터)|필수|
|`duration`|Int|목적지까지 소요 시간(초)|필수|
# 다중 목적지 길찾기

하나의 출발지에서 한 개 이상의 목적지까지의 경로 요약 정보를 제공합니다. 다중 목적지 길찾기의 경우 경로의 요약 정보를 제공하기 때문에 상세 정보를 받으려면 [자동차 길찾기](https://developers.kakaomobility.com/guide/navi-api/directions/)를 추가적으로 요청해야 합니다.

목적지는 최대 30개까지 설정할 수 있으며 30개를 초과하여 목적지를 설정하려면 제휴 문의에서 제휴를 신청하세요.

DANGER

해당 API를 사용하기 위해서는 REST API 키 값이 반드시 필요합니다. [시작하기](https://developers.kakaomobility.com/guide/navi-api/start/)에서 앱 등록과 REST API 키 값 확인 방법을 참고하세요.

## Request

요청 호출 방식과 각 요청 헤더에 포함될 내용을 안내합니다. 요청이 실패할 경우 [문제 해결하기](https://developers.kakaomobility.com/guide/navi-api/solution/)에서 에러에 대한 상세 내용을 확인하세요.

### 호출 방식

**표 1 호출 방식**

|Method|URL|
|---|---|
|`POST`|[https://apis-navi.kakaomobility.com/v1/destinations/directions](https://apis-navi.kakaomobility.com/v1/destinations/directions)|

### 요청 헤더(Header)

**표 2 요청 헤더**

|Parameter|Description|
|---|---|
|Authorization|KakaoAK ${REST_API_KEY}  <br>  <br>{REST_API_KEY}: 카카오디벨로퍼스에서 발급 받은 REST API 키|
|Content-Type|`application/json`|

### 요청 코드 예제

```
curl -v -X POST "https://apis-navi.kakaomobility.com/v1/destinations/directions" \
-H "Content-Type: application/json" \
-H "Authorization: KakaoAK ${REST_API_KEY}" \  // 카카오디벨로퍼스에서 발급 받은 API 키 값
-d '{
"origin": {
  "x": "127.13144306487084",
  "y": " 37.44134209110179"
},
"destinations": [
  {
    "x": "127.14112393388389",
    "y": "37.44558371517034",
    "key": "0"
  },
  {
    "x": "127.14192737519186",
    "y": "37.4401766683372",
    "key": "1"
  }
],
"radius": 5000
}'
```

요청에 대한 파라미터는 다음과 같습니다.

**표 3 요청 파라미터**

|Name|Type|Description|Required|
|---|---|---|---|
|`origin`|Object|출발지|필수|
|`name`|String|출발지 이름|선택|
|`x`|Double|X 좌표(경도)|필수|
|`y`|Double|Y 좌표(위도)|필수|
|`destinations`|Object[]|목적지, 최대 30개까지 허용|필수|
|`key`|String|각 목적지를 구분하기 위한 임의의 문자열 지정|필수|
|`x`|Double|X 좌표(경도)|필수|
|`y`|Double|Y 좌표(위도)|필수|
|`radius`|Int|길찾기 반경(미터)(최대: 10000)|필수|
|`priority`|String|경로 탐색 우선순위 옵션  <br>  <br>다음 중 하나:  <br>`TIME`: 최단 시간  <br>`DISTANCE`: 최단 경로  <br>(기본값: `TIME`)|선택|
|`avoid`|String[]|경로 탐색 제한 옵션  <br>  <br>다음 값 사용 가능:  <br>`ferries`: 페리 항로  <br>`toll`: 유료 도로  <br>`motorway`: 자동차 전용 도로  <br>`schoolzone`: 어린이 보호 구역  <br>`uturn`: 유턴  <br>(기본값: `null`)  <br>  <br>여러 개의 제한 옵션을 사용하려면 다음과 같이 연결  <br>(예: ["`ferries`", "`motorway`"])|선택|
|`roadevent`|Int|유고(교통사고, 행사, 재난, 도로 공사 등의 교통 장애)로 인한 도로 통제 정보 반영 옵션  <br>  <br>`0`: 전체 차선 통제(도로 전체 통제) 정보를 반영  <br>`1`: 출발지 및 목적지 주변의 전체 차선 통제 정보 반영 안 함  <br>`2`: 모든 구간의 전체 차선 통제 정보 반영 안 함  <br>(기본값: `0`)|선택|

## Response

응답 성공 시 요청에 대한 성공 여부를 [HTTP 상태 코드](https://developers.kakaomobility.com/guide/navi-api/solution/)로, 요청 본문은 `JSON` 포맷으로 전달합니다.

### 응답 코드 예제

```
{
  "trans_id": "b2520cb429004460a4d5f389d108db38",
  "routes": [
      {
          "result_code": 0,
          "result_msg": "길찾기 성공",
          "key": "0",
          "summary": {
              "distance": 1307,
              "duration": 307
          }
      },
      {
          "result_code": 0,
          "result_msg": "길찾기 성공",
          "key": "1",
          "summary": {
              "distance": 1323,
              "duration": 320
          }
      }
  ]
}
```

요청 응답에 대한 객체 정보는 다음과 같습니다.

**표 4 응답 객체**

|Name|Type|Description|Required|
|---|---|---|---|
|`trans_id`|String|경로 요청 ID|필수|
|`routes`|Object[]|경로 정보, 경로 수만큼 생성|필수|
|`result_code`|Int|[경로 탐색 결과 코드](https://developers.kakaomobility.com/guide/navi-api/reference/)|필수|
|`result_msg`|String|경로 탐색 결과 메시지|필수|
|`key`|String|`destinations`의 `key` 값으로 지정한 각 목적지의 키 값|필수|
|`summary`|Object|경로 요약 정보|필수|
|`distance`|Int|전체 검색 결과 거리(미터)|필수|
|`duration`|Int|목적지까지 소요 시간(초)|필수|
# 미래 운행 정보 길찾기

미래의 어느 특정 시간을 지정하고 해당 시간을 기준으로 하나의 출발지에서 하나의 목적지까지로의 경로 정보를 제공합니다. 출발 시간은 반드시 현재 시간 이후의 시간으로 지정해야 합니다. 경유지는 최대 5개까지 추가할 수 있으며 모든 경유지를 포함한 경로의 총 거리는 1,500 km 미만으로 설정해야 합니다.

DANGER

해당 API를 사용하기 위해서는 REST API 키 값이 반드시 필요합니다. [시작하기](https://developers.kakaomobility.com/guide/navi-api/start/)에서 앱 등록과 REST API 키 값 확인 방법을 참고하세요.

## Request

요청 호출 방식과 각 요청 헤더에 포함될 내용을 안내합니다. 요청이 실패할 경우 [문제 해결하기](https://developers.kakaomobility.com/guide/navi-api/solution/)에서 에러에 대한 상세 내용을 확인하세요.

### 호출 방식

**표 1 호출 방식**

|Method|URL|
|---|---|
|`GET`|[https://apis-navi.kakaomobility.com/v1/future/directions](https://apis-navi.kakaomobility.com/v1/future/directions)|

### 요청 헤더(Header)

**표 2 요청 헤더**

|Parameter|Description|
|---|---|
|Authorization|KakaoAK ${REST_API_KEY}  <br>  <br>{REST_API_KEY}: 카카오디벨로퍼스에서 발급 받은 REST API 키|
|Content-Type|`application/json`|

### 요청 코드 예제

```
curl -v -X GET "https://apis-navi.kakaomobility.com/v1/future/directions?origin=127.11015314141542,37.39472714688412,angle=270&destination=127.10824367964793,37.401937080111644&departure_time=202109170000" \
  -H "Authorization: KakaoAK ${REST_API_KEY}" // 카카오디벨로퍼스에서 발급 받은 API 키 값
```

요청에 대한 파라미터는 다음과 같습니다.

**표 3 요청 파라미터**

|Name|Type|Description|Required|
|---|---|---|---|
|`departure_time`|String|출발 시간, YYYYMMDDHHMM 형식으로 현재 시간 이후 시간 설정  <br>(예: 202107171010)|필수|
|`origin`|String|출발지  <br>  <br>다음 중 하나의 형식으로 요청:  <br>1. `${X좌표},${Y좌표},name=${출발지명}`  <br>(예: "`127.111202,37.394912,name=판교역`")  <br>  <br>2. `${X좌표},${Y좌표}`  <br>(예: "`127.111202,37.394912`")  <br>  <br>3.`${X좌표},${Y좌표},${angle}`  <br>(예:"`127.111202,37.394912,angle=90`")  <br>  <br>`angle`: 출발지의 초기 진행 방향 지정. 0~360 범위의 정수를 입력  <br>(각도에 따른 방향: 0 = 북쪽, 90 = 동쪽, 180 = 남쪽, 270 = 서쪽 등 시계 방향으로 반영. 범위를 벗어난 값은 무시)|필수|
|`destination`|String|목적지  <br>  <br>다음 중 하나의 형식으로 요청:  <br>`${X좌표},${Y좌표},name=${목적지명}` 또는  <br>`${X좌표},${Y좌표}`  <br>(예: "`127.111202,37.394912,name=판교역`" 또는   <br>"`127.111202,37.394912`")|필수|
|`waypoints`|String|경유지, 최대 5개까지 허용  <br>모든 경유지를 포함한 경로의 총 거리는 1,500 km 미만으로 설정해야 함.  <br>  <br>경유지 수만큼 `${X좌표},${Y좌표},name=${경유지명}` 또는 `${X좌표},${Y좌표}`를 `\|`(또는 인코딩 된 문자인 `%7C`)로 연결하여 입력  <br>(예: "`127.111202,37.394912,name=판교역 \| 127.112275,37.392815`")|선택|
|`priority`|String|경로 탐색 우선순위 옵션  <br>  <br>다음 중 하나:  <br>`RECOMMEND`: 추천 경로  <br>`TIME`: 최단 시간  <br>`DISTANCE`: 최단 경로  <br>(기본값: `RECOMMEND`)|선택|
|`avoid`|String|경로 탐색 제한 옵션  <br>  <br>다음 값 사용 가능:  <br>`ferries`: 페리 항로  <br>`toll`: 유료 도로  <br>`motorway`: 자동차 전용 도로  <br>`schoolzone`: 어린이 보호 구역  <br>`uturn`: 유턴  <br>(기본값: `null`)  <br>  <br>여러 개의 제한 옵션을 사용하려면 `\|`(또는 인코딩 된 문자인 `%7C`)로 연결  <br>(예: `avoid=motorway\|ferries`)|선택|
|`roadevent`|Int|유고(교통사고, 행사, 재난, 도로 공사 등의 교통 장애)로 인한 도로 통제 정보 반영 옵션  <br>  <br>`0`: 전체 차선 통제(도로 전체 통제) 정보를 반영  <br>`1`: 출발지 및 목적지 주변의 전체 차선 통제 정보 반영 안 함  <br>`2`: 모든 구간의 전체 차선 통제 정보 반영 안 함  <br>(기본값: `0`)|선택|
|`alternatives`|Boolean|대안 경로 제공 여부  <br>  <br>`true`: 대안 경로 제공  <br>`false`: 대안 경로 미제공  <br>(기본값: `false`)|선택|
|`road_details`|Boolean|상세 도로 정보 제공 여부  <br>  <br>`true`: 상세 도로 정보 제공  <br>`false`: 상세 도로 정보 미제공  <br>(기본값: `false`)|선택|
|`car_type`|Int|[차종](https://developers.kakaomobility.com/guide/navi-api/reference/#car_type-%EC%B0%A8%EC%A2%85)  <br>  <br>(기본값: `1`)|선택|
|`car_fuel`|String|차량 유종 정보  <br>  <br>다음 중 하나:  <br>`GASOLINE`: 휘발유  <br>`DIESEL`: 경유  <br>`LPG`: LPG  <br>(기본값: `GASOLINE`)|선택|
|`car_hipass`|Boolean|하이패스 장착 여부  <br>  <br>`true`: 하이패스 장착  <br>`false`: 하이패스 미장착  <br>(기본값: `false`)|선택|
|`summary`|Boolean|경로 정보 응답 범위 설정  <br>  <br>`true`: 요약 정보만 반환 (`sections`의 `bound`, `roads`, `guides` 정보 제외)  <br>`false`: 요약 정보와 상세 정보 반환(`sections`의 `bound`, `roads`, `guides` 정보 포함)  <br>(기본값: `false`)|선택|

## Response

응답 성공 시 요청에 대한 성공 여부를 [HTTP 상태 코드](https://developers.kakaomobility.com/guide/navi-api/solution/)로, 요청 본문은 `JSON` 포맷으로 전달합니다.

### 응답 코드 예제

```
{
  "trans_id": "0194de169a8d79c98f718af8c8410932",
  "routes": [
      {
          "result_code": 0,
          "result_msg": "길찾기 성공",
          "summary": {
              "origin": {
                  "name": "",
                  "x": 127.11015051307636,
                  "y": 37.394725518530834
              },
              "destination": {
                  "name": "",
                  "x": 127.10823557165544,
                  "y": 37.401928707331656
              },
              "waypoints": [],
              "priority": "RECOMMEND",
              "bound": {
                  "min_x": 127.10873060789754,
                  "min_y": 37.39446252338457,
                  "max_x": 127.1098222529551,
                  "max_y": 37.40242724407785
              },
              "fare": {
                  "taxi": 5100,
                  "toll": 0
              },
              "distance": 1012,
              "duration": 304
          },
          "sections": [
              {
                  "distance": 1012,
                  "duration": 304,
                  "bound": {
                      "min_x": 127.10863660151416,
                      "min_y": 37.394469584427156,
                      "max_x": 127.10991634747967,
                      "max_y": 37.40242613861426
                  },
                  "roads": [
                      {
                          "name": "",
                          "distance": 22,
                          "duration": 5,
                          "traffic_speed": 16.0,
                          "traffic_state": 0,
                          "vertexes": [
                              127.10991634747967,
                              37.39447145478345,
                              127.10966790676201,
                              37.394469584427156
                          ]
                      },
                      {
                          "name": "판교역로",
                          "distance": 883,
                          "duration": 224,
                          "traffic_speed": 11.0,
                          "traffic_state": 2,
                          "vertexes": [
                              127.10966790676201,
                              37.394469584427156,
                              127.10967141980313,
                              37.39512739646385,
                              127.10968100356395,
                              37.396226781360426,
                              127.10967417816033,
                              37.39775855885587,
                              127.10968323318781,
                              37.39794785293074,
                              127.10967534594126,
                              37.39861458950405,
                              127.10967214334856,
                              37.399840028043634,
                              127.1096931266438,
                              37.40093048716485,
                              127.10967543155922,
                              37.40242613861426
                          ]
                      },
                      {
                          "name": "판교역로241번길",
                          "distance": 92,
                          "duration": 72,
                          "traffic_speed": 12.0,
                          "traffic_state": 2,
                          "vertexes": [
                              127.10967543155922,
                              37.40242613861426,
                              127.10863660151416,
                              37.40240029023456
                          ]
                      },
                      {
                          "name": "",
                          "distance": 15,
                          "duration": 3,
                          "traffic_speed": 16.0,
                          "traffic_state": 0,
                          "vertexes": [
                              127.10863660151416,
                              37.40240029023456,
                              127.1086494963113,
                              37.402265226201656
                          ]
                      }
                  ],
                  "guides": [
                      {
                          "name": "출발지",
                          "x": 127.10991634747967,
                          "y": 37.39447145478345,
                          "distance": 0,
                          "duration": 0,
                          "type": 100,
                          "guidance": "출발지",
                          "road_index": 0
                      },
                      {
                          "name": "",
                          "x": 127.10966790676201,
                          "y": 37.394469584427156,
                          "distance": 22,
                          "duration": 5,
                          "type": 2,
                          "guidance": "우회전",
                          "road_index": 1
                      },
                      {
                          "name": "",
                          "x": 127.10967543155922,
                          "y": 37.40242613861426,
                          "distance": 883,
                          "duration": 224,
                          "type": 1,
                          "guidance": "좌회전",
                          "road_index": 2
                      },
                      {
                          "name": "",
                          "x": 127.10863660151416,
                          "y": 37.40240029023456,
                          "distance": 92,
                          "duration": 72,
                          "type": 1,
                          "guidance": "좌회전",
                          "road_index": 3
                      },
                      {
                          "name": "목적지",
                          "x": 127.1086494963113,
                          "y": 37.402265226201656,
                          "distance": 15,
                          "duration": 3,
                          "type": 101,
                          "guidance": "목적지",
                          "road_index": -1
                      }
                  ]
              }
          ]
      }
  ]
}
```

요청 응답에 대한 객체 정보는 다음과 같습니다.

**표 4 응답 객체**

|Name|Type|Description|Required|
|---|---|---|---|
|`trans_id`|String|경로 요청 ID|필수|
|`routes`|Object[]|경로 정보  <br>  <br>`alternatives`가 `true`인 경우 한 개 이상의 경로 제공 가능|필수|
|`result_code`|Int|[경로 탐색 결과 코드](https://developers.kakaomobility.com/guide/navi-api/reference/)|필수|
|`result_msg`|String|경로 탐색 결과 메시지|필수|
|`summary`|Object|경로 요약 정보|필수|
|`origin`|Object|출발지 정보|필수|
|`name`|String|출발지 이름|필수|
|`x`|Double|X 좌표(경도)|필수|
|`y`|Double|Y 좌표(위도)|필수|
|`destination`|Object|목적지 정보|필수|
|`name`|String|목적지 이름|필수|
|`x`|Double|X 좌표(경도)|필수|
|`y`|Double|Y 좌표(위도)|필수|
|`waypoints`|Object[]|경유지 정보|필수|
|`name`|String|경유지 이름|필수|
|`x`|Double|X 좌표(경도)|필수|
|`y`|Double|Y 좌표(위도)|필수|
|`priority`|String|경로 탐색 우선순위 옵션|필수|
|`bound`|Object|모든 경로를 포함하는 사각형의 바운딩 박스(Bounding box)|선택|
|`min_x`|Double|바운딩 박스 왼쪽 하단의 X 좌표|필수|
|`min_y`|Double|바운딩 박스 왼쪽 하단의 Y 좌표|필수|
|`max_x`|Double|바운딩 박스 오른쪽 상단의 X 좌표|필수|
|`max_y`|Double|바운딩 박스 오른쪽 상단의 Y 좌표|필수|
|`fare`|Object|요금 정보|필수|
|`taxi`|Int|택시 요금(원)|필수|
|`toll`|Int|통행 요금(원)|필수|
|`distance`|Int|전체 검색 결과 거리(미터)|필수|
|`duration`|Int|목적지까지 소요 시간(초)|필수|
|`sections`|Object[]|구간별 경로 정보  <br>  <br>경유지가 존재할 경우 {경유지 수 + 1} 만큼의 섹션(경로 구간) 생성  <br>(예: 경유지 수가 2개인 경우 총 3개의 섹션 정보가 생성,  <br>section1: 출발지 → 경유지 1  <br>section2: 경유지 1 → 경유지 2  <br>section3: 경유지 2 → 목적지)|필수|
|`distance`|Int|섹션 거리(미터)|필수|
|`duration`|Int|전체 검색 결과 이동 시간(초)|필수|
|`bound`|Object|모든 경로를 포함하는 사각형의 바운딩 박스(Bounding box)  <br>  <br>`summary`가 `false`인 경우에만 제공|선택|
|`min_x`|Double|바운딩 박스 왼쪽 하단의 X 좌표|필수|
|`min_y`|Double|바운딩 박스 왼쪽 하단의 Y 좌표|필수|
|`max_x`|Double|바운딩 박스 오른쪽 상단의 X 좌표|필수|
|`max_y`|Double|바운딩 박스 오른쪽 상단의 Y 좌표|필수|
|`roads`|Object[]|도로 정보  <br>  <br>`summary`가 `false`인 경우에만 제공|선택|
|`name`|String|도로명|필수|
|`distance`|Int|도로 길이(미터)|필수|
|`duration`|Int|예상 이동 시간(초)  <br>  <br>현재 예상 이동 시간 및 실제 이동 시간은 동일한 값으로 설정|필수|
|`traffic_speed`|Double|현재 교통 정보 속도(km/h)|필수|
|`traffic_state`|Int|[현재 교통 정보 상태](https://developers.kakaomobility.com/guide/navi-api/reference/)|필수|
|`vertexes`|Double[]|X, Y 좌표로 구성된 1차원 배열  <br>  <br>(예: [127.10966790676201, 37.394469584427156, 127.10967141980313, 37.39512739646385] )|필수|
|`guides`|Object[]|안내 정보  <br>  <br>`summary`가 `false`인 경우에만 제공|선택|
|`name`|String|명칭|필수|
|`x`|Double|X 좌표(경도)|필수|
|`y`|Double|Y 좌표(위도)|필수|
|`distance`|Int|이전 가이드 지점부터 현재 가이드 지점까지 거리(미터)|필수|
|`duration`|Int|이전 가이드 지점부터 현재 가이드 지점까지 시간(초)|필수|
|`type`|Int|[안내 타입](https://developers.kakaomobility.com/guide/navi-api/reference/#type-%EC%95%88%EB%82%B4-%ED%83%80%EC%9E%85)|필수|
|`guidance`|String|안내 문구|필수|
|`road_index`|Int|현재 가이드에 대한 링크 인덱스|필수|
# 레퍼런스

길찾기 API에서 사용하는 공통 클래스 정보를 안내합니다.

### result_code: 경로 탐색 결과 코드

**표 1 경로 탐색 결과 코드**

|Code|Description|
|---|---|
|0|길찾기 성공|
|1|길찾기 결과를 찾을 수 없음|
|101|경유지 지점 주변의 도로를 탐색할 수 없음|
|102|시작 지점 주변의 도로를 탐색할 수 없음|
|103|도착 지점 주변의 도로를 탐색할 수 없음|
|104|출발지와 도착지가 5 m 이내로 설정된 경우 경로를 탐색할 수 없음|
|105|시작 지점 주변의 도로에 유고 정보(교통 장애)가 있음|
|106|도착 지점 주변의 도로에 유고 정보(교통 장애)가 있음|
|107|경유지 주변의 도로에 유고 정보(교통 장애)가 있음.  <br>result_message에 경유지의 순번이 표시되며 번호는 1번부터 시작함  <br>  <br>예시)  <br>result_code: 107  <br>result_message: 경유지에 유고 정보 존재: 1번 경유지|
|201|다중 출발지: 출발지가 탐색 영역에 포함되지 않음|
|202|다중 출발지: 출발지 최대 개수 초과 도로 선택 실패|
|203|다중 출발지: 목적지 도로 선택 실패|
|204|다중 출발지: 경로 탐색 처리 시간 제한|
|205|다중 출발지: 출발지 주변의 유고 정보(교통 장애)로 인한 통행 불가|
|206|다중 출발지: 목적지 주변의 유고 정보(교통 장애)로 인한 통행 불가|
|207|다중 출발지: 출발지가 설정한 길찾기 반경 범위를 벗어남|
|301|다중 목적지: 출발지 도로 선택 실패|
|302|다중 목적지: 목적지 도로 선택 실패|
|303|다중 목적지: 목적지 최대 개수 초과로 인해 경로 탐색 실패|
|304|다중 목적지: 목적지가 설정한 길찾기 반경 범위를 벗어남|

### traffic_state: 현재 교통 정보 상태 코드

**표 2 현재 교통 정보 상태 코드**

|Code|Description|
|---|---|
|0|교통 상태 정보 없음|
|1|교통 정체|
|2|교통 지체|
|3|교통 서행|
|4|교통 원활|
|6|교통사고(통행 불가)|

### car_type: 차종

**표 3 차종**

|Value|차종|분류 기준|예시|
|---|---|---|---|
|1|소형|2축 차량, 윤폭 279.4 mm 이하|승용차, 16인승 이하 승합차, 2.5 톤 미만 화물차|
|2|중형|2축 차량, 윤폭 279.4 mm 초과, 윤거 1,800 mm 이하|승합차 17-32인승, 2.5~5.5 톤 화물차|
|3|대형|2축 차량, 윤폭 279.4 mm 초과, 윤거 1,800 mm 초과|승합차 33인승 이상, 5.5~10 톤 화물차|
|4|대형 화물|3축 차량|10~20 톤 화물차|
|5|특수 화물|4축 이상 차량|20 톤 이상 화물차|
|6|경차|배기량이 1,000 cc 미만으로 길이 3.6 m, 너비 1.6 m, 높이 2.0 m 이하인 차량|-|
|7|이륜차|-|-|

### type: 안내 타입

**표 4 안내 타입**

|Value|Description|
|---|---|
|0|직진|
|1|좌회전|
|2|우회전|
|3|유턴|
|5|왼쪽 방향|
|6|오른쪽 방향|
|7|고속 도로 출구|
|8|왼쪽에 고속 도로 출구|
|9|오른쪽에 고속 도로 출구|
|10|고속 도로 입구|
|11|왼쪽에 고속 도로 입구|
|12|오른쪽에 고속 도로 입구|
|14|고가 도로 진입|
|15|지하 차도 진입|
|16|고가 도로 옆길|
|17|지하 차도 옆길|
|18|오른쪽 1시 방향|
|19|오른쪽 2시 방향|
|20|오른쪽 3시 방향|
|21|오른쪽 4시 방향|
|22|오른쪽 5시 방향|
|23|6시 방향|
|24|왼쪽 7시 방향|
|25|왼쪽 8시 방향|
|26|왼쪽 9시 방향|
|27|왼쪽 10시 방향|
|28|왼쪽 11시 방향|
|29|12시 방향|
|30|로터리에서 오른쪽 1시 방향|
|31|로터리에서 오른쪽 2시 방향|
|32|로터리에서 오른쪽 3시 방향|
|33|로터리에서 오른쪽 4시 방향|
|34|로터리에서 오른쪽 5시 방향|
|35|로터리에서 6시 방향|
|36|로터리에서 왼쪽 7시 방향|
|37|로터리에서 왼쪽 8시 방향|
|38|로터리에서 왼쪽 9시 방향|
|39|로터리에서 왼쪽 10시 방향|
|40|로터리에서 왼쪽 11시 방향|
|41|로터리에서 12시 방향|
|42|도시 고속 도로 출구|
|43|왼쪽에 도시 고속 도로 출구|
|44|오른쪽에 도시 고속 도로 출구|
|45|도시 고속 도로 입구|
|46|왼쪽에 도시 고속 도로 입구|
|47|오른쪽에 도시 고속 도로 입구|
|48|왼쪽 고속 도로 진입|
|49|오른쪽 고속 도로 진입|
|61|페리 항로 진입|
|62|페리 항로 진출|
|70|회전 교차로에서 오른쪽 1시 방향|
|71|회전 교차로에서 오른쪽 2시 방향|
|72|회전 교차로에서 오른쪽 3시 방향|
|73|회전 교차로에서 오른쪽 4시 방향|
|74|회전 교차로에서 오른쪽 5시 방향|
|75|회전 교차로에서 6시 방향|
|76|회전 교차로에서 왼쪽 7시 방향|
|77|회전 교차로에서 왼쪽 8시 방향|
|78|회전 교차로에서 왼쪽 9시 방향|
|79|회전 교차로에서 왼쪽 10시 방향|
|80|회전 교차로에서 왼쪽 11시 방향|
|81|회전 교차로에서 12시 방향|
|82|왼쪽 직진|
|83|오른쪽 직진|
|84|톨게이트 진입|
|85|원톨링 진입|
|86|분기 후 합류 구간 진입|
|100|출발지|
|101|목적지|
|1000|경유지|
|300|톨게이트|
|301|휴게소|
# 문제 해결하기

## 응답 코드

응답 코드는 요청에 대한 상태를 나타내는 HTTP 상태 코드(HTTP status code)와 에러에 대한 정보를 담은 에러 코드(Error code)로 나뉩니다. 요청 성공 시 HTTP 상태 코드 200과 함께 요청에 대한 응답 바디(response body)가 반환되고, 요청이 실패하였을 경우 `code`와 `msg`로 이루어진 에러 코드를 반환합니다.

### HTTP 상태 코드

HTTP 상태 코드(HTTP status code)란 응답 메시지의 첫 번째 줄에 나타나는 세 자리 숫자의 코드로 요청에 대한 상태 정보(성공 또는 실패)를 나타냅니다. 상태 코드는 크게 5가지로 분류되며, 상태 코드의 첫 번째 숫자로 응답의 종류를 파악할 수 있습니다. 자세한 정보는 [RFC 2616](https://tools.ietf.org/html/rfc2616#section-6)을 참고하세요.

다음은 API 요청에 대해 응답하는 상태 코드의 종류와 의미입니다.

**표 1 HTTP 상태 코드**

|Code|Status|Description|
|---|---|---|
|200 OK|성공|서버가 클라이언트의 요청을 성공적으로 수행  <br>  <br>응답 바디는 API마다 형식이 다를 수 있으니 각 API의 상세 설명 참고|
|400 Bad Request|실패|일반적인 오류  <br>  <br>서버가 클라이언트 오류를 감지해 요청을 처리하지 못한 상태. 주로 API에 필요한 필수 파라미터와 관련됨|
|401 Unauthorized|실패|인증 오류(주로 토큰 관련)  <br>  <br>해당 리소스에 대한 인증 자격 증명이 유효하지 않아 요청에 실패한 상태|
|403 Forbidden|실패|권한 오류  <br>  <br>서버에 요청은 전달되었으나 권한 문제로 인하여 요청이 거절된 상태|
|429 Too Many Request|실패|쿼터 초과  <br>  <br>정해진 쿼터(사용량)나 초당 요청 한도를 초과한 상태|
|500 Internal Server Error|실패|시스템 오류(서버 관련 오류를 총칭)  <br>  <br>요청을 처리하는 과정에서 서버가 예상치 못한 상태에 놓인 상태.|
|502 Bad Gateway|실패|시스템 오류  <br>  <br>서로 다른 프로토콜을 연결해 주는 게이트웨이(Gateway)가 잘못된 프로토콜을 연결하거나, 연결된 프로토콜에 문제가 있어 통신이 제대로 되지 않은 상태|
|503 Service Unavailable|실패|서비스 점검 중  <br>  <br>서버가 요청을 처리할 준비가 되지 않은 상태|

### 에러 코드

다음은 API 제품별로 발생할 수 있는 에러 코드 정보입니다. 에러 발생 시 `code` 중 해당하는 항목을 찾아 원인을 파악할 수 있습니다.

**표 2 공통 에러 코드**

|Code|HTTP status code|Description|
|---|---|---|
|-1|500|서버 내부에서 처리 중에 에러가 발생한 경우  <br>  <br>해결 방법: 재시도|
|-2|400|필수 인자가 포함되지 않은 경우나 호출 인자 값의 데이터 타입이 적절하지 않거나 허용된 범위를 벗어난 경우  <br>  <br>해결 방법: 요청 파라미터 확인|
|-3|403|해당 API를 사용하기 위해 필요한 기능(간편 가입, 동의 항목, 서비스 설정 등)이 활성화되지 않은 경우  <br>  <br>해결 방법: 카카오디벨로퍼스의 [앱](https://developers.kakao.com/console/app)에서 필요한 기능을 선택한 후, [활성화 설정]에서 ON으로 설정한 후 재호출|
|-4|403|계정이 제재된 경우나 해당 계정에 제재된 행동을 하는 경우|
|-5|403|해당 API에 대한 요청 권한이 없는 경우  <br>  <br>해결 방법: 검수 진행하여 권한 획득 후 재호출|
|-7|500|서비스 점검 또는 내부 문제가 있는 경우|
|-8|400|올바르지 않은 헤더로 요청한 경우  <br>  <br>해결 방법: 요청 헤더 확인|
|-9|400|서비스가 종료된 API를 호출한 경우|
|-10|400|허용된 요청 회수가 초과한 경우  <br>  <br>해결 방법: 허용된 쿼터 확인 후 쿼터 범위 내로 호출 조정, 쿼터 및 제한 참고|
|-401|401|유효하지 않은 앱 키나 액세스 토큰으로 요청한 경우, 등록된 앱 정보와 호출된 앱 정보가 불일치하는 경우  <br>  <br>해결 방법: 앱 키(App Key) 확인 또는 토큰 갱신, 개발자 사이트에 등록된 앱 정보 확인|
|-602|400|이미지 업로드 시 최대 용량을 초과하였을 경우|
|-603|400|이미지 업로드나 스크랩 요청과 같이 오래 걸리는 작업이 필요한 API에서 수행 시간이 오래 걸리는 경우|
|-903|400|등록되지 않은 개발자의 앱 키나 등록되지 않은 개발자의 앱 키로 구성된 액세스 토큰으로 요청한 경우|
|-911|400|지원하지 않는 포맷의 이미지를 업로드하는 경우|
|-9798|503|서비스 점검 중|
