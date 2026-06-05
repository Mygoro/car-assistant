이 문서는 지도 API를 사용하기 위한 전반적인 방법을 안내합니다.

## 기능 소개[](https://developers.kakao.com/docs/ko/kakaomap/common#overview)

지도 API는 카카오맵의 기능을 웹과 앱 플랫폼에 구현할 수 있도록 다양한 메서드와 라이브러리를 SDK로 제공합니다. 지도 API를 사용하면 다양한 위치 기반 서비스를 만들 수 있습니다.

![](https://developers.kakao.com/docs/_next/image?url=%2Fimg%2Fmap_intro_ko.png&w=2040&q=75)

## 설정하기[](https://developers.kakao.com/docs/ko/kakaomap/common#prerequisite)

지도 API를 사용하려면 아래 작업을 수행해야 합니다.

1. [카카오디벨로퍼스 앱 생성](https://developers.kakao.com/docs/ko/tutorial/start#create)
2. [플랫폼 키](https://developers.kakao.com/docs/ko/app-setting/app#key) 정보 등록
3. 카카오맵 API 사용 설정: [앱 관리 페이지](https://developers.kakao.com/console/app)의 [카카오맵] > [사용 설정]의 [상태]를 [ON]으로 설정
    
    - 이미 카카오맵을 사용 중인 앱을 소유한 개발자가, 다른 앱에서 추가로 카카오맵 사용 설정을 해야 하는 경우, [추가 기능 신청](https://developers.kakao.com/docs/ko/app-setting/app#app-permission)으로 권한 신청 및 승인 후 설정 가능
    
4. [무료 제공 쿼터](https://developers.kakao.com/docs/ko/getting-started/quota#free) 이상 쿼터가 필요한 경우, [앱 관리 페이지](https://developers.kakao.com/console/app)의 [유료 API] > [일반] > [[사용 가능한 유료 API](https://developers.kakao.com/docs/ko/app-setting/paid-api#billing-api)] 목록의 [카카오맵] 상태를 [사용함]으로 설정해 유료로 추가 사용 가능

**카카오맵 API 활성화**

2024년 12월 1일부터 신규로 카카오맵 API를 호출하는 앱은 카카오맵 사용 설정이 필요 합니다. 자세한 안내는 [공지사항](https://devtalk.kakao.com/t/api/140875)을 참고합니다.

## 개발하기[](https://developers.kakao.com/docs/ko/kakaomap/common#development)

지도 API를 쉽게 연동할 수 있도록 [Kakao Maps API](https://apis.map.kakao.com/) 웹사이트에서 SDK를 제공합니다.

지도 SDK로 API 호출 시, 반드시 플랫폼에 맞는 [플랫폼 키](https://developers.kakao.com/docs/ko/app-setting/app#key)를 사용해야 합니다. 잘못된 앱 키 사용 시, 에러가 발생합니다.

|개발 플랫폼|사용할 앱 키|참고|
|---|---|---|
|JavaScript SDK|JavaScript 키  <br>  <br>**중요**: REST API 키를 사용하지 않도록 유의|[개발 가이드](https://apis.map.kakao.com/web/guide/)|
|Android SDK|네이티브 앱 키|[개발 가이드](https://apis.map.kakao.com/android_v2/docs/)|
|iOS SDK|네이티브 앱 키|[개발 가이드](https://apis.map.kakao.com/ios_v2/docs/)|

## 이용 정책[](https://developers.kakao.com/docs/ko/kakaomap/common#policy)

### 쿼터[](https://developers.kakao.com/docs/ko/kakaomap/common#policy-quota)

카카오 API는 원활한 서비스 제공을 위해 월간 및 일간 쿼터(Quota)를 적용합니다. 현재 적용 중인 쿼터 정보는 [쿼터](https://developers.kakao.com/docs/ko/getting-started/quota)에서 확인할 수 있습니다.

[무료 제공 쿼터](https://developers.kakao.com/docs/ko/getting-started/quota#free) 외에 추가 제공량이 필요한 경우 유료 API 설정이 필요합니다. 자세한 설정 방법은 [유료 API](https://developers.kakao.com/docs/ko/app-setting/paid-api)를 참고합니다.

## FAQ[](https://developers.kakao.com/docs/ko/kakaomap/common#faq)

#### Q. 429 Too Many Request 에러가 발생해요.

카카오맵 API는 앱별로 [무료로 제공하는 쿼터](https://developers.kakao.com/docs/ko/getting-started/quota#free)가 있습니다. 무료 제공량을 모두 소진한 경우, 429 에러가 발생합니다.

무료 제공량 외에 더 많은 제공량이 필요한 경우, 사용량에 대한 요금을 지불하고 추가 API를 호출할 수 있습니다. 자세한 설정은 [유료 API](https://developers.kakao.com/docs/ko/app-setting/paid-api)를 참고합니다.

#### Q. 내가 사용한 쿼터 사용량은 어디서 확인할 수 있나요?

[앱 관리 페이지](https://developers.kakao.com/console/app)의 [통계] > [쿼터]에서 내 앱이 사용한 월간 및 일간 쿼터를 확인할 수 있습니다.

#### Q. 카카오맵 API 사용 시 활용할 수 있는 카카오맵 아이콘 이미지가 있나요?

네. [도구] > [리소스 다운로드] > [[카카오맵](https://developers.kakao.com/tool/resource/map)]에서 카카오맵 로고와 디자인 가이드를 제공합니다. 카카오맵 API를 활용하는 서비스나 바로가기 아이콘으로 사용할 수 있습니다.

로고 사용 시, 사용자에게 일관된 브랜드 이미지를 전달하기 위해 디자인 가이드를 준수하는 것을 권장합니다. 디자인 가이드는 리소스 다운로드 페이지에서 함께 제공합니다.

#### Q. 카카오맵 API에 대해 궁금한 점이 있어요. 어디로 문의하면 되나요?

데브톡의 [지도/로컬 API](https://devtalk.kakao.com/c/map-api/101) 게시판의 게시글을 찾아보거나, 서비스 소유자나 관계자로 확인되는 계정으로 글을 남기면 담당자가 빠르게 대응할 수 있습니다.

### 도움이 되었나요?

로컬

# 이해하기

이 문서는 로컬(Local) API를 소개합니다.

## 기능 소개[](https://developers.kakao.com/docs/ko/local/common#intro)

로컬(Local) API는 키워드로 특정 장소 정보를 조회하거나, 좌표를 주소 또는 행정구역으로 변환하는 등 장소에 대한 정보를 제공합니다. 특정 카테고리로 장소를 검색하는 등 폭넓은 활용이 가능하며, 지번 주소와 도로명 주소 체계를 모두 지원합니다.

장소 정보 활용 예시![](https://developers.kakao.com/docs/_next/image?url=%2Fimg%2Flocal_intro_ko.png&w=2040&q=75)

## 사전 설정[](https://developers.kakao.com/docs/ko/local/common#prerequisite)

로컬 API를 사용하려면 아래 작업을 수행해야 합니다.

1. [카카오디벨로퍼스 앱 생성](https://developers.kakao.com/docs/ko/tutorial/start#create)
2. 카카오맵 API 활성화: [앱 관리 페이지](https://developers.kakao.com/console/app)의 [카카오맵] > [사용 설정]의 [상태]를 [ON]으로 설정
    
    - 이미 카카오맵 API를 활성화한 앱을 소유한 개발자가 추가로 카카오맵 API를 활성화해야 하는 경우, [추가 기능 신청](https://developers.kakao.com/docs/ko/app-setting/app#app-permission)으로 권한 신청 및 승인 후 설정 가능
    

**카카오맵 API 활성화**

2024년 12월 1일부터 신규로 카카오맵 API를 호출하는 앱은 카카오맵 사용 설정이 필요 합니다. 자세한 안내는 [공지](https://devtalk.kakao.com/t/api/140875)를 참고합니다.

## 이용 정책[](https://developers.kakao.com/docs/ko/local/common#policy)

### 쿼터[](https://developers.kakao.com/docs/ko/local/common#policy-quota)

카카오 API는 원활한 서비스 제공을 위해 월간 및 일간 쿼터(Quota)를 적용합니다. 현재 적용 중인 쿼터 정보는 [쿼터](https://developers.kakao.com/docs/ko/getting-started/quota)에서 확인할 수 있습니다.

[무료 제공 쿼터](https://developers.kakao.com/docs/ko/getting-started/quota#free) 외에 추가 제공량이 필요한 경우 유료 API 설정이 필요합니다. 자세한 설정 방법은 [유료 API](https://developers.kakao.com/docs/ko/app-setting/paid-api)를 참고합니다.

## 지도 SDK[](https://developers.kakao.com/docs/ko/local/common#map)

Kakao 지도 API는 Web(JavaScript)과 모바일 애플리케이션(Android, iOS)에서 지도를 이용한 서비스를 제작할 수 있도록 다양한 기능을 제공하고 있습니다. 지도 SDK에 대한 내용은 [Kakao Maps API](https://apis.map.kakao.com/) 웹사이트를 참고합니다.

## 제공 API[](https://developers.kakao.com/docs/ko/local/common#api-list)

각 API의 Kakao SDK 지원 여부는 [지원 범위](https://developers.kakao.com/docs/ko/getting-started/scope-of-support)에서 확인할 수 있습니다.

|API|메서드|URL|설명|
|---|---|---|---|
|[주소로 좌표 변환](https://developers.kakao.com/docs/ko/local/dev-guide#address-coord-info)|`GET`|`https://dapi.kakao.com/v2/local/search/address.${FORMAT}`|주소를 지도 위에 정확하게 표시하기 위해 해당 주소의 좌표 정보를 제공하는 API입니다.|
|[좌표로 행정구역정보 변환](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-district-info)|`GET`|`https://dapi.kakao.com/v2/local/geo/coord2regioncode.${FORMAT}`|다양한 좌표계에 대한 좌표값을 받아 해당 좌표에 부합하는 행정동, 법정동 정보를 반환합니다.|
|[좌표로 주소 변환](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-address-info)|`GET`|`https://dapi.kakao.com/v2/local/geo/coord2address.${FORMAT}`|좌표 정보의 지번 주소와 도로명 주소 정보를 반환합니다.|
|[좌표계 변환](https://developers.kakao.com/docs/ko/local/dev-guide#trans-coord-info)|`GET`|`https://dapi.kakao.com/v2/local/geo/transcoord.${FORMAT}`|`x`, `y` 값과 입력 및 출력 좌표계를 지정해 변환된 좌표 값을 구해, 서로 다른 좌표계간 데이터 호환이 가능하도록 합니다.|
|[키워드로 장소 검색](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-keyword-info)|`GET`|`https://dapi.kakao.com/v2/local/search/keyword.${FORMAT}`|질의어에 매칭된 장소 검색 결과를 지정된 정렬 기준에 따라 제공합니다.|
|[카테고리로 장소 검색](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-category-info)|`GET`|`https://dapi.kakao.com/v2/local/search/category.${FORMAT}`|미리 정의된 카테고리 코드에 해당하는 장소 검색 결과를 지정된 정렬 기준에 따라 제공합니다.|
로컬

# REST API

이 문서는 로컬(Local) API 구현 방법을 소개합니다.

이 문서에 포함된 기능은 [도구] > [REST API 테스트]에서 사용해 볼 수 있습니다.

[REST API 테스트 도구](https://developers.kakao.com/tool/rest-api/open/get/v2-local-search-address.%7Bformat%7D)

## 주소로 좌표 변환[](https://developers.kakao.com/docs/ko/local/dev-guide#address-coord)

##### 기본 정보[](https://developers.kakao.com/docs/ko/local/dev-guide#address-coord-info)

|메서드|URL|인증 방식|
|---|---|---|
|`GET`|`https://dapi.kakao.com/v2/local/search/address.${FORMAT}`|REST API 키|

|[권한](https://developers.kakao.com/docs/ko/getting-started/permission)|사전 설정|[카카오 로그인](https://developers.kakao.com/docs/ko/kakaologin/common)|[동의항목](https://developers.kakao.com/docs/ko/kakaologin/utilize#scope)|
|---|---|---|---|
|-|[REST API 키](https://developers.kakao.com/docs/ko/app-setting/app#rest-api-key)|-|-|

주소를 지도 위에 정확하게 표시하기 위해 해당 주소의 좌표 정보를 제공하는 API입니다.

주소에 해당하는 지번 주소, 도로명 주소, 좌표, 우편번호, 빌딩명 등의 다양한 정보를 함께 제공합니다. 이 API는 지번 주소, 도로명 주소 모두 지원합니다.

REST API 키를 헤더에 담아 `GET`으로 요청합니다. 검색어와 함께 결과 형식 파라미터의 값을 선택적으로 추가할 수 있습니다.

응답은 `JSON`과 `XML` 형식을 지원합니다. 요청 시 URL의 `${FORMAT}` 부분에 원하는 응답 형식을 지정할 수 있습니다. 별도로 포맷을 지정하지 않은 경우 응답은 `JSON` 형식으로 반환됩니다.

#### 요청[](https://developers.kakao.com/docs/ko/local/dev-guide#address-coord-request)

##### 헤더[](https://developers.kakao.com/docs/ko/local/dev-guide#address-coord-request-header)

|이름|설명|필수|
|---|---|---|
|Authorization|`Authorization: KakaoAK ${REST_API_KEY}`  <br>인증 방식, REST API 키로 인증 요청|O|

##### 경로 변수[](https://developers.kakao.com/docs/ko/local/dev-guide#get-request-path-variable)

|이름|타입|설명|필수|
|---|---|---|---|
|FORMAT|`String`|응답 형식(기본값: `JSON`)|X|

##### 쿼리 파라미터[](https://developers.kakao.com/docs/ko/local/dev-guide#address-coord-request-query)

|이름|타입|설명|필수|
|---|---|---|---|
|query|`String`|검색을 원하는 질의어|O|
|analyze_type|`String`|검색 결과 제공 방식, 아래 중 하나  <br><br>- `similar`: 입력한 건물명과 일부만 매칭될 경우에도 확장된 검색 결과 제공, 미지정 시 `similar`가 적용됨<br>- `exact`: 주소의 정확한 건물명이 입력된 주소패턴일 경우에 한해, 입력한 건물명과 정확히 일치하는 검색 결과 제공<br><br>(기본값: `similar`)  <br>  <br>**참고**: [품질 향상을 위한 주소로 좌표 변환 API 업데이트](https://devtalk.kakao.com/t/112161)|X|
|page|`Integer`|결과 페이지 번호  <br>(최소: `1`, 최대: `45`, 기본값: `1`)|X|
|size|`Integer`|한 페이지에 보여질 문서의 개수  <br>(최소: `1`, 최대: `30`, 기본값: `10`)|X|

#### 응답[](https://developers.kakao.com/docs/ko/local/dev-guide#address-coord-response)

##### 헤더[](https://developers.kakao.com/docs/ko/local/dev-guide#address-coord-response-header)

|이름|설명|필수|
|---|---|---|
|Content-Type|응답 데이터 타입  <br>`content-type: application/json;charset=UTF-8` 또는  <br>`content-type: text/xml;charset=UTF-8`|O|

##### 본문[](https://developers.kakao.com/docs/ko/local/dev-guide#address-coord-response-body)

|이름|타입|설명|
|---|---|---|
|meta|[`Meta`](https://developers.kakao.com/docs/ko/local/dev-guide#address-coord-response-body-meta)|응답 관련 정보|
|documents|[`Document[]`](https://developers.kakao.com/docs/ko/local/dev-guide#address-coord-response-body-document)|응답 결과|

##### Meta[](https://developers.kakao.com/docs/ko/local/dev-guide#address-coord-response-body-meta)

|이름|타입|설명|
|---|---|---|
|total_count|`Integer`|검색어에 검색된 문서 수|
|pageable_count|`Integer`|`total_count` 중 노출 가능 문서 수|
|is_end|`Boolean`|현재 페이지가 마지막 페이지인지 여부  <br>값이 `false`면 다음 요청 시 `page` 값을 증가시켜 다음 페이지 요청 가능|

##### Document[](https://developers.kakao.com/docs/ko/local/dev-guide#address-coord-response-body-document)

|이름|타입|설명|
|---|---|---|
|address_name|`String`|전체 지번 주소 또는 전체 도로명 주소, 입력에 따라 결정됨|
|address_type|`String`|`address_name`의 값의 타입(Type), 아래 중 하나  <br><br>- `REGION`(지명)<br>- `ROAD`(도로명)<br>- `REGION_ADDR`(지번 주소)<br>- `ROAD_ADDR`(도로명 주소)|
|x|`String`|X 좌표값, 경위도인 경우 경도(longitude)|
|y|`String`|Y 좌표값, 경위도인 경우 위도(latitude)|
|address|[`Address`](https://developers.kakao.com/docs/ko/local/dev-guide#address-coord-response-body-document-address)|지번 주소 상세 정보|
|road_address|[`RoadAddress`](https://developers.kakao.com/docs/ko/local/dev-guide#address-coord-response-body-document-road-address)|도로명 주소 상세 정보|

##### Address[](https://developers.kakao.com/docs/ko/local/dev-guide#address-coord-response-body-document-address)

|이름|타입|설명|
|---|---|---|
|address_name|`String`|전체 지번 주소|
|region_1depth_name|`String`|지역 1 Depth, 시도 단위|
|region_2depth_name|`String`|지역 2 Depth, 구 단위|
|region_3depth_name|`String`|지역 3 Depth, 동 단위|
|region_3depth_h_name|`String`|지역 3 Depth, 행정동 명칭|
|h_code|`String`|행정 코드|
|b_code|`String`|법정 코드|
|mountain_yn|`String`|산 여부, `Y` 또는 `N`|
|main_address_no|`String`|지번 주번지|
|sub_address_no|`String`|지번 부번지, 없을 경우 빈 문자열(`""`) 반환|
|x|`String`|X 좌표값, 경위도인 경우 경도(longitude)|
|y|`String`|Y 좌표값, 경위도인 경우 위도(latitude)|

* zip_code: Deprecated, 우편번호(String), 6자리, [공지](https://devtalk.kakao.com/t/api-6/93000) 참고

##### RoadAddress[](https://developers.kakao.com/docs/ko/local/dev-guide#address-coord-response-body-document-road-address)

|이름|타입|설명|
|---|---|---|
|address_name|`String`|전체 도로명 주소|
|region_1depth_name|`String`|지역명1|
|region_2depth_name|`String`|지역명2|
|region_3depth_name|`String`|지역명3|
|road_name|`String`|도로명|
|underground_yn|`String`|지하 여부, `Y` 또는 `N`|
|main_building_no|`String`|건물 본번|
|sub_building_no|`String`|건물 부번, 없을 경우 빈 문자열(`""`) 반환|
|building_name|`String`|건물 이름|
|zone_no|`String`|우편번호(5자리)|
|x|`String`|X 좌표값, 경위도인 경우 경도(longitude)|
|y|`String`|Y 좌표값, 경위도인 경우 위도(latitude)|

#### 예제[](https://developers.kakao.com/docs/ko/local/dev-guide#address-coord-sample)

##### 요청

curl -v -G GET "https://dapi.kakao.com/v2/local/search/address.json" \

  -H "Authorization: KakaoAK ${REST_API_KEY}" \

  --data-urlencode "query=전북 삼성동 100"

##### 응답

// HTTP/1.1 200 OK

// Content-Type: application/json;charset=UTF-8

{

  "meta": {

    "total_count": 4,

    "pageable_count": 4,

    "is_end": true

  },

  "documents": [

    {

      "address_name": "전북 익산시 부송동 100",

      "y": "35.97664845766847",

      "x": "126.99597295767953",

      "address_type": "REGION_ADDR",

      "address": {

        "address_name": "전북 익산시 부송동 100",

        "region_1depth_name": "전북",

        "region_2depth_name": "익산시",

        "region_3depth_name": "부송동",

        "region_3depth_h_name": "삼성동",

        "h_code": "4514069000",

        "b_code": "4514013400",

        "mountain_yn": "N",

        "main_address_no": "100",

        "sub_address_no": "",

        "x": "126.99597295767953",

        "y": "35.97664845766847"

      },

      "road_address": {

        "address_name": "전북 익산시 망산길 11-17",

        "region_1depth_name": "전북",

        "region_2depth_name": "익산시",

        "region_3depth_name": "부송동",

        "road_name": "망산길",

        "underground_yn": "N",

        "main_building_no": "11",

        "sub_building_no": "17",

        "building_name": "",

        "zone_no": "54547",

        "y": "35.976749396987046",

        "x": "126.99599512792346"

      }

    }

    // ...

  ]

}

## 좌표로 행정구역정보 변환[](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-district)

##### 기본 정보[](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-district-info)

|메서드|URL|인증 방식|
|---|---|---|
|`GET`|`https://dapi.kakao.com/v2/local/geo/coord2regioncode.${FORMAT}`|REST API 키|

|[권한](https://developers.kakao.com/docs/ko/getting-started/permission)|사전 설정|[카카오 로그인](https://developers.kakao.com/docs/ko/kakaologin/common)|[동의항목](https://developers.kakao.com/docs/ko/kakaologin/utilize#scope)|
|---|---|---|---|
|-|[REST API 키](https://developers.kakao.com/docs/ko/app-setting/app#rest-api-key)|-|-|

다양한 좌표계에 대한 좌표값을 받아 해당 좌표에 부합하는 행정동, 법정동 정보를 반환합니다.

대략적인 지역 정보를 제공하여 해당 위치에 맞는 다른 서비스(맛집, 날씨 등등)를 연계하는데 활용 가능합니다.

앱 REST API 키를 헤더에 담아 `GET`으로 요청합니다. 좌표와 함께 좌표계 등 파라미터를 선택적으로 추가할 수 있습니다.

응답은 `JSON`과 `XML` 형식을 지원합니다. 요청 시 URL의 `${FORMAT}` 부분에 원하는 응답 형식을 지정할 수 있습니다. 별도로 포맷을 지정하지 않은 경우 응답은 `JSON` 형식으로 반환됩니다.

#### 요청[](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-district-request)

##### 헤더[](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-district-request-header)

|이름|설명|필수|
|---|---|---|
|Authorization|`Authorization: KakaoAK ${REST_API_KEY}`  <br>인증 방식, REST API 키로 인증 요청|O|

##### 경로 변수[](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-district-request-path-variable)

|이름|타입|설명|필수|
|---|---|---|---|
|FORMAT|`String`|응답 형식(기본값: `JSON`)|X|

##### 쿼리 파라미터[](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-district-request-query)

|이름|타입|설명|필수|
|---|---|---|---|
|x|`String`|X 좌표값, 경위도인 경우 경도(longitude)|O|
|y|`String`|Y 좌표값, 경위도인 경우 위도(latitude)|O|
|input_coord|`String`|x, y 로 입력되는 값에 대한 좌표계  <br>지원 좌표계: `WGS84`, `WCONGNAMUL`, `CONGNAMUL`, `WTM`, `TM`  <br>(기본값: `WGS84`)|X|
|output_coord|`String`|결과에 출력될 좌표계  <br>지원 좌표계: `WGS84`, `WCONGNAMUL`, `CONGNAMUL`, `WTM`, `TM`  <br>(기본값: `WGS84`)|X|

#### 응답[](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-district-response)

##### 헤더[](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-district-response-header)

|이름|설명|필수|
|---|---|---|
|Content-Type|응답 데이터 타입  <br>`content-type: application/json;charset=UTF-8` 또는  <br>`content-type: text/xml;charset=UTF-8`|O|

##### 본문[](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-district-response-body)

|이름|타입|설명|
|---|---|---|
|meta|[`Meta`](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-district-response-body-meta)|응답 관련 정보|
|documents|[`Document[]`](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-district-response-body-document)|응답 결과|

##### Meta[](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-district-response-body-meta)

|이름|타입|설명|
|---|---|---|
|total_count|`Integer`|검색어에 검색된 문서 수|

##### Document[](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-district-response-body-document)

|이름|타입|설명|
|---|---|---|
|region_type|`String`|`H`(행정동) 또는 `B`(법정동)|
|address_name|`String`|전체 지역 명칭|
|region_1depth_name|`String`|지역 1Depth, 시도 단위  <br>바다 영역은 존재하지 않음|
|region_2depth_name|`String`|지역 2Depth, 구 단위  <br>바다 영역은 존재하지 않음|
|region_3depth_name|`String`|지역 3Depth, 동 단위  <br>바다 영역은 존재하지 않음|
|region_4depth_name|`String`|지역 4Depth  <br>`region_type`이 법정동이며, 리 영역인 경우만 존재|
|code|`String`|`region` 코드|
|x|`Double`|X 좌표값, 경위도인 경우 경도(longitude)|
|y|`Double`|Y 좌표값, 경위도인 경우 위도(latitude)|

#### 예제[](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-district-sample)

##### 요청

curl -v -G GET "https://dapi.kakao.com/v2/local/geo/coord2regioncode.json?x=127.1086228&y=37.4012191" \

  -H "Authorization: KakaoAK ${REST_API_KEY}"

##### 응답

// HTTP/1.1 200 OK

// Content-Type: application/json;charset=UTF-8

{

  "meta": {

    "total_count": 2

  },

  "documents": [

    {

      "region_type": "B",

      "address_name": "경기도 성남시 분당구 삼평동",

      "region_1depth_name": "경기도",

      "region_2depth_name": "성남시 분당구",

      "region_3depth_name": "삼평동",

      "region_4depth_name": "",

      "code": "4113510900",

      "x": 127.10459896729914,

      "y": 37.40269721785548

    },

    {

      "region_type": "H",

      "address_name": "경기도 성남시 분당구 삼평동",

      "region_1depth_name": "경기도",

      "region_2depth_name": "성남시 분당구",

      "region_3depth_name": "삼평동",

      "region_4depth_name": "",

      "code": "4113565500",

      "x": 127.1163593869371,

      "y": 37.40612091848614

    }

  ]

}

## 좌표로 주소 변환[](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-address)

##### 기본 정보[](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-address-info)

|메서드|URL|인증 방식|
|---|---|---|
|`GET`|`https://dapi.kakao.com/v2/local/geo/coord2address.${FORMAT}`|REST API 키|

|[권한](https://developers.kakao.com/docs/ko/getting-started/permission)|사전 설정|[카카오 로그인](https://developers.kakao.com/docs/ko/kakaologin/common)|[동의항목](https://developers.kakao.com/docs/ko/kakaologin/utilize#scope)|
|---|---|---|---|
|-|[REST API 키](https://developers.kakao.com/docs/ko/app-setting/app#rest-api-key)|-|-|

좌표 정보의 지번 주소와 도로명 주소 정보를 반환합니다.

도로명 주소는 좌표에 따라 반환되지 않을 수 있습니다.

앱 REST API 키를 헤더에 담아 `GET`으로 요청합니다. 좌표와 함께 좌표계 파라미터를 추가할 수 있습니다.

응답은 `JSON`과 `XML` 형식을 지원합니다. 요청 시 URL의 `${FORMAT}` 부분에 원하는 응답 형식을 지정할 수 있습니다. 별도로 포맷을 지정하지 않은 경우 응답은 `JSON` 형식으로 반환됩니다.

요청 성공 시 응답은 `documents` 하위에 지번 주소 또는 도로명 주소 상세 정보를 포함합니다.

#### 요청[](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-address-request)

##### 헤더[](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-address-request-header)

|이름|설명|필수|
|---|---|---|
|Authorization|`Authorization: KakaoAK ${REST_API_KEY}`  <br>인증 방식, REST API 키로 인증 요청|O|

##### 쿼리 파라미터[](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-address-request-query)

|이름|타입|설명|필수|
|---|---|---|---|
|x|`String`|X 좌표값, 경위도인 경우 경도(longitude)|O|
|y|`String`|Y 좌표값, 경위도인 경우 위도(latitude)|O|
|input_coord|`String`|x, y 로 입력되는 값에 대한 좌표계  <br>지원 좌표계: `WGS84`, `WCONGNAMUL`, `CONGNAMUL`, `WTM`, `TM`  <br>(기본값: `WGS84`)|X|

#### 응답[](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-address-response)

##### 헤더[](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-address-response-header)

|이름|설명|필수|
|---|---|---|
|Content-Type|응답 데이터 타입  <br>`content-type: application/json;charset=UTF-8` 또는  <br>`content-type: text/xml;charset=UTF-8`|O|

##### 본문[](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-address-response-body)

|이름|타입|설명|
|---|---|---|
|meta|[`Meta`](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-address-response-body-meta)|응답 관련 정보|
|documents|[`Document[]`](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-address-response-body-document)|응답 결과|

##### Meta[](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-address-response-body-meta)

|이름|타입|설명|
|---|---|---|
|total_count|`Integer`|변환된 지번 주소 및 도로명 주소 의 개수, `0` 또는 `1`|

##### Document[](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-address-response-body-document)

|이름|타입|설명|
|---|---|---|
|address|[`Address`](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-address-response-body-address)|지번 주소 상세 정보, 아래 `Address` 참고|
|road_address|[`RoadAddress`](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-address-response-body-road-address)|도로명 주소 상세 정보, 아래 `RoadAddress` 참고|

##### Address[](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-address-response-body-address)

|이름|타입|설명|
|---|---|---|
|address_name|`String`|전체 지번 주소|
|region_1depth_name|`String`|지역 1Depth명, 시도 단위|
|region_2depth_name|`String`|지역 2Depth명, 구 단위|
|region_3depth_name|`String`|지역 3Depth명, 동 단위|
|mountain_yn|`String`|산 여부, `Y` 또는 `N`|
|main_address_no|`String`|지번 주 번지|
|sub_address_no|`String`|지번 부 번지, 없을 경우 빈 문자열(`""`) 반환|

* zip_code: Deprecated, 우편번호(String), 6자리, [공지](https://devtalk.kakao.com/t/api-6/93000) 참고

##### RoadAddress[](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-address-response-body-road-address)

|이름|타입|설명|
|---|---|---|
|address_name|`String`|전체 도로명 주소|
|region_1depth_name|`String`|지역 1Depth, 시도 단위|
|region_2depth_name|`String`|지역 2Depth, 구 단위|
|region_3depth_name|`String`|지역 3Depth, 면 단위|
|road_name|`String`|도로명|
|underground_yn|`String`|지하 여부, `Y` 또는 `N`|
|main_building_no|`String`|건물 본번|
|sub_building_no|`String`|건물 부번, 없을 경우 빈 문자열(`""`) 반환|
|building_name|`String`|건물 이름|
|zone_no|`String`|우편번호(5자리)|

#### 예제[](https://developers.kakao.com/docs/ko/local/dev-guide#coord-to-address-sample)

##### 요청

curl -v -G GET "https://dapi.kakao.com/v2/local/geo/coord2address.json?x=127.423084873712&y=37.0789561558879&input_coord=WGS84" \

  -H "Authorization: KakaoAK ${REST_API_KEY}"

##### 응답

// HTTP/1.1 200 OK

// Content-Type: application/json;charset=UTF-8

{

  "meta": {

    "total_count": 1

  },

  "documents": [

    {

      "road_address": {

        "address_name": "경기도 안성시 죽산면 죽산초교길 69-4",

        "region_1depth_name": "경기",

        "region_2depth_name": "안성시",

        "region_3depth_name": "죽산면",

        "road_name": "죽산초교길",

        "underground_yn": "N",

        "main_building_no": "69",

        "sub_building_no": "4",

        "building_name": "무지개아파트",

        "zone_no": "17519"

      },

      "address": {

        "address_name": "경기 안성시 죽산면 죽산리 343-1",

        "region_1depth_name": "경기",

        "region_2depth_name": "안성시",

        "region_3depth_name": "죽산면 죽산리",

        "mountain_yn": "N",

        "main_address_no": "343",

        "sub_address_no": "1"

      }

    }

  ]

}

## 좌표계 변환[](https://developers.kakao.com/docs/ko/local/dev-guide#trans-coord)

##### 기본 정보[](https://developers.kakao.com/docs/ko/local/dev-guide#trans-coord-info)

|메서드|URL|인증 방식|
|---|---|---|
|`GET`|`https://dapi.kakao.com/v2/local/geo/transcoord.${FORMAT}`|REST API 키|

|[권한](https://developers.kakao.com/docs/ko/getting-started/permission)|사전 설정|[카카오 로그인](https://developers.kakao.com/docs/ko/kakaologin/common)|[동의항목](https://developers.kakao.com/docs/ko/kakaologin/utilize#scope)|
|---|---|---|---|
|-|[REST API 키](https://developers.kakao.com/docs/ko/app-setting/app#rest-api-key)|-|-|

`x`, `y` 값과 입력 및 출력 좌표계를 지정해 변환된 좌표 값을 구해, 서로 다른 좌표계간 데이터 호환이 가능하도록 합니다.

앱 REST API 키를 헤더에 담아 `GET`으로 요청합니다. 좌표와 함께 좌표계 파라미터의 값을 선택해 요청합니다.

응답은 `JSON`과 `XML` 형식을 지원합니다. 요청 시 URL의 `${FORMAT}` 부분에 원하는 응답 형식을 지정할 수 있습니다. 별도로 포맷을 지정하지 않은 경우 응답은 `JSON` 형식으로 반환됩니다.

#### 요청[](https://developers.kakao.com/docs/ko/local/dev-guide#trans-coord-request)

##### 헤더[](https://developers.kakao.com/docs/ko/local/dev-guide#trans-coord-request-header)

|이름|설명|필수|
|---|---|---|
|Authorization|`Authorization: KakaoAK ${REST_API_KEY}`  <br>인증 방식, REST API 키로 인증 요청|O|

##### 쿼리 파라미터[](https://developers.kakao.com/docs/ko/local/dev-guide#trans-coord-request-query)

|이름|타입|설명|필수|
|---|---|---|---|
|x|`Double`|X 좌표값, 경위도인 경우 `longitude`(경도)|O|
|y|`Double`|Y 좌표값, 경위도인 경우 `latitude`(위도)|O|
|input_coord|`String`|`x`, `y` 값의 좌표계  <br>지원 좌표계: `WGS84`, `WCONGNAMUL`, `CONGNAMUL`, `WTM`, `TM`, `KTM`, `UTM`, `BESSEL`, `WKTM`, `WUTM`  <br>(기본값: `WGS84`)|X|
|output_coord|`String`|변환할 좌표계  <br>지원 좌표계:`WGS84`, `WCONGNAMUL`, `CONGNAMUL`, `WTM`, `TM`, `KTM`, `UTM`, `BESSEL`, `WKTM`, `WUTM`  <br>(기본값: `WGS84`)|O|

#### 응답[](https://developers.kakao.com/docs/ko/local/dev-guide#trans-coord-response)

##### 헤더[](https://developers.kakao.com/docs/ko/local/dev-guide#trans-coord-response-header)

|이름|설명|필수|
|---|---|---|
|Content-Type|응답 데이터 타입  <br>`content-type: application/json;charset=UTF-8` 또는  <br>`content-type: text/xml;charset=UTF-8`|O|

##### 본문[](https://developers.kakao.com/docs/ko/local/dev-guide#trans-coord-response-body)

|이름|타입|설명|
|---|---|---|
|meta|[`Meta`](https://developers.kakao.com/docs/ko/local/dev-guide#trans-coord-response-body-meta)|응답 관련 정보|
|documents|[`Document[]`](https://developers.kakao.com/docs/ko/local/dev-guide#trans-coord-response-body-document)|응답 결과|

##### Meta[](https://developers.kakao.com/docs/ko/local/dev-guide#trans-coord-response-body-meta)

|이름|타입|설명|
|---|---|---|
|total_count|`Integer`|매칭된 문서수|

##### Document[](https://developers.kakao.com/docs/ko/local/dev-guide#trans-coord-response-body-document)

|이름|타입|설명|
|---|---|---|
|x|`Double`|X 좌표, 경위도인 경우 경도(longitude)|
|y|`Double`|Y 좌표, 경위도인 경우 위도(latitude)|

#### 예제[](https://developers.kakao.com/docs/ko/local/dev-guide#trans-coord-sample)

##### 요청

curl -v -G GET "https://dapi.kakao.com/v2/local/geo/transcoord.json?x=160710.37729270622&y=-4388.879299157299&input_coord=WTM&output_coord=WGS84" \

  -H "Authorization: KakaoAK ${REST_API_KEY}"

##### 응답

// HTTP/1.1 200 OK

// Content-Type: application/json;charset=UTF-8

{

  "meta": {

    "total_count": 1

  },

  "documents": [

    {

      "x": 126.57740680000002,

      "y": 33.453357700000005

    }

  ]

}

## 키워드로 장소 검색[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-keyword)

##### 기본 정보[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-keyword-info)

|메서드|URL|인증 방식|
|---|---|---|
|`GET`|`https://dapi.kakao.com/v2/local/search/keyword.${FORMAT}`|REST API 키|

|[권한](https://developers.kakao.com/docs/ko/getting-started/permission)|사전 설정|[카카오 로그인](https://developers.kakao.com/docs/ko/kakaologin/common)|[동의항목](https://developers.kakao.com/docs/ko/kakaologin/utilize#scope)|
|---|---|---|---|
|-|[REST API 키](https://developers.kakao.com/docs/ko/app-setting/app#rest-api-key)|-|-|

질의어에 매칭된 장소 검색 결과를 지정된 정렬 기준에 따라 제공합니다.

현재 위치 좌표, 반경 제한, 정렬 옵션, 페이징 등의 기능으로 원하는 결과를 요청 할 수 있습니다.

앱 REST API 키를 헤더에 담아 `GET`으로 요청합니다. 원하는 검색어와 함께 결과 형식 파라미터의 값을 선택적으로 추가할 수 있습니다.

응답은 `JSON`과 `XML` 형식을 지원합니다. 요청 시 URL의 `${FORMAT}` 부분에 원하는 응답 형식을 지정할 수 있습니다. 별도로 포맷을 지정하지 않은 경우 응답은 `JSON` 형식으로 반환됩니다.

요청 성공 시 응답의 장소 정보는 이름, 주소, 좌표, 카테고리 등의 기본 정보와 다양한 부가정보, 카카오 맵의 장소 상세 페이지로 연결되는 URL을 제공합니다.

#### 요청[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-keyword-request)

##### 헤더[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-keyword-request-header)

|이름|설명|필수|
|---|---|---|
|Authorization|`Authorization: KakaoAK ${REST_API_KEY}`  <br>인증 방식, REST API 키로 인증 요청|O|

##### 쿼리 파라미터[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-keyword-request-query)

|이름|타입|설명|필수|
|---|---|---|---|
|query|`String`|검색을 원하는 질의어|O|
|category_group_code|[`CategoryGroupCode`](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-keyword-request-query-category-group-code)|카테고리 그룹 코드, 카테고리로 결과 필터링을 원하는 경우 사용|X|
|x|`String`|중심 좌표의 X 혹은 경도(longitude) 값  <br>특정 지역을 중심으로 검색할 경우 `radius`와 함께 사용 가능|X|
|y|`String`|중심 좌표의 Y 혹은 위도(latitude) 값  <br>특정 지역을 중심으로 검색할 경우 `radius`와 함께 사용 가능|X|
|radius|`Integer`|중심 좌표부터의 반경거리. 특정 지역을 중심으로 검색하려고 할 경우 중심좌표로 쓰일 x,y와 함께 사용  <br>(단위: 미터(m), 최소: `0`, 최대: `20000`)|X|
|rect|`String`|사각형의 지정 범위 내 제한 검색을 위한 좌표  <br>지도 화면 내 검색 등 제한 검색에서 사용 가능  <br>좌측 X 좌표, 좌측 Y 좌표, 우측 X 좌표, 우측 Y 좌표 형식|X|
|page|`Integer`|결과 페이지 번호  <br>(최소: `1`, 최대: `45`, 기본값: `1`)|X|
|size|`Integer`|한 페이지에 보여질 문서의 개수  <br>(최소: `1`, 최대: `15`, 기본값: `15`)|X|
|sort|`String`|결과 정렬 순서  <br>`distance` 정렬을 원할 때는 기준 좌표로 쓰일 `x`, `y`와 함께 사용  <br>`distance` 또는 `accuracy`(기본값: `accuracy`)|X|

##### CategoryGroupCode[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-keyword-request-query-category-group-code)

|이름|설명|
|---|---|
|MT1|대형마트|
|CS2|편의점|
|PS3|어린이집, 유치원|
|SC4|학교|
|AC5|학원|
|PK6|주차장|
|OL7|주유소, 충전소|
|SW8|지하철역|
|BK9|은행|
|CT1|문화시설|
|AG2|중개업소|
|PO3|공공기관|
|AT4|관광명소|
|AD5|숙박|
|FD6|음식점|
|CE7|카페|
|HP8|병원|
|PM9|약국|

#### 응답[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-keyword-response)

##### 헤더[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-keyword-response-header)

|이름|설명|필수|
|---|---|---|
|Content-Type|응답 데이터 타입  <br>`content-type: application/json;charset=UTF-8` 또는  <br>`content-type: text/xml;charset=UTF-8`|O|

##### 본문[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-keyword-response-body)

|이름|타입|설명|
|---|---|---|
|meta|[`Meta`](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-keyword-response-body-meta)|응답 관련 정보|
|documents|[`Document[]`](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-keyword-response-body-document)|응답 결과|

##### Meta[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-keyword-response-body-meta)

|이름|타입|설명|
|---|---|---|
|total_count|`Integer`|검색어에 검색된 문서 수|
|pageable_count|`Integer`|`total_count` 중 노출 가능 문서 수 (최대: `45`)|
|is_end|`Boolean`|현재 페이지가 마지막 페이지인지 여부  <br>값이 `false`면 다음 요청 시 `page` 값을 증가시켜 다음 페이지 요청 가능|
|same_name|[`SameName`](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-keyword-response-body-same-name)|질의어의 지역 및 키워드 분석 정보|

##### SameName[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-keyword-response-body-same-name)

|이름|타입|설명|
|---|---|---|
|region|`String[]`|질의어에서 인식된 지역의 리스트  <br>예: '중앙로 맛집' 에서 중앙로에 해당하는 지역 리스트|
|keyword|`String`|질의어에서 지역 정보를 제외한 키워드  <br>예: '중앙로 맛집' 에서 '맛집'|
|selected_region|`String`|인식된 지역 리스트 중, 현재 검색에 사용된 지역 정보|

##### Document[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-keyword-response-body-document)

|이름|타입|설명|
|---|---|---|
|id|`String`|장소 ID|
|place_name|`String`|장소명, 업체명|
|category_name|`String`|카테고리 이름|
|category_group_code|`String`|중요 카테고리만 그룹핑한 카테고리 그룹 코드|
|category_group_name|`String`|중요 카테고리만 그룹핑한 카테고리 그룹명|
|phone|`String`|전화번호|
|address_name|`String`|전체 지번 주소|
|road_address_name|`String`|전체 도로명 주소|
|x|`String`|X 좌표값, 경위도인 경우 longitude (경도)|
|y|`String`|Y 좌표값, 경위도인 경우 latitude(위도)|
|place_url|`String`|장소 상세페이지 URL|
|distance|`String`|중심좌표까지의 거리 (단, `x`,`y` 파라미터를 준 경우에만 존재)  <br>단위 meter|

#### 예제[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-keyword-sample)

##### 요청: 서울 강남구 삼성동 20km 반경에서 카카오프렌즈 매장 검색

curl -v -G GET "https://dapi.kakao.com/v2/local/search/keyword.json?y=37.514322572335935&x=127.06283102249932&radius=20000" \

  -H "Authorization: KakaoAK ${REST_API_KEY}" \

  --data-urlencode "query=카카오프렌즈"

##### 응답

// HTTP/1.1 200 OK

// Content-Type: application/json;charset=UTF-8

{

  "meta": {

    "same_name": {

      "region": [],

      "keyword": "카카오프렌즈",

      "selected_region": ""

    },

    "pageable_count": 14,

    "total_count": 14,

    "is_end": true

  },

  "documents": [

    {

      "place_name": "카카오프렌즈 코엑스점",

      "distance": "418",

      "place_url": "http://place.map.kakao.com/26338954",

      "category_name": "가정,생활 > 문구,사무용품 > 디자인문구 > 카카오프렌즈",

      "address_name": "서울 강남구 삼성동 159",

      "road_address_name": "서울 강남구 영동대로 513",

      "id": "26338954",

      "phone": "02-6002-1880",

      "category_group_code": "",

      "category_group_name": "",

      "x": "127.05902969025047",

      "y": "37.51207412593136"

    }

    // ...

  ]

}

## 카테고리로 장소 검색[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-category)

##### 기본 정보[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-category-info)

|메서드|URL|인증 방식|
|---|---|---|
|`GET`|`https://dapi.kakao.com/v2/local/search/category.${FORMAT}`|REST API 키|

|[권한](https://developers.kakao.com/docs/ko/getting-started/permission)|사전 설정|[카카오 로그인](https://developers.kakao.com/docs/ko/kakaologin/common)|[동의항목](https://developers.kakao.com/docs/ko/kakaologin/utilize#scope)|
|---|---|---|---|
|-|[REST API 키](https://developers.kakao.com/docs/ko/app-setting/app#rest-api-key)|-|-|

미리 정의된 카테고리 코드에 해당하는 장소 검색 결과를 지정된 정렬 기준에 따라 제공합니다.

앱 REST API 키를 헤더에 담아 `GET`으로 요청합니다. 카테고리 코드와 함께 위치 좌표, 반경 제한, 결과 정렬 순서, 페이징 등의 파라미터를 선택적으로 사용할 수 있습니다.

응답은 `JSON`과 `XML` 형식을 지원합니다. 요청 시 URL의 `${FORMAT}` 부분에 원하는 응답 형식을 지정할 수 있습니다. 별도로 포맷을 지정하지 않은 경우 응답은 `JSON` 형식으로 반환됩니다.

각 장소 정보는 이름, 주소, 좌표, 카테고리 등의 기본 정보와 다양한 부가정보, 카카오맵의 장소 상세 페이지로 연결되는 URL을 제공합니다.

#### 요청[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-category-request)

##### 헤더[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-category-request-header)

|이름|설명|필수|
|---|---|---|
|Authorization|`Authorization: KakaoAK ${REST_API_KEY}`  <br>인증 방식, REST API 키로 인증 요청|O|

##### 경로 변수[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-category-request-path-variable)

|이름|타입|설명|필수|
|---|---|---|---|
|FORMAT|`String`|응답 형식(기본값: `JSON`)|X|

##### 쿼리 파라미터[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-category-request-query)

|이름|타입|설명|필수|
|---|---|---|---|
|category_group_code|[`CategoryGroupCode`](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-category-request-query-category-group-code)|카테고리 코드|O|
|x|`String`|중심 좌표의 X값 혹은 longitude  <br>특정 지역을 중심으로 검색하려고 할 경우 `radius`와 함께 사용 가능.|(`x`,`y`,`radius`) 또는 `rect` 필수|
|y|`String`|중심 좌표의 Y값 혹은 latitude  <br>특정 지역을 중심으로 검색하려고 할 경우 `radius`와 함께 사용 가능.|(`x`,`y`,`radius`) 또는 `rect` 필수|
|radius|`Integer`|중심 좌표부터의 반경거리. 특정 지역을 중심으로 검색하려고 할 경우 중심좌표로 쓰일 x,y와 함께 사용. 단위 meter, 0~20000 사이의 값|(`x`,`y`,`radius`) 또는 `rect` 필수|
|rect|`String`|사각형 범위내에서 제한 검색을 위한 좌표  <br>지도 화면 내 검색시 등 제한 검색에서 사용 가능  <br>좌측 X 좌표, 좌측 Y 좌표, 우측 X 좌표, 우측 Y 좌표 형식  <br>`x`, `y`, `radius` 또는 `rect` 필수|X|
|page|`Integer`|결과 페이지 번호  <br>1~45 사이의 값 (기본값: `1`)|X|
|size|`Integer`|한 페이지에 보여질 문서의 개수  <br>1~15 사이의 값 (기본값: `15`)|X|
|sort|`String`|결과 정렬 순서, distance 정렬을 원할 때는 기준좌표로 쓰일 x, y 파라미터 필요  <br>`distance` 또는 `accuracy` (기본값: `accuracy`)|X|

##### CategoryGroupCode[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-category-request-query-category-group-code)

|이름|설명|
|---|---|
|MT1|대형마트|
|CS2|편의점|
|PS3|어린이집, 유치원|
|SC4|학교|
|AC5|학원|
|PK6|주차장|
|OL7|주유소, 충전소|
|SW8|지하철역|
|BK9|은행|
|CT1|문화시설|
|AG2|중개업소|
|PO3|공공기관|
|AT4|관광명소|
|AD5|숙박|
|FD6|음식점|
|CE7|카페|
|HP8|병원|
|PM9|약국|

#### 응답[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-category-response)

##### 헤더[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-category-response-header)

|이름|설명|필수|
|---|---|---|
|Content-Type|응답 데이터 타입  <br>`content-type: application/json;charset=UTF-8` 또는  <br>`content-type: text/xml;charset=UTF-8`|O|

##### 본문[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-category-response-body)

|이름|타입|설명|
|---|---|---|
|meta|[`Meta`](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-category-response-body-meta)|응답 관련 정보|
|documents|[`Document[]`](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-category-response-body-document)|응답 결과|

##### Meta[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-category-response-body-meta)

|이름|타입|설명|
|---|---|---|
|total_count|`Integer`|검색된 문서 수|
|pageable_count|`Integer`|`total_count` 중 노출 가능 문서 수 (최대값: `45`)|
|is_end|`Boolean`|현재 페이지가 마지막 페이지인지 여부  <br>값이 `false`면 다음 요청 시 `page` 값을 증가시켜 다음 페이지 요청 가능|
|same_name|[`SameName`](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-category-response-body-meta-same-name)|질의어의 지역 및 키워드 분석 정보|

##### SameName[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-category-response-body-meta-same-name)

|이름|타입|설명|
|---|---|---|
|region|`String[]`|질의어에서 인식된 지역의 리스트  <br>(예: '중앙로 맛집' 에서 '중앙로'에 해당하는 지역 리스트)|
|keyword|`String`|질의어에서 지역 정보를 제외한 키워드  <br>(예: '중앙로 맛집' 에서 '맛집')|
|selected_region|`String`|인식된 지역 리스트 중 현재 검색에 사용된 지역 정보|

##### Document[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-category-response-body-document)

|이름|타입|설명|
|---|---|---|
|id|`String`|장소 ID|
|place_name|`String`|장소명, 업체명|
|category_name|`String`|카테고리 이름|
|category_group_code|`String`|중요 카테고리만 그룹핑한 카테고리 그룹 코드|
|category_group_name|`String`|중요 카테고리만 그룹핑한 카테고리 그룹명|
|phone|`String`|전화번호|
|address_name|`String`|전체 지번 주소|
|road_address_name|`String`|전체 도로명 주소|
|x|`String`|X 좌표 혹은 경도(longitude)|
|y|`String`|Y 좌표 혹은 위도(latitude)|
|place_url|`String`|장소 상세 페이지 URL|
|distance|`String`|중심좌표까지의 거리 (단, `x`,`y` 파라미터를 준 경우에만 존재)  <br>(단위: 미터(m))|

#### 예제[](https://developers.kakao.com/docs/ko/local/dev-guide#search-by-category-sample)

##### 요청: 서울 강남구 삼성동 20km 반경에서 약국 검색

curl -v -G GET "https://dapi.kakao.com/v2/local/search/category.json?category\_group\_code=PM9&radius=20000" \

  -H "Authorization: KakaoAK ${REST_API_KEY}"

##### 응답

// HTTP/1.1 200 OK

// Content-Type: application/json;charset=UTF-8

{

  "meta": {

    "same_name": null,

    "pageable_count": 11,

    "total_count": 11,

    "is_end": true

  },

  "documents": [

    {

      "place_name": "장생당약국",

      "distance": "",

      "place_url": "http://place.map.kakao.com/16618597",

      "category_name": "의료,건강 > 약국",

      "address_name": "서울 강남구 대치동 943-16",

      "road_address_name": "서울 강남구 테헤란로84길 17",

      "id": "16618597",

      "phone": "02-558-5476",

      "category_group_code": "PM9",

      "category_group_name": "약국",

      "x": "127.05897078335246",

      "y": "37.506051888130386"

    }

    // ...

  ]

}

## 더 보기[](https://developers.kakao.com/docs/ko/local/dev-guide#see-more)

- [REST API 레퍼런스](https://developers.kakao.com/docs/ko/rest-api/reference)

### 도움이 되었나요?

카카오내비

# 이해하기

이 문서는 카카오내비 SDK 및 API를 소개합니다.

## 기능 소개[](https://developers.kakao.com/docs/ko/kakaonavi/common#intro)

카카오내비는 서비스에서 내비게이션 기능을 사용할 수 있도록 SDK 및 API를 제공합니다. 간단히 카카오내비 앱을 실행해 내비게이션 기능을 사용하거나, 서비스 앱 안에서 내비게이션 및 경로 정보 활용 기능을 구현할 수 있습니다.

## 카카오내비 앱으로 길 안내[](https://developers.kakao.com/docs/ko/kakaonavi/common#launch-kakaonavi)

Kakao SDK의 카카오내비 모듈이 제공하는 기능입니다. 카카오내비 앱을 실행하여 목적지를 공유하거나 길을 안내할 수 있습니다. 카카오내비 앱이 설치되어있지 않은 경우, 설치 페이지로 이동합니다.

카카오내비 기능 예시 화면![](https://developers.kakao.com/docs/_next/image?url=%2Fimg%2Fnavi_intro_ko.png&w=2040&q=75)

## 서비스 앱에 길 안내 제공하기[](https://developers.kakao.com/docs/ko/kakaonavi/common#navigation-in-your-service)

### 길찾기 SDK[](https://developers.kakao.com/docs/ko/kakaonavi/common#navigation-in-your-service-embedded-sdk)

카카오내비를 실행하지 않고 내 서비스 안에서 바로 길 안내 기능을 사용할 수 있는 내장형 SDK입니다. 카카오내비에 지도와 경로를 요청하여 내 서비스에 꼭 맞는 기능들을 선택해 사용할 수 있습니다. 사용자의 목적에 따라 사용자 맞춤 설정이 가능한 길찾기 SDK와 기본 UI를 제공하는 길찾기 SDK with UI 중 선택할 수 있습니다.

### 길찾기 API[](https://developers.kakao.com/docs/ko/kakaonavi/common#navigation-in-your-service-api)

REST API로 제공하는 길찾기 API는 길 안내에 필요한 핵심적인 기능을 제공합니다. 여러 개의 경유지가 포함된 경로를 설정하는 것, 한 출발지에서 여러 군데의 목적지로 가는 경로를 탐색하는 것과 같이 다양한 상황에 맞는 경로 탐색 결과를 제공할 수 있습니다.

**길찾기 SDK & API**

길찾기 SDK와 길찾기 API에 대한 상세 정보는 [카카오모빌리티 디벨로퍼스](https://developers.kakaomobility.com/product/naviapi.html)에서 확인할 수 있습니다.

## 이용 정책[](https://developers.kakao.com/docs/ko/kakaonavi/common#policy)

### 쿼터[](https://developers.kakao.com/docs/ko/kakaonavi/common#policy-quota)

카카오 API는 원활한 서비스 제공을 위해 월간 및 일간 쿼터(Quota)를 적용합니다. 현재 적용 중인 쿼터 정보는 [쿼터](https://developers.kakao.com/docs/ko/getting-started/quota)에서 확인할 수 있습니다. 적용된 쿼터 한도를 상향하기 위해서는 협의 및 제휴가 필요하므로 [별도 문의](https://devtalk.kakao.com/)합니다.

## 제공 API[](https://developers.kakao.com/docs/ko/kakaonavi/common#api-list)

아래 표는 Kakao SDK의 카카오내비 모듈이 제공하는 [카카오내비 앱으로 길 안내](https://developers.kakao.com/docs/ko/kakaonavi/common#launch-kakaonavi) 기능만 포함합니다. 각 API의 Kakao SDK 지원 여부는 [지원 범위](https://developers.kakao.com/docs/ko/getting-started/scope-of-support)에서 확인할 수 있습니다.

JavaScriptAndroidiOSFlutter

|API|레퍼런스|설명|
|---|---|---|
|[길 안내](https://developers.kakao.com/docs/ko/kakaonavi/js#navigation-info)|[`Kakao.Navi.start()`](https://developers.kakao.com/sdk/reference/js/release/Kakao.Navi.html#.start)|카카오내비를 실행하여 목적지까지의 길을 안내합니다.|
|[목적지 공유](https://developers.kakao.com/docs/ko/kakaonavi/js#share-destn-info)|[`Kakao.Navi.share()`](https://developers.kakao.com/sdk/reference/js/release/Kakao.Navi.html#.share)|카카오내비를 실행하여 지정한 목적지 정보를 공유합니다.|
카카오내비

# JavaScript

이 문서는 JavaScript SDK(Kakao SDK for JavaScript)를 사용한 카카오내비 API 구현 방법을 안내합니다.

JavaScript SDK는 `Kakao.Navi`의 API로 카카오내비 네이티브(Native) 앱에서 목적지 공유 및 길 안내 기능을 실행합니다. 카카오내비 앱이 설치돼 있다면 앱, 그렇지 않다면 설치 페이지를 엽니다.

이 문서에 포함된 기능들은 [도구] > [JS 데모]에서 JavaScript 예제 및 실제 동작을 확인할 수 있습니다.

[JS SDK 데모](https://developers.kakao.com/tool/demo/navi/start)

## 길 안내[](https://developers.kakao.com/docs/ko/kakaonavi/js#navigation)

##### 기본 정보[](https://developers.kakao.com/docs/ko/kakaonavi/js#navigation-info)

|레퍼런스|앱 설정|
|---|---|
|[`Kakao.Navi.start()`](https://developers.kakao.com/sdk/reference/js/release/Kakao.Navi.html#.start)|[설치](https://developers.kakao.com/docs/ko/javascript/getting-started#download)  <br>[초기화](https://developers.kakao.com/docs/ko/javascript/getting-started#init)|

|[권한](https://developers.kakao.com/docs/ko/getting-started/permission)|사전 설정|[카카오 로그인](https://developers.kakao.com/docs/ko/kakaologin/common)|[동의항목](https://developers.kakao.com/docs/ko/kakaologin/utilize#scope)|
|---|---|---|---|
|-|[JavaScript 키](https://developers.kakao.com/docs/ko/app-setting/app#javascript-key)  <br>[JavaScript SDK 도메인](https://developers.kakao.com/docs/ko/app-setting/app#js-domain)|-|-|

카카오내비를 실행하여 목적지까지의 길을 안내합니다.

**웹 길 안내 제공 종료**

- JavaScript SDK 1.41.0 버전부터 길 안내 시 카카오내비 앱이 설치돼 있지 않다면 설치 페이지로 이동되며, 웹 페이지로 길 안내를 실행하는 기능은 제공하지 않습니다.
- 자세한 내용은 [데브톡 공지사항](https://devtalk.kakao.com/t/120188)을 참고합니다.

#### 요청[](https://developers.kakao.com/docs/ko/kakaonavi/js#navigation-request)

`Kakao.Navi.start()`를 호출합니다. 필수 파라미터로 목적지 이름과 좌표를 전달해야 합니다.

`name`에 목적지 이름, `x`와 `y`에 목적지 좌표를 입력합니다. 좌표 타입은 `wgs84` 또는 `katec`여야 하고, `coordType` 파라미터로 지정할 수 있습니다.

이밖에 특정 차종이나 도로를 우선하는 등 길 안내 조건을 설정하기 위한 선택 파라미터들을 사용할 수 있습니다. 레퍼런스를 참고합니다.

#### 응답[](https://developers.kakao.com/docs/ko/kakaonavi/js#navigation-response)

요청 성공 시, 카카오내비 앱이 실행되어 공유한 목적지를 보여줍니다.

#### 예제[](https://developers.kakao.com/docs/ko/kakaonavi/js#navigation-sample)

Kakao.Navi.start({

  name: "현대백화점 판교점",

  x: 127.11205203011632,

  y: 37.39279717586919,

  coordType: "wgs84",

})

길 안내 예시 화면![](https://developers.kakao.com/docs/_next/image?url=%2Fimg%2Fnavi_start_ko.png&w=2040&q=75)

## 목적지 공유[](https://developers.kakao.com/docs/ko/kakaonavi/js#share-destn)

##### 기본 정보[](https://developers.kakao.com/docs/ko/kakaonavi/js#share-destn-info)

|레퍼런스|앱 설정|
|---|---|
|[`Kakao.Navi.share()`](https://developers.kakao.com/sdk/reference/js/release/Kakao.Navi.html#.share)|[설치](https://developers.kakao.com/docs/ko/javascript/getting-started#download)  <br>[초기화](https://developers.kakao.com/docs/ko/javascript/getting-started#init)|

|[권한](https://developers.kakao.com/docs/ko/getting-started/permission)|사전 설정|[카카오 로그인](https://developers.kakao.com/docs/ko/kakaologin/common)|[동의항목](https://developers.kakao.com/docs/ko/kakaologin/utilize#scope)|
|---|---|---|---|
|-|[JavaScript 키](https://developers.kakao.com/docs/ko/app-setting/app#javascript-key)  <br>[JavaScript SDK 도메인](https://developers.kakao.com/docs/ko/app-setting/app#js-domain)|-|-|

카카오내비를 실행하여 지정한 목적지 정보를 공유합니다.

#### 요청[](https://developers.kakao.com/docs/ko/kakaonavi/js#share-destn-request)

`Kakao.Navi.share()`를 호출합니다. 필수 파라미터로 목적지 이름과 좌표를 전달해야 합니다.

`name`에 목적지 이름, `x`와 `y`에 목적지 좌표를 입력합니다. 좌표 타입은 `wgs84` 또는 `katec`여야 하고, `coordType` 파라미터로 지정할 수 있습니다.

#### 응답[](https://developers.kakao.com/docs/ko/kakaonavi/js#share-destn-response)

요청 성공 시, 카카오내비 앱이 실행되어 공유한 목적지를 보여줍니다.

#### 예제[](https://developers.kakao.com/docs/ko/kakaonavi/js#share-destn-sample)

Kakao.Navi.share({

  name: "현대백화점 판교점",

  x: 127.11205203011632,

  y: 37.39279717586919,

  coordType: "wgs84",

})

목적지 공유 예시 화면![](https://developers.kakao.com/docs/_next/image?url=%2Fimg%2Fnavi_share_ko.png&w=2040&q=75)

### 도움이 되었나요?