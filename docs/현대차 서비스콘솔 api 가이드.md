#### 계정 API 호출

디벨로퍼스의 API를 활용하여 차량데이터를 획득하기 위해서는, 아래와 같은 절차를 통해 로그인 프로세스 진행 및 사용자 토큰을 획득해야 합니다.

1. 로그인 인증 요청 API를 통해 통합계정 로그인 창 호출하기

개발하시는 서비스 내에서, 로그인 인증 요청 API를 통해 현대자동차 통합계정 로그인창을 호출해야 합니다.  
다음은 로그인 창을 호출하는 간단한 예제를 HTML 과 Javascript로 작성한 예입니다.

- [HTML](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/guide_api#cont1)
- [Javascript](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/guide_api#cont2)

                                                        
`<html>     <head>         <title>로그인 인증 요청</title>     </head>     <body>         <a href=https://prd.kr-ccapi.hyundai.com/api/v1/user/oauth2/authorize? client_id={YOUR_CLIENT_ID}&redirect_uri={YOUR_REDIRECT_URI}&response_type=code&state={YOUR_STATE_TEXT}>로그인</a><!-- 해당 링크 클릭 시 로그인 인증 요청 API 호출-->     </body> </html>`
	
                                                    

정상적으로 호출이 되면, 아래와 같이 통합계정 로그인 창이 보여집니다.

![콘솔 로그인 화면](https://console.developers.hyundai.com/images/common_guide/img_guide_04_01.png)

해당 API 호출 시에는 Client ID 및 Redirect URL정보 등을 함께 전달해주어야 합니다.  
Redirect URL 정보는 Console > 설정 페이지 내에도 입력해주셔야 하며, 해당정보와 동일한 값을 API 호출 시 입력값으로 입력해주셔야 합니다.

2. 통합계정 로그인 및 차량 접근 권한 동의 수행

사용자는 통합계정 로그인을 진행합니다. 로그인된 정보가 올바르다면 아래와 같이 차량리스트가 표출되며, 차량별 접근 권한 동의 절차를 수행합니다.  
이 때, 사용자가 선택한 차량에 대해서만 API를 통한 데이터 확인이 가능합니다. 다만, 차량을 공유하였거나 공유받은 경우 차량 리스트에 차량이 표출되지 않습니다.

![접근 권한 동의 화면](https://console.developers.hyundai.com/images/common_guide/img_guide_04_02.png)

3. Authorization Code (인증코드) 확인 및 사용자 토큰 발급받기

차량 접근 권한 동의가 완료되면 사용자가 설정한 Redirect URL로 Authorization Code (인증코드) 값을 전달합니다.  
해당 인증코드를 바탕으로 사용자 토큰 발급/갱신/삭제 요청 API를 통해 사용자 토큰 (Access / Refresh Token) 을 발급 받습니다.  
발급받은 사용자 토큰을 활용하여, 사용자 정보 조회 및 개인정보 제공동의, 데이터 API 조회를 진행할 수 있습니다.  
아래 소스코드를 참고하여 Authorization Code 확인과 Access Token 발급 절차를 진행해주세요.

Authorization Code 확인

- [java](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/guide_api#cont3)
- [Javascript](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/guide_api#cont4)

```
@RequestMapping(value = "/authorization") //설정한 redirect_uri에 맞게 정의
public void account(@RequestParam(value="code") String code, @RequestParam(value="state") String state, HttpServletResponse response) throws IOException {

    String requestState = "{YOUR_STATE_TEXT}"; //request로 설정한 state와 동일한 값
    String redirectURL = "{YOUR_RECIRECT_URI}";


    // SUCCESS 200 Response code, state
    System.out.println("RESPONSE_STATE = " + state);
    System.out.println("RESPONSE_CODE = " + code);


    // state 검증
    if(!state.equals(requestState)) {
        System.out.println(state + " 유효하지 않은 state 응답입니다.");
        return;
    }
}
```

사용자 토큰 발급

- [java](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/guide_api#cont5)
- [Javascript](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/guide_api#cont6)

```
// 1. 계정 API 예제 – AccessToken 발급
@RequestMapping(value = "/authorization") //설정한 redirect_uri에 맞게 정의
public void getAccessToken(@RequestParam(value="code") String code,
    @RequestParam(value="state") String state,
    HttpServletResponse response) throws IOException {

    String requestBody = "grant_type=authorization_code&code=" + code + "&redirect_uri=" + "{YOUR_RECIRECT_URI}";
    String tokenResponse = tokenAPICall(requestBody);

    ObjectMapper accessTokenObjectMapper = new ObjectMapper();
    JsonNode TokenRoot = accessTokenObjectMapper.readTree(tokenResponse);
    String accessToken = TokenRoot.path("access_token").asText(); // Response에서 AccessToken 값 추출
    String refreshToken = TokenRoot.path("refresh_token").asText(); // Response에서 refreshToken 값 추출
    System.out.println("accessToken = " + accessToken);
    System.out.println("refreshToken = " + refreshToken);
}
```

사용자 토큰 갱신

- [java](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/guide_api#cont7)
- [Javascript](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/guide_api#cont8)

```
// 2. 계정 API 예제 – 토큰 갱신
public String tokenRefresh() throws IOException {
    // AccessToken 발급시에 받은 RefreshToken 사용
    String requestBody = "grant_type=refresh_token&refresh_token=" + "{YOUR_REFRESH_TOKEN}" + "&redirect_uri=" + "{YOUR_REDIRECT_URI}";

    String tokenResponse = tokenAPICall(requestBody);

    ObjectMapper accessTokenObjectMapper = new ObjectMapper();
    JsonNode TokenRoot = accessTokenObjectMapper.readTree(tokenResponse);
    String accessToken = TokenRoot.path("access_token").asText();
    System.out.println("갱신된 accessToken = " + accessToken);

    return accessToken;
}
```

사용자 토큰 삭제

- [java](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/guide_api#cont9)
- [Javascript](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/guide_api#cont10)

```
// 3. 계정 API 예제 – 토큰 삭제
public void tokenDelete() {
    String requestBody = "grant_type=delete&access_token=" + "{YOUR_ACCESS_TOKEN}" + "&redirect_uri=" + "{YOUR_RECIRECT_URI}";

    tokenAPICall(requestBody);
}
```

토큰 관련 메인 호출

- [java](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/guide_api#cont11)

                                                        
`public String tokenAPICall(String requestBody){  StringBuffer sb = null; String responseData = "";  String apiURL = "https://prd.kr-ccapi.hyundai.com/api/v1/user/oauth2/token";  String token = "Basic " + Base64.encodeBase64String(("{YOUR_CLIENT_ID}" + ":" + "{YOUR_CLIENT_SECRET}").getBytes()); String contentType = "application/x-www-form-urlencoded";  try{     URL url = new URL(apiURL);     HttpURLConnection con = (HttpURLConnection)url.openConnection();     con.setRequestMethod("POST");      // Set Header Info     con.setRequestProperty("Authorization", token);     con.setRequestProperty("Content-Type", contentType);      // Body data 전송     con.setDoOutput(true);     try (DataOutputStream output = new DataOutputStream(con.getOutputStream())){         output.writeBytes(requestBody);         output.flush();     }     catch(Exception e) {         e.printStackTrace();     }      int responseCode = con.getResponseCode();     BufferedReader br;     if(responseCode == HttpURLConnection.HTTP_OK){         br = new BufferedReader(new InputStreamReader(con.getInputStream())); // 정상호출     } else {         br = new BufferedReader(new InputStreamReader(con.getErrorStream())); // 에러발생     }      sb = new StringBuffer();     while ((responseData = br.readLine()) != null){         sb.append(responseData);     }     br.close();      System.out.println("responseCode = " + responseCode);     System.out.println("responseData = " + sb.toString());  } catch (Exception e) {     System.out.println(e); }  return sb.toString(); }`
	
                                                    

사용자 정보 조회

- [java](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/guide_api#cont13)
- [Javascript](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/guide_api#cont14)

                                                        
`// 계정 API 예제 사용자 정보 조회 public void userProfileAPICall(String accessToken) {    // 발급받은 Access Token      StringBuffer sb;     String responseData = "";     try{         String apiURL = "https://prd.kr-ccapi.hyundai.com/api/v1/user/profile";         URL url = new URL(apiURL);          HttpURLConnection con = (HttpURLConnection)url.openConnection();          con.setRequestMethod("GET");          // Set Header Info         con.setRequestProperty("Authorization", "Bearer " + accessToken);          int responseCode = con.getResponseCode();         BufferedReader br;         if(con.getResponseCode() == HttpURLConnection.HTTP_OK){             br = new BufferedReader(new InputStreamReader(con.getInputStream())); // 정상호출         } else {             br = new BufferedReader(new InputStreamReader(con.getErrorStream())); // 에러발생         }          sb = new StringBuffer();         while ((responseData = br.readLine()) != null){             sb.append(responseData);         }         br.close();          System.out.println("responseCode = " + responseCode);         System.out.println("userData = "+sb.toString());      } catch (Exception e) {         System.out.println(e);     } }`
	
                                                    

#### 데이터 API 호출

계정 API를 활용한 사용자 계정연동 및 차량 접근 권한 동의 이후, 데이터 API를 통한 사용자의 개인정보 제3자 제공 동의가 완료되면 API 를 통하여 차량 데이터를 확인 할 수 있습니다.

개인정보 제3자 제공 동의

사용자가 구현한 서비스 내에서 디벨로퍼스에서 제공하는 API를 사용하기 위해서는 고객의 개인정보 제공 동의 과정이 필수적으로 이루어져야 합니다.

STEP1  
계정 API를 통해 발급받은 사용자 토큰 (Access Token) 을 기반으로, 개인정보 제3자 제공 동의 요청 API를 호출하여 약관 동의 페이지를 연결합니다.  
개발 프로젝트 생성 시에는 개인정보 제3자 제공에 필요한 약관이 Default로 셋팅이 되어 있으며, 대고객 서비스를 위한 상용화 시점에는 상용화 신청을 통해 서비스 약관을 등록해주셔야 합니다.

STEP2  
사용자의 제3자 제공 동의 가 정상적으로 완료 시, 해당 사용자에 대한 API 응답이 가능한 상태로 변경되며, Redirect URL로 사용자 아이디 (useId)와 state값을 전달합니다.

연동 차량의 차량 정보 (carId 등) 가져오기

내 차량 리스트 조회 API를 통하여, 서비스 이용 동의가 완료된 사용자의 CCS 차량정보를 가져올 수 있습니다. 해당 API 호출을 통한 응답값으로 전달받은 carId는 차량 데이터 호출 시 필수적으로 입력되어야 하는 정보입니다.

데이터 API를 통한 차량 데이터 조회

계정 API를 통한 차량연동 및 차량 정보 조회가 정상적으로 진행 된 경우, 아래와 같이 데이터 API를 호출하여 차량 데이터를 호출 할 수 있습니다.

- [java](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/guide_api#cont15)
- [Javascript](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/guide_api#cont16)

                                                        
`// 데이터 API 예제 주행 가능 거리 조회 public class DteCallSampleCode {     public static void main(String[] args){          StringBuffer sb;         String responseData = "";          String token = "Bearer " + "{YOUR_ACCESS_TOKEN}";         String carID = "{YOUR_CAR_ID}";         String contentType = "application/json";         try{             String apiURL = "https://dev.kr-ccapi.hyundai.com/api/v1/car/status/"+ carID +"/dte";             URL url = new URL(apiURL);              HttpURLConnection con = (HttpURLConnection)url.openConnection();             con.setRequestMethod("GET");              // Set Header Info             con.setRequestProperty("Authorization", token);             con.setRequestProperty("Content-Type", contentType);              int responseCode = con.getResponseCode();             BufferedReader br;             if(responseCode == HttpURLConnection.HTTP_OK){                 br = new BufferedReader(new InputStreamReader(con.getInputStream())); // 정상호출             } else {                 br = new BufferedReader(new InputStreamReader(con.getErrorStream())); // 에러발생             }              sb = new StringBuffer();             while ((responseData = br.readLine()) != null){                 sb.append(responseData);             }             br.close();              System.out.println(sb.toString());          } catch (Exception e) {             System.out.println(e);         }     } }`

## 계정 API

### 로그인 인증 요청

현대자동차 통합 계정은 OAuth 2.0을 지원합니다.  
사용자 로그인 후 권한 동의 결과에 따라 Redirect URL로 Authorization Code(인증 코드)를 전달합니다.  
Redirect URL은 '설정 - 계정 API' 페이지에서 등록 가능합니다.

![GET](https://img.shields.io/badge/method-GET-green.svg) ![PUBLIC](https://img.shields.io/badge/service-PUBLIC-blue.svg) ![PUBLIC](https://img.shields.io/badge/KR-green.svg)

```
https://prd.kr-ccapi.hyundai.com/api/v1/user/oauth2/authorize
```

### Parameters

|Name|Type|Description|
|---|---|---|
|response_type|string|code로 입력|
|client_id|string|애플리케이션 등록 시 발급 받은 Client ID|
|redirect_uri|string|애플리케이션 등록 시 설정한 Redirect URL|
|state|string|애플리케이션에서 생성한 상태 토큰 값  <br>사이트 간 요청 위조(cross-site request forgery) 공격을 방지하기 위해 사용  <br>특수문자 사용 시, Base64 혹은 URL Encoding 필수|

### Success 200

|Name|Type|Description|
|---|---|---|
|code|string|로그인 인증 성공 시 발급된 인증 코드  <br>사용자 토큰 발급에 사용|
|state|string|애플리케이션에서 요청한 상태 토큰 값|

### Success Response

Success Response (Example):

```
HTTP/1.1 302 Found
Content-Length: 0
Location: https://www.example.com/auth/bluelink?code=A1B2C3&state=r_basicprofile
```

### Error 4xx

|Name|Type|Description|
|---|---|---|
|errCode|string|에러 코드|
|errMsg|string|에러에 대한 상세 설명|
|errId|string|에러 ID|

### Error Response

Error Response (Example):

```
{
  "errId": "123e4567-e89b-12d3-a456-426655440000",
  "errCode": "4002",
  "errMsg": "Invalid request body"
}
```

  

  

|에러 코드|에러 메시지|설명|
|---|---|---|
|4002|Invalid Request Body|호출 인자 값 오류|
|4003|Invalid Request Value|비밀번호 미일치 등 사용자의 입력 값이 틀린 경우 발생|
|4010|Require authentication|토큰 발급 시 호출 값 오류|
|4011|Invalid Access Token|접근 토큰 값 오류|
|4012|Deactivated User|사용자가 로그인 후 1년 경과하여 휴면계정으로 전환된 경우 발생|
|4081|Request Timeout|타임아웃 에러|
|4121|No Context|에러 코드로 상세 분류되어있지 않은 경우 발생|
|5001|Internal Server Error|API 내부 에러|
|9999|Undefined Error|API 내부 에러|
## 계정 API

### 사용자 토큰 발급/갱신/삭제 요청

API 호출에 필요한 사용자 토큰을 발급/갱신/삭제하기 위한 API입니다.  
access_token은 발급 후 24시간, refresh_token은 1년간 유효합니다.

![POST](https://img.shields.io/badge/method-POST-blue.svg) ![PUBLIC](https://img.shields.io/badge/service-PUBLIC-blue.svg) ![PUBLIC](https://img.shields.io/badge/KR-green.svg)

```
https://prd.kr-ccapi.hyundai.com/api/v1/user/oauth2/token
```

### Headers

|Name|Type|Description|
|---|---|---|
|Authorization|string|HTTP Basic 'ID:Secret' 값  <br>(애플리케이션 등록 시 발급받은 Client ID와 Client Secret 값으로 Base64 인코딩 값)|
|Content-Type|string|'application/x-www-form-urlencoded'로 전송|

### Parameters

|Name|Type|Description|
|---|---|---|
|grant_type|string|인증 구분 값  <br>1) 발급: authorization_code  <br>2) 갱신: refresh_token  <br>3) 삭제: delete|
|code ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|string|로그인 인증 요청 API 호출 후 발급 받은 인증 코드 값|
|redirect_uri ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|string|애플리케이션 등록 시 설정한 Redirect URL|
|refresh_token ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|string|Token 발급 시 응답으로 받은 갱신 토큰 값  <br>접근 토큰(access_token) 갱신 요청 시 입력|
|access_token ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|string|Token 발급 시 응답으로 받은 접근 토큰 값  <br>Token 삭제 요청 시 입력|

### Request (Example)

New Token

```
grant_type=authorization_code&code={code}&redirect_uri={redirect_uri}
```

Refresh Token

Delete Token

  

### Success 200

|Name|Type|Description|
|---|---|---|
|access_token|string|접근 토큰|
|refresh_token ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|string|갱신 토큰, 접근 토큰(access_token) 갱신 요청 시 사용|
|token_type ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|string|Bearer로 입력|
|expires_in ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|string|접근 토큰(access_token) 유효 기간(단위: 초)|

### Success Response

New Token

```
{ 
    "access_token": "***", 
    "token_type": "Bearer", 
    "refresh_token": "YDBRI832UM6DO_BB5TN12G", 
    "expires_in": 7200 
}
```

Refresh Token

Delete Token

  

### Error 4xx

|Name|Type|Description|
|---|---|---|
|errCode|string|에러 코드|
|errMsg|string|에러에 대한 상세 설명|
|errId|string|에러 ID|

### Error Response

Error Response (Example):

```
{
  "errId": "123e4567-e89b-12d3-a456-426655440000",
  "errCode": "4002",
  "errMsg": "Invalid request body"
}
```

  

  

|에러 코드|에러 메시지|설명|
|---|---|---|
|4002|Invalid Request Body|호출 인자 값 오류|
|4003|Invalid Request Value|비밀번호 미일치 등 사용자의 입력 값이 틀린 경우 발생|
|4010|Require authentication|토큰 발급 시 호출 값 오류|
|4011|Invalid Access Token|접근 토큰 값 오류|
|4012|Deactivated User|사용자가 로그인 후 1년 경과하여 휴면계정으로 전환된 경우 발생|
|4081|Request Timeout|타임아웃 에러|
|4121|No Context|에러 코드로 상세 분류되어있지 않은 경우 발생|
|5001|Internal Server Error|API 내부 에러|
|9999|Undefined Error|API 내부 에러|
## 계정 API

### 사용자 정보 조회

사용자에 대한 정보를 조회합니다.

![GET](https://img.shields.io/badge/method-GET-green.svg) ![PUBLIC](https://img.shields.io/badge/service-PUBLIC-blue.svg) ![PUBLIC](https://img.shields.io/badge/KR-green.svg)

```
https://prd.kr-ccapi.hyundai.com/api/v1/user/profile
```

### Headers

|Name|Type|Description|
|---|---|---|
|Authorization|string|Bearer {access_token}|

### Success 200

|Name|Type|Description|
|---|---|---|
|id|string|당사 발급 사용자 고유 식별자|
|email|string|이메일(가입 ID)|
|name|string|이름|
|mobileNum|string|휴대폰번호|
|birthdate|string|생년월일|
|lang|string|언어코드  <br>(ko: 국문, en: 영문, zh: 중문)|
|social|boolean|소셜로그인 등록 여부|

### Success Response

Success Response:

```
{ 
    "id": "12345680-5ca3-11e7-9d1d-95bfd5a660bc", 
    "email": "test@ccsp.com", 
    "name": "tester", 
    "mobileNum": "+821012345678", 
    "birthdate": "110111", 
    "lang": "en", 
    "social": true
}
```

### Error 4xx

|Name|Type|Description|
|---|---|---|
|errCode|string|에러 코드|
|errMsg|string|에러에 대한 상세 설명|
|errId|string|에러 ID|

### Error Response

Error Response (Example):

```
{
  "errId": "123e4567-e89b-12d3-a456-426655440000",
  "errCode": "4002",
  "errMsg": "Invalid request body"
}
```

  

|에러 코드|에러 메시지|설명|
|---|---|---|
|4002|Invalid Request Body|호출 인자 값 오류|
|4003|Invalid Request Value|비밀번호 미일치 등 사용자의 입력 값이 틀린 경우 발생|
|4010|Require authentication|토큰 발급 시 호출 값 오류|
|4011|Invalid Access Token|접근 토큰 값 오류|
|4012|Deactivated User|사용자가 로그인 후 1년 경과하여 휴면계정으로 전환된 경우 발생|
|4081|Request Timeout|타임아웃 에러|
|4121|No Context|에러 코드로 상세 분류되어있지 않은 경우 발생|
|5001|Internal Server Error|API 내부 에러|
|9999|Undefined Error|API 내부 에러|
## 데이터 API

### 개인정보 제공 동의 요청

사용자에게 개인정보 제 3자 제공 동의 페이지를 연결하기 위한 API입니다.  
사용자 동의 시, Redirect URL로 사용자 ID 값이 전달됩니다.

![POST](https://img.shields.io/badge/method-POST-blue.svg) ![PUBLIC](https://img.shields.io/badge/service-PUBLIC-blue.svg)

```
https://dev.kr-ccapi.hyundai.com/api/v1/car-service/terms/agreement
```

### Headers

|Name|Type|Description|
|---|---|---|
|Content-Type|string|MIMETYPE 'application/x-www-form-urlencoded'로 전송해야 함|

### Parameters

|Name|Type|Description|
|---|---|---|
|token|string|Bearer {access_token}|
|state|string|애플리케이션에서 요청한 상태 토큰 값|

### Success 200

|Name|Type|Description|
|---|---|---|
|userId|string|당사 발급 사용자 고유 식별자|
|state|string|애플리케이션에서 요청한 상태 토큰 값|

### Success Response

Success Response (Web):

```
HTTP/1.1 302 Found
Content-Length: 0
Location: https://dev.kr-ccapi.hyundai.com/web/v1/car-service
```

Success Response (Accepted):

```
HTTP/1.1 302 Found
Content-Length: 0
Location: redirect_url?userId=:userId&?state=:state
```

### Error

|Name|Type|Description|
|---|---|---|
|errCode|string|에러 코드|
|errMsg|string|에러에 대한 상세 설명|
|errId|string|에러 ID|

### Error Response

Error Response (보유 차량 없는 경우):

```
HTTP/1.1 302 Found
Content-Length: 0
Location: redirect_url?errCode=4046&errMsg=No%20registered%20 vehicles&errId=123e4567-e89b-12d3-a456-426655440000
```

Error Response (Example):

```
HTTP/1.1 302 Found
Content-Length: 0
Location: redirect_url?errCode=4002&errMsg=Invalid%20request%20 body&errId=123e4567-e89b-12d3-a456-426655440000
```

  

  

|에러 코드|에러 메시지|설명|
|---|---|---|
|4002|Invalid Request Body|호출 인자 값 오류|
|4011|Invalid Authorization Header|헤더 값 오류|
|4012|Invalid Session|세션 값 오류|
|4014|No Service term|약관 미등록 상태  <br>developers@hyundai.com에 문의하여 등록 요청해야 합니다.|
|4016|Unauthorized Client|서비스 인증 값 오류  <br>(adminKey 항목이 없거나 adminKey 이상)|
|4041|Unregistered Device|CCS 미가입 차량의 정보를 요청함  <br>(커넥티드서비스 미개통, 커넥티드서비스 해지, 커넥티드서비스 무료 기간 종료 후 유료 미전환)|
|4043|Unregistered User|CCS 미가입 고객의 정보를 요청함  <br>(입력된 생년월일 기준, 커넥티드서비스 계약자 정보 없음)|
|4045|No data|장기 미운행 차량, 단말 데이터 전송 오류 등으로 데이터 제공 불가|
|4046|No Registered Vehicles|차량 미보유 고객으로 데이터 제공 불가|
|4047|Agreement dose not exist|동의 이력이 없이 철회부터 진행 시 발생|
|4120|Pre-operation is required|선 호출 필요한 API를 호출하지 않은 경우 발생|
|5001|Internal Server Error|API 내부 에러|
|5003|Service Provider Error|연동 서비스 오류|
|5004|Internal Server Permission Error|API 내부 에러|
|5005|No Agreement Error|사용자가 정보 제공 미동의 상태로 데이터 제공 불가  <br>(커넥티드서비스 계약자가 제3자 제공 동의 '미동의')|
|5006|No Permission Error|API 호출 권한 없음|
|5007|Service not registered Error|등록된 서비스가 아닌 경우 발생|
|5008|Service not defined Error|서비스 정보 오류  <br>(맞지않는 서비스 ID)|
|5031|Unavailable remote control|차량 상태에 의해 원격제어가 불가능한 경우 발생|
|5032|Service Unavailable|데이터 조회 불가 차량으로 서비스 지원이 불가한 경우 발생|
|5041|Gateway Timeout|타임아웃 에러|
|9999|Undefined Error|API 내부 에러|
## 데이터 API

### 개인정보 제공 철회 요청

개인정보 제3자 제공 동의 여부가 미동의 상태로 변경되었을 때, 이 정보를 Developers 서버에 업데이트하기 위한 API입니다.

![GET](https://img.shields.io/badge/method-GET-green.svg) ![PUBLIC](https://img.shields.io/badge/service-PUBLIC-blue.svg)

```
https://dev.kr-ccapi.hyundai.com/api/v1/car-service/terms/reject
```

### Headers

|Name|Type|Description|
|---|---|---|
|Authorization|string|Bearer {access_token}|
|Content-Type ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|string|MIMETYPE _Default value : application/json_|

### Success 200

|Name|Type|Description|
|---|---|---|
|msgId|string|요청 결과 확인을 위한 메시지 ID|

### Success Response

Success Response:

```
{
  "msgId": "11e77efa-aff0-4b3c-a5a0-c4cde4674963"
}
```

### Error 4xx

|Name|Type|Description|
|---|---|---|
|errCode|string|에러 코드|
|errMsg|string|에러에 대한 상세 설명|
|errId|string|에러 ID|

### Error Response

Error Response (Example):

```
{
  "errId": "123e4567-e89b-12d3-a456-426655440000",
  "errCode": "4002",
  "errMsg": "Invalid request body"
}
```

  

  

|에러 코드|에러 메시지|설명|
|---|---|---|
|4002|Invalid Request Body|호출 인자 값 오류|
|4011|Invalid Authorization Header|헤더 값 오류|
|4012|Invalid Session|세션 값 오류|
|4014|No Service term|약관 미등록 상태  <br>developers@hyundai.com에 문의하여 등록 요청해야 합니다.|
|4016|Unauthorized Client|서비스 인증 값 오류  <br>(adminKey 항목이 없거나 adminKey 이상)|
|4041|Unregistered Device|CCS 미가입 차량의 정보를 요청함  <br>(커넥티드서비스 미개통, 커넥티드서비스 해지, 커넥티드서비스 무료 기간 종료 후 유료 미전환)|
|4043|Unregistered User|CCS 미가입 고객의 정보를 요청함  <br>(입력된 생년월일 기준, 커넥티드서비스 계약자 정보 없음)|
|4045|No data|장기 미운행 차량, 단말 데이터 전송 오류 등으로 데이터 제공 불가|
|4046|No Registered Vehicles|차량 미보유 고객으로 데이터 제공 불가|
|4047|Agreement dose not exist|동의 이력이 없이 철회부터 진행 시 발생|
|4120|Pre-operation is required|선 호출 필요한 API를 호출하지 않은 경우 발생|
|5001|Internal Server Error|API 내부 에러|
|5003|Service Provider Error|연동 서비스 오류|
|5004|Internal Server Permission Error|API 내부 에러|
|5005|No Agreement Error|사용자가 정보 제공 미동의 상태로 데이터 제공 불가  <br>(커넥티드서비스 계약자가 제3자 제공 동의 '미동의')|
|5006|No Permission Error|API 호출 권한 없음|
|5007|Service not registered Error|등록된 서비스가 아닌 경우 발생|
|5008|Service not defined Error|서비스 정보 오류  <br>(맞지않는 서비스 ID)|
|5031|Unavailable remote control|차량 상태에 의해 원격제어가 불가능한 경우 발생|
|5032|Service Unavailable|데이터 조회 불가 차량으로 서비스 지원이 불가한 경우 발생|
|5041|Gateway Timeout|타임아웃 에러|
|9999|Undefined Error|API 내부 에러|
## 데이터 API

### 내 차량 리스트 조회

사용자가 소유하고 있는 차량 리스트를 조회합니다.  
로그인 시점 접근 권한을 승인한 차량만 조회 가능합니다.

![GET](https://img.shields.io/badge/method-GET-green.svg) ![PUBLIC](https://img.shields.io/badge/service-PUBLIC-blue.svg)

```
https://dev.kr-ccapi.hyundai.com/api/v1/car/profile/carlist
```

### Headers

|Name|Type|Description|
|---|---|---|
|Authorization|string|Bearer {access_token}|

### Success 200

|Name|Type|Description|
|---|---|---|
|cars|object|차량 리스트|
|carId|string|당사 발급 차량 고유 식별자|
|carNickname|string|사용자가 커넥티드 서비스 앱에서 설정한 닉네임|
|carType|string|차량 타입  <br>(GN:내연기관, EV:전기, HEV:하이브리드, PHEV: 플러그인하이브리드, FCEV:수소전기)|
|carName|string|차종명(차종코드)|
|carSellname|string|차량 판매 모델명|
|msgId|string|요청 결과 확인을 위한 메시지 ID|

### Success Response

Success Response:

```
{
 "cars": [
   {
     "carId": "123e4567-c0a8-4af7-b8e5-262ea1f6aab4",
     "carNickname": "my sonata",
     "carType": "GN",
     "carName": "LF",
     "carSellname": "Sonata"
   }
 ],
 "msgId": "714dd6b9-af57-4c25-9630-0f0eef9175f9"
}
```

### Error 4xx

|Name|Type|Description|
|---|---|---|
|errCode|string|에러 코드|
|errMsg|string|에러에 대한 상세 설명|
|errId|string|에러 ID|

### Error Response

Error Response (보유 차량 없는 경우):

```
{
  "errId": "123e4567-e89b-12d3-a456-426655440000",
  "errCode": "4045",
  "errMsg": "No data"
}
```

Error Response (Example):

```
{
  "errId": "123e4567-e89b-12d3-a456-426655440000",
  "errCode": "4002",
  "errMsg": "Invalid request body"
}
```

  

  

|에러 코드|에러 메시지|설명|
|---|---|---|
|4002|Invalid Request Body|호출 인자 값 오류|
|4011|Invalid Authorization Header|헤더 값 오류|
|4012|Invalid Session|세션 값 오류|
|4014|No Service term|약관 미등록 상태  <br>developers@hyundai.com에 문의하여 등록 요청해야 합니다.|
|4016|Unauthorized Client|서비스 인증 값 오류  <br>(adminKey 항목이 없거나 adminKey 이상)|
|4041|Unregistered Device|CCS 미가입 차량의 정보를 요청함  <br>(커넥티드서비스 미개통, 커넥티드서비스 해지, 커넥티드서비스 무료 기간 종료 후 유료 미전환)|
|4043|Unregistered User|CCS 미가입 고객의 정보를 요청함  <br>(입력된 생년월일 기준, 커넥티드서비스 계약자 정보 없음)|
|4045|No data|장기 미운행 차량, 단말 데이터 전송 오류 등으로 데이터 제공 불가|
|4046|No Registered Vehicles|차량 미보유 고객으로 데이터 제공 불가|
|4047|Agreement dose not exist|동의 이력이 없이 철회부터 진행 시 발생|
|4120|Pre-operation is required|선 호출 필요한 API를 호출하지 않은 경우 발생|
|5001|Internal Server Error|API 내부 에러|
|5003|Service Provider Error|연동 서비스 오류|
|5004|Internal Server Permission Error|API 내부 에러|
|5005|No Agreement Error|사용자가 정보 제공 미동의 상태로 데이터 제공 불가  <br>(커넥티드서비스 계약자가 제3자 제공 동의 '미동의')|
|5006|No Permission Error|API 호출 권한 없음|
|5007|Service not registered Error|등록된 서비스가 아닌 경우 발생|
|5008|Service not defined Error|서비스 정보 오류  <br>(맞지않는 서비스 ID)|
|5031|Unavailable remote control|차량 상태에 의해 원격제어가 불가능한 경우 발생|
|5032|Service Unavailable|데이터 조회 불가 차량으로 서비스 지원이 불가한 경우 발생|
|5041|Gateway Timeout|타임아웃 에러|
|9999|Undefined Error|API 내부 에러|
## 데이터 API

### 커넥티드 서비스 가입일/무료 종료일 조회

[Sample Test](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/specification/data/carprofile_contract#a)

차량의 커넥티드 서비스(blueLink) 가입일과 무료 서비스 종료일 정보를 조회합니다.  
2020년 기준 신차 구입 이후 최초 서비스 가입에 한해 5년 동안 무료 서비스가 제공됩니다.

![GET](https://img.shields.io/badge/method-GET-green.svg) ![PUBLIC](https://img.shields.io/badge/service-PUBLIC-blue.svg)

```
https://dev.kr-ccapi.hyundai.com/api/v1/car/profile/:carId/contract
```

### Headers

|Name|Type|Description|
|---|---|---|
|Authorization|string|Bearer {access_token}|

### Parameters

|Name|Type|Description|
|---|---|---|
|carId|string|당사 발급 차량 고유 식별자|

### Success 200

|Name|Type|Description|
|---|---|---|
|subscribeDate|date|커넥티드 서비스 가입일(YYYYMMDD)|
|endDate ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|date|무료 서비스 종료일(YYYYMMDD)|
|msgId|string|요청 결과 확인을 위한 메시지 ID|

### Success Response

Success Response:

```
{
  "subscribeDate": "20180711",
  "endDate": "20230710",
  "msgId":"714dd6b9-af57-4c25-9630-0f0eef9175f9"
}
```

### Error 4xx

|Name|Type|Description|
|---|---|---|
|errCode|string|에러 코드|
|errMsg|string|에러에 대한 상세 설명|
|errId|string|에러 ID|

### Error Response

Error Response (Example):

```
{
  "errId": "123e4567-e89b-12d3-a456-426655440000",
  "errCode": "4002",
  "errMsg": "Invalid request body"
}
```

  

  

|에러 코드|에러 메시지|설명|
|---|---|---|
|4002|Invalid Request Body|호출 인자 값 오류|
|4011|Invalid Authorization Header|헤더 값 오류|
|4012|Invalid Session|세션 값 오류|
|4014|No Service term|약관 미등록 상태  <br>developers@hyundai.com에 문의하여 등록 요청해야 합니다.|
|4016|Unauthorized Client|서비스 인증 값 오류  <br>(adminKey 항목이 없거나 adminKey 이상)|
|4041|Unregistered Device|CCS 미가입 차량의 정보를 요청함  <br>(커넥티드서비스 미개통, 커넥티드서비스 해지, 커넥티드서비스 무료 기간 종료 후 유료 미전환)|
|4043|Unregistered User|CCS 미가입 고객의 정보를 요청함  <br>(입력된 생년월일 기준, 커넥티드서비스 계약자 정보 없음)|
|4045|No data|장기 미운행 차량, 단말 데이터 전송 오류 등으로 데이터 제공 불가|
|4046|No Registered Vehicles|차량 미보유 고객으로 데이터 제공 불가|
|4047|Agreement dose not exist|동의 이력이 없이 철회부터 진행 시 발생|
|4120|Pre-operation is required|선 호출 필요한 API를 호출하지 않은 경우 발생|
|5001|Internal Server Error|API 내부 에러|
|5003|Service Provider Error|연동 서비스 오류|
|5004|Internal Server Permission Error|API 내부 에러|
|5005|No Agreement Error|사용자가 정보 제공 미동의 상태로 데이터 제공 불가  <br>(커넥티드서비스 계약자가 제3자 제공 동의 '미동의')|
|5006|No Permission Error|API 호출 권한 없음|
|5007|Service not registered Error|등록된 서비스가 아닌 경우 발생|
|5008|Service not defined Error|서비스 정보 오류  <br>(맞지않는 서비스 ID)|
|5031|Unavailable remote control|차량 상태에 의해 원격제어가 불가능한 경우 발생|
|5032|Service Unavailable|데이터 조회 불가 차량으로 서비스 지원이 불가한 경우 발생|
|5041|Gateway Timeout|타임아웃 에러|
|9999|Undefined Error|API 내부 에러|

## Sample Test

CarID6d97337b-eb53-467b-baf4-7faec6d7065e3f979d64-1e57-4ead-90af-25da1756e206ce7dfc88-f6b3-41ad-9099-4eb57bce4944b23f1cd3-517c-4ac0-b574-cfc8eeca5fed10cc6538-82b5-48aa-9d85-16416b8e07fb

API 호출하기 초기화
## 데이터 API

### 주행 가능 거리 조회

[Sample Test](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/specification/data/status_dte#a)

차량의 주행 가능 거리를 조회하는 API 입니다.  
시동 종료 시점을 기준으로 업데이트되며, 2개월 미운행 차량의 데이터는 조회 불가합니다.  

![GET](https://img.shields.io/badge/method-GET-green.svg) ![PUBLIC](https://img.shields.io/badge/service-PUBLIC-blue.svg)

```
https://dev.kr-ccapi.hyundai.com/api/v1/car/status/:carId/dte
```

### Headers

|Name|Type|Description|
|---|---|---|
|Authorization|string|Bearer {access_token}|
|Content-Type ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|string|MIMETYPE _Default value : application/json_|

### Parameters

|Name|Type|Description|
|---|---|---|
|carId|string|당사 발급 차량 고유 식별자|

### Success 200

|Name|Type|Description|
|---|---|---|
|timestamp|datetime|차량 전송 시간(YYYYMMDDHHmmSS)|
|value|number|거리 수치|
|unit|number|단위(0: feet, 1: km, 2: meter, 3: miles)|
|phevTotalValue ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|number|PHEV 차량의 Battery + Engine 주행가능거리  <br>거리 수치|
|phevTotalUnit ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|number|PHEV 차량의 Battery + Engine 주행가능거리  <br>단위(0: feet, 1: km, 2: meter, 3: miles)|
|msgId|string|요청 결과 확인을 위한 메시지 ID|

### Success Response

Success Response (Example):

```
{
  "timestamp": "20200114152139",
  "value": 32.3,
  "unit": 1,
  "msgId": "714dd6b9-af57-4c25-9630-0f0eef9175f9"
}
```

### Error 4xx

|Name|Type|Description|
|---|---|---|
|errCode|string|에러 코드|
|errMsg|string|에러에 대한 상세 설명|
|errId|string|에러 ID|

### Error Response

Error Response (Example):

```
{
  "errId": "123e4567-e89b-12d3-a456-426655440000",
  "errCode": "4002",
  "errMsg": "Invalid request body"
}
```

  

  

|에러 코드|에러 메시지|설명|
|---|---|---|
|4002|Invalid Request Body|호출 인자 값 오류|
|4011|Invalid Authorization Header|헤더 값 오류|
|4012|Invalid Session|세션 값 오류|
|4014|No Service term|약관 미등록 상태  <br>developers@hyundai.com에 문의하여 등록 요청해야 합니다.|
|4016|Unauthorized Client|서비스 인증 값 오류  <br>(adminKey 항목이 없거나 adminKey 이상)|
|4041|Unregistered Device|CCS 미가입 차량의 정보를 요청함  <br>(커넥티드서비스 미개통, 커넥티드서비스 해지, 커넥티드서비스 무료 기간 종료 후 유료 미전환)|
|4043|Unregistered User|CCS 미가입 고객의 정보를 요청함  <br>(입력된 생년월일 기준, 커넥티드서비스 계약자 정보 없음)|
|4045|No data|장기 미운행 차량, 단말 데이터 전송 오류 등으로 데이터 제공 불가|
|4046|No Registered Vehicles|차량 미보유 고객으로 데이터 제공 불가|
|4047|Agreement dose not exist|동의 이력이 없이 철회부터 진행 시 발생|
|4120|Pre-operation is required|선 호출 필요한 API를 호출하지 않은 경우 발생|
|5001|Internal Server Error|API 내부 에러|
|5003|Service Provider Error|연동 서비스 오류|
|5004|Internal Server Permission Error|API 내부 에러|
|5005|No Agreement Error|사용자가 정보 제공 미동의 상태로 데이터 제공 불가  <br>(커넥티드서비스 계약자가 제3자 제공 동의 '미동의')|
|5006|No Permission Error|API 호출 권한 없음|
|5007|Service not registered Error|등록된 서비스가 아닌 경우 발생|
|5008|Service not defined Error|서비스 정보 오류  <br>(맞지않는 서비스 ID)|
|5031|Unavailable remote control|차량 상태에 의해 원격제어가 불가능한 경우 발생|
|5032|Service Unavailable|데이터 조회 불가 차량으로 서비스 지원이 불가한 경우 발생|
|5041|Gateway Timeout|타임아웃 에러|
|9999|Undefined Error|API 내부 에러|

## Sample Test

CarID6d97337b-eb53-467b-baf4-7faec6d7065e3f979d64-1e57-4ead-90af-25da1756e206ce7dfc88-f6b3-41ad-9099-4eb57bce4944b23f1cd3-517c-4ac0-b574-cfc8eeca5fed10cc6538-82b5-48aa-9d85-16416b8e07fb

API 호출하기 초기화
## 데이터 API

### 누적 운행 거리 조회

[Sample Test](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/specification/data/status_odometer#a)

차량의 누적 운행 거리를 조회하는 API 입니다.  
시동 종료 시점을 기준으로 업데이트됩니다.

![GET](https://img.shields.io/badge/method-GET-green.svg) ![PUBLIC](https://img.shields.io/badge/service-PUBLIC-blue.svg)

```
https://dev.kr-ccapi.hyundai.com/api/v1/car/status/:carId/odometer
```

### Headers

|Name|Type|Description|
|---|---|---|
|Authorization|string|Bearer {access_token}|
|Content-Type ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|string|MIMETYPE _Default value : application/json_|

### Parameters

|Name|Type|Description|
|---|---|---|
|carId|string|당사 발급 차량 고유 식별자|

### Success 200

|Name|Type|Description|
|---|---|---|
|odometers|object|누적 운행 거리|
|date|date|조회일자(YYYYMMDD)|
|timestamp|datetime|차량 전송 시간(YYYYMMDDHHmmSS)|
|value|number|거리 수치 (소수점 절사)|
|unit|number|단위  <br>(0: feet, 1: km, 2: meter, 3: miles)|
|msgId|string|요청 결과 확인을 위한 메시지 ID|

### Success Response

Success Response (Example):

```
{
  "msgId": "5db9fc02-1b36-448e-9307-52761fd9ad92",
  "odometers": [
    {
      "date": "20190821",
      "unit": 1,
      "value": 12320,
      "timestamp": "20200114152139"
    }
  ]
}
```

### Error 4xx

|Name|Type|Description|
|---|---|---|
|errCode|string|에러 코드|
|errMsg|string|에러에 대한 상세 설명|
|errId|string|에러 ID|

### Error Response

Error Response (Example):

```
{
  "errId": "123e4567-e89b-12d3-a456-426655440000",
  "errCode": "4002",
  "errMsg": "Invalid request body"
}
```

  

  

|에러 코드|에러 메시지|설명|
|---|---|---|
|4002|Invalid Request Body|호출 인자 값 오류|
|4011|Invalid Authorization Header|헤더 값 오류|
|4012|Invalid Session|세션 값 오류|
|4014|No Service term|약관 미등록 상태  <br>developers@hyundai.com에 문의하여 등록 요청해야 합니다.|
|4016|Unauthorized Client|서비스 인증 값 오류  <br>(adminKey 항목이 없거나 adminKey 이상)|
|4041|Unregistered Device|CCS 미가입 차량의 정보를 요청함  <br>(커넥티드서비스 미개통, 커넥티드서비스 해지, 커넥티드서비스 무료 기간 종료 후 유료 미전환)|
|4043|Unregistered User|CCS 미가입 고객의 정보를 요청함  <br>(입력된 생년월일 기준, 커넥티드서비스 계약자 정보 없음)|
|4045|No data|장기 미운행 차량, 단말 데이터 전송 오류 등으로 데이터 제공 불가|
|4046|No Registered Vehicles|차량 미보유 고객으로 데이터 제공 불가|
|4047|Agreement dose not exist|동의 이력이 없이 철회부터 진행 시 발생|
|4120|Pre-operation is required|선 호출 필요한 API를 호출하지 않은 경우 발생|
|5001|Internal Server Error|API 내부 에러|
|5003|Service Provider Error|연동 서비스 오류|
|5004|Internal Server Permission Error|API 내부 에러|
|5005|No Agreement Error|사용자가 정보 제공 미동의 상태로 데이터 제공 불가  <br>(커넥티드서비스 계약자가 제3자 제공 동의 '미동의')|
|5006|No Permission Error|API 호출 권한 없음|
|5007|Service not registered Error|등록된 서비스가 아닌 경우 발생|
|5008|Service not defined Error|서비스 정보 오류  <br>(맞지않는 서비스 ID)|
|5031|Unavailable remote control|차량 상태에 의해 원격제어가 불가능한 경우 발생|
|5032|Service Unavailable|데이터 조회 불가 차량으로 서비스 지원이 불가한 경우 발생|
|5041|Gateway Timeout|타임아웃 에러|
|9999|Undefined Error|API 내부 에러|

## Sample Test

CarID6d97337b-eb53-467b-baf4-7faec6d7065e3f979d64-1e57-4ead-90af-25da1756e206ce7dfc88-f6b3-41ad-9099-4eb57bce4944b23f1cd3-517c-4ac0-b574-cfc8eeca5fed10cc6538-82b5-48aa-9d85-16416b8e07fb

API 호출하기 초기화
## 데이터 API

### 전기차 충전 상태 조회

[Sample Test](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/specification/data/status_evcharging#a)

전기차 차량의 충전 중 정보를 조회하는 API입니다.

![GET](https://img.shields.io/badge/method-GET-green.svg) ![PUBLIC](https://img.shields.io/badge/service-PUBLIC-blue.svg)

```
https://dev.kr-ccapi.hyundai.com/api/v1/car/status/:carId/ev/charging
```

### Headers

|Name|Type|Description|
|---|---|---|
|Authorization|string|Bearer {access_token}|
|Content-Type ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|string|MIMETYPE _Default value : application/json_|

### Parameters

|Name|Type|Description|
|---|---|---|
|carId|string|당사 발급 차량 고유 식별자|

### Success 200

|Name|Type|Description|
|---|---|---|
|batteryPlugin|number|플러그 연결 여부 (0: 연결 안됨, 1: 급속 충전기 연결, 2: 일반 충전기 연결)|
|batteryCharge|boolean|충전 여부|
|soc|number|배터리 잔량(단위: %)|
|targetSOC ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|object|목표 충전 설정값|
|plugType ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|number|충전기 타입 (0 : DC charger, 1 : AC w/ 240V, 2 : AC w/ 120V)|
|targetSOClevel ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|number|충전 목표 배터리 잔량|
|remainTime|object|목표 충전까지 남은 시간  <br>-충전 연결 상태: 잔여 충전 시간  <br>- 충전 미연결 상태: 240V 충전 시 잔여 충전 시간|
|value|number|시간 간격 수치|
|unit|number|단위 (0: hour, 1: min, 2: msec, 3: sec)|
|timestamp|datetime|차량 전송 시간|
|msgId|string|요청 결과 확인을 위한 메시지 ID|

### Success Response

Success Response (Example):

```
{
  "batteryPlugin": 1,
  "batteryCharge": true,
  "soc": 51,
  "targetSOC": {
    "plugType": 0,
    "targetSOClevel": 80,
  },
  "remainTime": {
    "value": 17,
    "unit": 1
  },
  "timestamp": "20200701101011",
  "msgId": "bc0b86cb-f9bc-4013-b9ca-e353894a341a"
}
```

### Error 4xx

|Name|Type|Description|
|---|---|---|
|errCode|string|에러 코드|
|errMsg|string|에러에 대한 상세 설명|
|errId|string|에러 ID|

### Error Response

Error Response (Example):

```
{
  "errId": "123e4567-e89b-12d3-a456-426655440000",
  "errCode": "4002",
  "errMsg": "Invalid request body"
}
```

  

  

|에러 코드|에러 메시지|설명|
|---|---|---|
|4002|Invalid Request Body|호출 인자 값 오류|
|4011|Invalid Authorization Header|헤더 값 오류|
|4012|Invalid Session|세션 값 오류|
|4014|No Service term|약관 미등록 상태  <br>developers@hyundai.com에 문의하여 등록 요청해야 합니다.|
|4016|Unauthorized Client|서비스 인증 값 오류  <br>(adminKey 항목이 없거나 adminKey 이상)|
|4041|Unregistered Device|CCS 미가입 차량의 정보를 요청함  <br>(커넥티드서비스 미개통, 커넥티드서비스 해지, 커넥티드서비스 무료 기간 종료 후 유료 미전환)|
|4043|Unregistered User|CCS 미가입 고객의 정보를 요청함  <br>(입력된 생년월일 기준, 커넥티드서비스 계약자 정보 없음)|
|4045|No data|장기 미운행 차량, 단말 데이터 전송 오류 등으로 데이터 제공 불가|
|4046|No Registered Vehicles|차량 미보유 고객으로 데이터 제공 불가|
|4047|Agreement dose not exist|동의 이력이 없이 철회부터 진행 시 발생|
|4120|Pre-operation is required|선 호출 필요한 API를 호출하지 않은 경우 발생|
|5001|Internal Server Error|API 내부 에러|
|5003|Service Provider Error|연동 서비스 오류|
|5004|Internal Server Permission Error|API 내부 에러|
|5005|No Agreement Error|사용자가 정보 제공 미동의 상태로 데이터 제공 불가  <br>(커넥티드서비스 계약자가 제3자 제공 동의 '미동의')|
|5006|No Permission Error|API 호출 권한 없음|
|5007|Service not registered Error|등록된 서비스가 아닌 경우 발생|
|5008|Service not defined Error|서비스 정보 오류  <br>(맞지않는 서비스 ID)|
|5031|Unavailable remote control|차량 상태에 의해 원격제어가 불가능한 경우 발생|
|5032|Service Unavailable|데이터 조회 불가 차량으로 서비스 지원이 불가한 경우 발생|
|5041|Gateway Timeout|타임아웃 에러|
|9999|Undefined Error|API 내부 에러|

## Sample Test

CarID6d97337b-eb53-467b-baf4-7faec6d7065e3f979d64-1e57-4ead-90af-25da1756e206ce7dfc88-f6b3-41ad-9099-4eb57bce4944b23f1cd3-517c-4ac0-b574-cfc8eeca5fed10cc6538-82b5-48aa-9d85-16416b8e07fb

API 호출하기 초기화
## 데이터 API

### 전기차 배터리 잔량 조회

[Sample Test](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/specification/data/status_evbattery#a)

전기차 차량의 배터리 잔량 정보를 조회하는 API입니다.

![GET](https://img.shields.io/badge/method-GET-green.svg) ![PUBLIC](https://img.shields.io/badge/service-PUBLIC-blue.svg)

```
https://dev.kr-ccapi.hyundai.com/api/v1/car/status/:carId/ev/battery
```

### Headers

|Name|Type|Description|
|---|---|---|
|Authorization|string|Bearer {access_token}|
|Content-Type ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|string|MIMETYPE _Default value : application/json_|

### Parameters

|Name|Type|Description|
|---|---|---|
|carId|string|당사 발급 차량 고유 식별자|

### Success 200

|Name|Type|Description|
|---|---|---|
|soc|number|배터리 잔량(단위: %)|
|timestamp|datetime|차량 전송 시간|
|msgId|string|요청 결과 확인을 위한 메시지 ID|

### Success Response

Success Response (Example):

```
{
  "soc": 100,
  "timestamp": "20200701101011",
  "msgId": "bc0b86cb-f9bc-4013-b9ca-e353894a341a"
}
```

### Error 4xx

|Name|Type|Description|
|---|---|---|
|errCode|string|에러 코드|
|errMsg|string|에러에 대한 상세 설명|
|errId|string|에러 ID|

### Error Response

Error Response (Example):

```
{
  "errId": "123e4567-e89b-12d3-a456-426655440000",
  "errCode": "4002",
  "errMsg": "Invalid request body"
}
```

  

  

|에러 코드|에러 메시지|설명|
|---|---|---|
|4002|Invalid Request Body|호출 인자 값 오류|
|4011|Invalid Authorization Header|헤더 값 오류|
|4012|Invalid Session|세션 값 오류|
|4014|No Service term|약관 미등록 상태  <br>developers@hyundai.com에 문의하여 등록 요청해야 합니다.|
|4016|Unauthorized Client|서비스 인증 값 오류  <br>(adminKey 항목이 없거나 adminKey 이상)|
|4041|Unregistered Device|CCS 미가입 차량의 정보를 요청함  <br>(커넥티드서비스 미개통, 커넥티드서비스 해지, 커넥티드서비스 무료 기간 종료 후 유료 미전환)|
|4043|Unregistered User|CCS 미가입 고객의 정보를 요청함  <br>(입력된 생년월일 기준, 커넥티드서비스 계약자 정보 없음)|
|4045|No data|장기 미운행 차량, 단말 데이터 전송 오류 등으로 데이터 제공 불가|
|4046|No Registered Vehicles|차량 미보유 고객으로 데이터 제공 불가|
|4047|Agreement dose not exist|동의 이력이 없이 철회부터 진행 시 발생|
|4120|Pre-operation is required|선 호출 필요한 API를 호출하지 않은 경우 발생|
|5001|Internal Server Error|API 내부 에러|
|5003|Service Provider Error|연동 서비스 오류|
|5004|Internal Server Permission Error|API 내부 에러|
|5005|No Agreement Error|사용자가 정보 제공 미동의 상태로 데이터 제공 불가  <br>(커넥티드서비스 계약자가 제3자 제공 동의 '미동의')|
|5006|No Permission Error|API 호출 권한 없음|
|5007|Service not registered Error|등록된 서비스가 아닌 경우 발생|
|5008|Service not defined Error|서비스 정보 오류  <br>(맞지않는 서비스 ID)|
|5031|Unavailable remote control|차량 상태에 의해 원격제어가 불가능한 경우 발생|
|5032|Service Unavailable|데이터 조회 불가 차량으로 서비스 지원이 불가한 경우 발생|
|5041|Gateway Timeout|타임아웃 에러|
|9999|Undefined Error|API 내부 에러|

## Sample Test

CarID6d97337b-eb53-467b-baf4-7faec6d7065e3f979d64-1e57-4ead-90af-25da1756e206ce7dfc88-f6b3-41ad-9099-4eb57bce4944b23f1cd3-517c-4ac0-b574-cfc8eeca5fed10cc6538-82b5-48aa-9d85-16416b8e07fb

API 호출하기 초기화

## 데이터 API

### 주유 경고등 상태 조회

[Sample Test](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/specification/data/statuswarning_lowfuellight#a)

주유 경고등 상태를 조회하는 API입니다.  
시동 종료 시점을 기준으로 업데이트됩니다.

![GET](https://img.shields.io/badge/method-GET-green.svg) ![PUBLIC](https://img.shields.io/badge/service-PUBLIC-blue.svg)

```
https://dev.kr-ccapi.hyundai.com/api/v1/car/status/warning/:carId/lowFuel
```

### Headers

|Name|Type|Description|
|---|---|---|
|Authorization|string|Bearer {access_token}|
|Content-Type ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|string|MIMETYPE _Default value : application/json_|

### Parameters

|Name|Type|Description|
|---|---|---|
|carId|string|당사 발급 차량 고유 식별자|

### Success 200

|Name|Type|Description|
|---|---|---|
|status|boolean|경고등 on/off 상태|
|msgId|string|요청 결과 확인을 위한 메시지 ID|

### Success Response

Success Response (Example):

```
{
  "status": false,
  "msgId": "714dd6b9-af57-4c25-9630-0f0eef9175f9"
}
```

### Error 4xx

|Name|Type|Description|
|---|---|---|
|errCode|string|에러 코드|
|errMsg|string|에러에 대한 상세 설명|
|errId|string|에러 ID|

### Error Response

Error Response (Example):

```
{
  "errId": "123e4567-e89b-12d3-a456-426655440000",
  "errCode": "4002",
  "errMsg": "Invalid request body"
}
```

  

  

|에러 코드|에러 메시지|설명|
|---|---|---|
|4002|Invalid Request Body|호출 인자 값 오류|
|4011|Invalid Authorization Header|헤더 값 오류|
|4012|Invalid Session|세션 값 오류|
|4014|No Service term|약관 미등록 상태  <br>developers@hyundai.com에 문의하여 등록 요청해야 합니다.|
|4016|Unauthorized Client|서비스 인증 값 오류  <br>(adminKey 항목이 없거나 adminKey 이상)|
|4041|Unregistered Device|CCS 미가입 차량의 정보를 요청함  <br>(커넥티드서비스 미개통, 커넥티드서비스 해지, 커넥티드서비스 무료 기간 종료 후 유료 미전환)|
|4043|Unregistered User|CCS 미가입 고객의 정보를 요청함  <br>(입력된 생년월일 기준, 커넥티드서비스 계약자 정보 없음)|
|4045|No data|장기 미운행 차량, 단말 데이터 전송 오류 등으로 데이터 제공 불가|
|4046|No Registered Vehicles|차량 미보유 고객으로 데이터 제공 불가|
|4047|Agreement dose not exist|동의 이력이 없이 철회부터 진행 시 발생|
|4120|Pre-operation is required|선 호출 필요한 API를 호출하지 않은 경우 발생|
|5001|Internal Server Error|API 내부 에러|
|5003|Service Provider Error|연동 서비스 오류|
|5004|Internal Server Permission Error|API 내부 에러|
|5005|No Agreement Error|사용자가 정보 제공 미동의 상태로 데이터 제공 불가  <br>(커넥티드서비스 계약자가 제3자 제공 동의 '미동의')|
|5006|No Permission Error|API 호출 권한 없음|
|5007|Service not registered Error|등록된 서비스가 아닌 경우 발생|
|5008|Service not defined Error|서비스 정보 오류  <br>(맞지않는 서비스 ID)|
|5031|Unavailable remote control|차량 상태에 의해 원격제어가 불가능한 경우 발생|
|5032|Service Unavailable|데이터 조회 불가 차량으로 서비스 지원이 불가한 경우 발생|
|5041|Gateway Timeout|타임아웃 에러|
|9999|Undefined Error|API 내부 에러|

## Sample Test

CarID6d97337b-eb53-467b-baf4-7faec6d7065e3f979d64-1e57-4ead-90af-25da1756e206ce7dfc88-f6b3-41ad-9099-4eb57bce4944b23f1cd3-517c-4ac0-b574-cfc8eeca5fed10cc6538-82b5-48aa-9d85-16416b8e07fb

API 호출하기 초기화

## 데이터 API

### 타이어 공기압 경고등 상태 조회

[Sample Test](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/specification/data/statuswarning_tirepressurelamp#a)

타이어 공기압 경고등 상태를 조회하는 API입니다.  
시동 종료, EV/PHEV 충전 종료 시점을 기준으로 업데이트됩니다.

![GET](https://img.shields.io/badge/method-GET-green.svg) ![PUBLIC](https://img.shields.io/badge/service-PUBLIC-blue.svg)

```
https://dev.kr-ccapi.hyundai.com/api/v1/car/status/warning/:carId/tirePressure
```

### Headers

|Name|Type|Description|
|---|---|---|
|Authorization|string|Bearer {access_token}|
|Content-Type ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|string|MIMETYPE _Default value : application/json_|

### Parameters

|Name|Type|Description|
|---|---|---|
|carId|string|당사 발급 차량 고유 식별자|

### Success 200

|Name|Type|Description|
|---|---|---|
|status|boolean|타이어 공기압 경고등 상태 (true : Tire Pressure Lamp ON / false : Tire Pressure Lamp OFF)|
|msgId|string|요청 결과 확인을 위한 메시지 ID|

### Success Response

Success Response (Example):

```
{
  "status": false,
  "msgId": "714dd6b9-af57-4c25-9630-0f0eef9175f9"
}
```

### Error 4xx

|Name|Type|Description|
|---|---|---|
|errCode|string|에러 코드|
|errMsg|string|에러에 대한 상세 설명|
|errId|string|에러 ID|

### Error Response

Error Response (Example):

```
{
  "errId": "123e4567-e89b-12d3-a456-426655440000",
  "errCode": "4002",
  "errMsg": "Invalid request body"
}
```

  

  

|에러 코드|에러 메시지|설명|
|---|---|---|
|4002|Invalid Request Body|호출 인자 값 오류|
|4011|Invalid Authorization Header|헤더 값 오류|
|4012|Invalid Session|세션 값 오류|
|4014|No Service term|약관 미등록 상태  <br>developers@hyundai.com에 문의하여 등록 요청해야 합니다.|
|4016|Unauthorized Client|서비스 인증 값 오류  <br>(adminKey 항목이 없거나 adminKey 이상)|
|4041|Unregistered Device|CCS 미가입 차량의 정보를 요청함  <br>(커넥티드서비스 미개통, 커넥티드서비스 해지, 커넥티드서비스 무료 기간 종료 후 유료 미전환)|
|4043|Unregistered User|CCS 미가입 고객의 정보를 요청함  <br>(입력된 생년월일 기준, 커넥티드서비스 계약자 정보 없음)|
|4045|No data|장기 미운행 차량, 단말 데이터 전송 오류 등으로 데이터 제공 불가|
|4046|No Registered Vehicles|차량 미보유 고객으로 데이터 제공 불가|
|4047|Agreement dose not exist|동의 이력이 없이 철회부터 진행 시 발생|
|4120|Pre-operation is required|선 호출 필요한 API를 호출하지 않은 경우 발생|
|5001|Internal Server Error|API 내부 에러|
|5003|Service Provider Error|연동 서비스 오류|
|5004|Internal Server Permission Error|API 내부 에러|
|5005|No Agreement Error|사용자가 정보 제공 미동의 상태로 데이터 제공 불가  <br>(커넥티드서비스 계약자가 제3자 제공 동의 '미동의')|
|5006|No Permission Error|API 호출 권한 없음|
|5007|Service not registered Error|등록된 서비스가 아닌 경우 발생|
|5008|Service not defined Error|서비스 정보 오류  <br>(맞지않는 서비스 ID)|
|5031|Unavailable remote control|차량 상태에 의해 원격제어가 불가능한 경우 발생|
|5032|Service Unavailable|데이터 조회 불가 차량으로 서비스 지원이 불가한 경우 발생|
|5041|Gateway Timeout|타임아웃 에러|
|9999|Undefined Error|API 내부 에러|

## Sample Test

CarID6d97337b-eb53-467b-baf4-7faec6d7065e3f979d64-1e57-4ead-90af-25da1756e206ce7dfc88-f6b3-41ad-9099-4eb57bce4944b23f1cd3-517c-4ac0-b574-cfc8eeca5fed10cc6538-82b5-48aa-9d85-16416b8e07fb

API 호출하기 초기화

## 데이터 API

### Lamp wire 경고등 상태 조회

[Sample Test](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/specification/data/statuswarning_lampwire#a)

Lamp wire 경고등 상태를 조회하는 API입니다.  
시동 종료, EV/PHEV 충전 종료 시점을 기준으로 업데이트됩니다.

![GET](https://img.shields.io/badge/method-GET-green.svg) ![PUBLIC](https://img.shields.io/badge/service-PUBLIC-blue.svg)

```
https://dev.kr-ccapi.hyundai.com/api/v1/car/status/warning/:carId/lampWire
```

### Headers

|Name|Type|Description|
|---|---|---|
|Authorization|string|Bearer {access_token}|
|Content-Type ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|string|MIMETYPE _Default value : application/json_|

### Parameters

|Name|Type|Description|
|---|---|---|
|carId|string|당사 발급 차량 고유 식별자|

### Success 200

|Name|Type|Description|
|---|---|---|
|status|boolean|Lamp wire 경고등 상태 (true : Lamp Wire ON / false : Lamp Wire OFF)|
|msgId|string|요청 결과 확인을 위한 메시지 ID|

### Success Response

Success Response (Example):

```
{
  "status": true,
  "msgId": "714dd6b9-af57-4c25-9630-0f0eef9175f9"
}
```

### Error 4xx

|Name|Type|Description|
|---|---|---|
|errCode|string|에러 코드|
|errMsg|string|에러에 대한 상세 설명|
|errId|string|에러 ID|

### Error Response

Error Response (Example):

```
{
  "errId": "123e4567-e89b-12d3-a456-426655440000",
  "errCode": "4002",
  "errMsg": "Invalid request body"
}
```

  

  

|에러 코드|에러 메시지|설명|
|---|---|---|
|4002|Invalid Request Body|호출 인자 값 오류|
|4011|Invalid Authorization Header|헤더 값 오류|
|4012|Invalid Session|세션 값 오류|
|4014|No Service term|약관 미등록 상태  <br>developers@hyundai.com에 문의하여 등록 요청해야 합니다.|
|4016|Unauthorized Client|서비스 인증 값 오류  <br>(adminKey 항목이 없거나 adminKey 이상)|
|4041|Unregistered Device|CCS 미가입 차량의 정보를 요청함  <br>(커넥티드서비스 미개통, 커넥티드서비스 해지, 커넥티드서비스 무료 기간 종료 후 유료 미전환)|
|4043|Unregistered User|CCS 미가입 고객의 정보를 요청함  <br>(입력된 생년월일 기준, 커넥티드서비스 계약자 정보 없음)|
|4045|No data|장기 미운행 차량, 단말 데이터 전송 오류 등으로 데이터 제공 불가|
|4046|No Registered Vehicles|차량 미보유 고객으로 데이터 제공 불가|
|4047|Agreement dose not exist|동의 이력이 없이 철회부터 진행 시 발생|
|4120|Pre-operation is required|선 호출 필요한 API를 호출하지 않은 경우 발생|
|5001|Internal Server Error|API 내부 에러|
|5003|Service Provider Error|연동 서비스 오류|
|5004|Internal Server Permission Error|API 내부 에러|
|5005|No Agreement Error|사용자가 정보 제공 미동의 상태로 데이터 제공 불가  <br>(커넥티드서비스 계약자가 제3자 제공 동의 '미동의')|
|5006|No Permission Error|API 호출 권한 없음|
|5007|Service not registered Error|등록된 서비스가 아닌 경우 발생|
|5008|Service not defined Error|서비스 정보 오류  <br>(맞지않는 서비스 ID)|
|5031|Unavailable remote control|차량 상태에 의해 원격제어가 불가능한 경우 발생|
|5032|Service Unavailable|데이터 조회 불가 차량으로 서비스 지원이 불가한 경우 발생|
|5041|Gateway Timeout|타임아웃 에러|
|9999|Undefined Error|API 내부 에러|

## Sample Test

CarID6d97337b-eb53-467b-baf4-7faec6d7065e3f979d64-1e57-4ead-90af-25da1756e206ce7dfc88-f6b3-41ad-9099-4eb57bce4944b23f1cd3-517c-4ac0-b574-cfc8eeca5fed10cc6538-82b5-48aa-9d85-16416b8e07fb

API 호출하기 초기화

## 데이터 API

### 스마트키 배터리 상태 조회

[Sample Test](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/specification/data/statuswarning_smartkeybattery#a)

스마트키 배터리 상태를 조회하는 API입니다.  
시동 종료, EV/PHEV 충전 종료 시점을 기준으로 업데이트됩니다.

![GET](https://img.shields.io/badge/method-GET-green.svg) ![PUBLIC](https://img.shields.io/badge/service-PUBLIC-blue.svg)

```
https://dev.kr-ccapi.hyundai.com/api/v1/car/status/warning/:carId/smartKeyBattery
```

### Headers

|Name|Type|Description|
|---|---|---|
|Authorization|string|Bearer {access_token}|
|Content-Type ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|string|MIMETYPE _Default value : application/json_|

### Parameters

|Name|Type|Description|
|---|---|---|
|carId|string|당사 발급 차량 고유 식별자|

### Success 200

|Name|Type|Description|
|---|---|---|
|status|boolean|스마트키 배터리 경고 상태 (true : warning voltage level / false : normal)|
|msgId|string|요청 결과 확인을 위한 메시지 ID|

### Success Response

Success Response (Example):

```
{
  "status": true,
  "msgId": "714dd6b9-af57-4c25-9630-0f0eef9175f9"
}
```

### Error 4xx

|Name|Type|Description|
|---|---|---|
|errCode|string|에러 코드|
|errMsg|string|에러에 대한 상세 설명|
|errId|string|에러 ID|

### Error Response

Error Response (Example):

```
{
  "errId": "123e4567-e89b-12d3-a456-426655440000",
  "errCode": "4002",
  "errMsg": "Invalid request body"
}
```

  

  

|에러 코드|에러 메시지|설명|
|---|---|---|
|4002|Invalid Request Body|호출 인자 값 오류|
|4011|Invalid Authorization Header|헤더 값 오류|
|4012|Invalid Session|세션 값 오류|
|4014|No Service term|약관 미등록 상태  <br>developers@hyundai.com에 문의하여 등록 요청해야 합니다.|
|4016|Unauthorized Client|서비스 인증 값 오류  <br>(adminKey 항목이 없거나 adminKey 이상)|
|4041|Unregistered Device|CCS 미가입 차량의 정보를 요청함  <br>(커넥티드서비스 미개통, 커넥티드서비스 해지, 커넥티드서비스 무료 기간 종료 후 유료 미전환)|
|4043|Unregistered User|CCS 미가입 고객의 정보를 요청함  <br>(입력된 생년월일 기준, 커넥티드서비스 계약자 정보 없음)|
|4045|No data|장기 미운행 차량, 단말 데이터 전송 오류 등으로 데이터 제공 불가|
|4046|No Registered Vehicles|차량 미보유 고객으로 데이터 제공 불가|
|4047|Agreement dose not exist|동의 이력이 없이 철회부터 진행 시 발생|
|4120|Pre-operation is required|선 호출 필요한 API를 호출하지 않은 경우 발생|
|5001|Internal Server Error|API 내부 에러|
|5003|Service Provider Error|연동 서비스 오류|
|5004|Internal Server Permission Error|API 내부 에러|
|5005|No Agreement Error|사용자가 정보 제공 미동의 상태로 데이터 제공 불가  <br>(커넥티드서비스 계약자가 제3자 제공 동의 '미동의')|
|5006|No Permission Error|API 호출 권한 없음|
|5007|Service not registered Error|등록된 서비스가 아닌 경우 발생|
|5008|Service not defined Error|서비스 정보 오류  <br>(맞지않는 서비스 ID)|
|5031|Unavailable remote control|차량 상태에 의해 원격제어가 불가능한 경우 발생|
|5032|Service Unavailable|데이터 조회 불가 차량으로 서비스 지원이 불가한 경우 발생|
|5041|Gateway Timeout|타임아웃 에러|
|9999|Undefined Error|API 내부 에러|

## Sample Test

CarID6d97337b-eb53-467b-baf4-7faec6d7065e3f979d64-1e57-4ead-90af-25da1756e206ce7dfc88-f6b3-41ad-9099-4eb57bce4944b23f1cd3-517c-4ac0-b574-cfc8eeca5fed10cc6538-82b5-48aa-9d85-16416b8e07fb

API 호출하기 초기화

## 데이터 API

### 워셔액 경고등 상태 조회

[Sample Test](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/specification/data/statuswarning_washerfluid#a)

워셔액 경고등 상태를 조회하는 API입니다.  
시동 종료, EV/PHEV 충전 종료 시점을 기준으로 업데이트됩니다.

![GET](https://img.shields.io/badge/method-GET-green.svg) ![PUBLIC](https://img.shields.io/badge/service-PUBLIC-blue.svg)

```
https://dev.kr-ccapi.hyundai.com/api/v1/car/status/warning/:carId/washerFluid
```

### Headers

|Name|Type|Description|
|---|---|---|
|Authorization|string|Bearer {access_token}|
|Content-Type ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|string|MIMETYPE _Default value : application/json_|

### Parameters

|Name|Type|Description|
|---|---|---|
|carId|string|당사 발급 차량 고유 식별자|

### Success 200

|Name|Type|Description|
|---|---|---|
|status|boolean|워셔액 경고등 상태 (true : on / false : off)|
|msgId|string|요청 결과 확인을 위한 메시지 ID|

### Success Response

Success Response (Example):

```
{
  "status": false,
  "msgId": "714dd6b9-af57-4c25-9630-0f0eef9175f9"
}
```

### Error 4xx

|Name|Type|Description|
|---|---|---|
|errCode|string|에러 코드|
|errMsg|string|에러에 대한 상세 설명|
|errId|string|에러 ID|

### Error Response

Error Response (Example):

```
{
  "errId": "123e4567-e89b-12d3-a456-426655440000",
  "errCode": "4002",
  "errMsg": "Invalid request body"
}
```

  

  

|에러 코드|에러 메시지|설명|
|---|---|---|
|4002|Invalid Request Body|호출 인자 값 오류|
|4011|Invalid Authorization Header|헤더 값 오류|
|4012|Invalid Session|세션 값 오류|
|4014|No Service term|약관 미등록 상태  <br>developers@hyundai.com에 문의하여 등록 요청해야 합니다.|
|4016|Unauthorized Client|서비스 인증 값 오류  <br>(adminKey 항목이 없거나 adminKey 이상)|
|4041|Unregistered Device|CCS 미가입 차량의 정보를 요청함  <br>(커넥티드서비스 미개통, 커넥티드서비스 해지, 커넥티드서비스 무료 기간 종료 후 유료 미전환)|
|4043|Unregistered User|CCS 미가입 고객의 정보를 요청함  <br>(입력된 생년월일 기준, 커넥티드서비스 계약자 정보 없음)|
|4045|No data|장기 미운행 차량, 단말 데이터 전송 오류 등으로 데이터 제공 불가|
|4046|No Registered Vehicles|차량 미보유 고객으로 데이터 제공 불가|
|4047|Agreement dose not exist|동의 이력이 없이 철회부터 진행 시 발생|
|4120|Pre-operation is required|선 호출 필요한 API를 호출하지 않은 경우 발생|
|5001|Internal Server Error|API 내부 에러|
|5003|Service Provider Error|연동 서비스 오류|
|5004|Internal Server Permission Error|API 내부 에러|
|5005|No Agreement Error|사용자가 정보 제공 미동의 상태로 데이터 제공 불가  <br>(커넥티드서비스 계약자가 제3자 제공 동의 '미동의')|
|5006|No Permission Error|API 호출 권한 없음|
|5007|Service not registered Error|등록된 서비스가 아닌 경우 발생|
|5008|Service not defined Error|서비스 정보 오류  <br>(맞지않는 서비스 ID)|
|5031|Unavailable remote control|차량 상태에 의해 원격제어가 불가능한 경우 발생|
|5032|Service Unavailable|데이터 조회 불가 차량으로 서비스 지원이 불가한 경우 발생|
|5041|Gateway Timeout|타임아웃 에러|
|9999|Undefined Error|API 내부 에러|

## Sample Test

CarID6d97337b-eb53-467b-baf4-7faec6d7065e3f979d64-1e57-4ead-90af-25da1756e206ce7dfc88-f6b3-41ad-9099-4eb57bce4944b23f1cd3-517c-4ac0-b574-cfc8eeca5fed10cc6538-82b5-48aa-9d85-16416b8e07fb

API 호출하기 초기화

## 데이터 API

### 브레이크 오일 경고등 상태 조회

[Sample Test](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/specification/data/statuswarning_breakoil#a)

브레이크 오일 경고등 상태를 조회하는 API입니다.  
시동 종료, EV/PHEV 충전 종료 시점을 기준으로 업데이트됩니다.

![GET](https://img.shields.io/badge/method-GET-green.svg) ![PUBLIC](https://img.shields.io/badge/service-PUBLIC-blue.svg)

```
  https://dev.kr-ccapi.hyundai.com/api/v1/car/status/warning/:carId/breakOil
```

### Headers

|Name|Type|Description|
|---|---|---|
|Authorization|string|Bearer {access_token}|
|Content-Type ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|string|MIMETYPE _Default value : application/json_|

### Parameters

|Name|Type|Description|
|---|---|---|
|carId|string|당사 발급 차량 고유 식별자|

### Success 200

|Name|Type|Description|
|---|---|---|
|status|boolean|브레이크 오일 경고등 상태 (true : on / false : off)|
|msgId|string|요청 결과 확인을 위한 메시지 ID|

### Success Response

Success Response (Example):

```
{
  "status": false,
  "msgId": "714dd6b9-af57-4c25-9630-0f0eef9175f9"
}
```

### Error 4xx

|Name|Type|Description|
|---|---|---|
|errCode|string|에러 코드|
|errMsg|string|에러에 대한 상세 설명|
|errId|string|에러 ID|

### Error Response

Error Response (Example):

```
{
  "errId": "123e4567-e89b-12d3-a456-426655440000",
  "errCode": "4002",
  "errMsg": "Invalid request body"
}
```

  

  

|에러 코드|에러 메시지|설명|
|---|---|---|
|4002|Invalid Request Body|호출 인자 값 오류|
|4011|Invalid Authorization Header|헤더 값 오류|
|4012|Invalid Session|세션 값 오류|
|4014|No Service term|약관 미등록 상태  <br>developers@hyundai.com에 문의하여 등록 요청해야 합니다.|
|4016|Unauthorized Client|서비스 인증 값 오류  <br>(adminKey 항목이 없거나 adminKey 이상)|
|4041|Unregistered Device|CCS 미가입 차량의 정보를 요청함  <br>(커넥티드서비스 미개통, 커넥티드서비스 해지, 커넥티드서비스 무료 기간 종료 후 유료 미전환)|
|4043|Unregistered User|CCS 미가입 고객의 정보를 요청함  <br>(입력된 생년월일 기준, 커넥티드서비스 계약자 정보 없음)|
|4045|No data|장기 미운행 차량, 단말 데이터 전송 오류 등으로 데이터 제공 불가|
|4046|No Registered Vehicles|차량 미보유 고객으로 데이터 제공 불가|
|4047|Agreement dose not exist|동의 이력이 없이 철회부터 진행 시 발생|
|4120|Pre-operation is required|선 호출 필요한 API를 호출하지 않은 경우 발생|
|5001|Internal Server Error|API 내부 에러|
|5003|Service Provider Error|연동 서비스 오류|
|5004|Internal Server Permission Error|API 내부 에러|
|5005|No Agreement Error|사용자가 정보 제공 미동의 상태로 데이터 제공 불가  <br>(커넥티드서비스 계약자가 제3자 제공 동의 '미동의')|
|5006|No Permission Error|API 호출 권한 없음|
|5007|Service not registered Error|등록된 서비스가 아닌 경우 발생|
|5008|Service not defined Error|서비스 정보 오류  <br>(맞지않는 서비스 ID)|
|5031|Unavailable remote control|차량 상태에 의해 원격제어가 불가능한 경우 발생|
|5032|Service Unavailable|데이터 조회 불가 차량으로 서비스 지원이 불가한 경우 발생|
|5041|Gateway Timeout|타임아웃 에러|
|9999|Undefined Error|API 내부 에러|

## Sample Test

CarID6d97337b-eb53-467b-baf4-7faec6d7065e3f979d64-1e57-4ead-90af-25da1756e206ce7dfc88-f6b3-41ad-9099-4eb57bce4944b23f1cd3-517c-4ac0-b574-cfc8eeca5fed10cc6538-82b5-48aa-9d85-16416b8e07fb

API 호출하기 초기화

## 데이터 API

### 엔진 오일 경고등 상태 조회

[Sample Test](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/specification/data/statuswarning_engineoil#a)

엔진 오일 경고등 상태를 조회하는 API입니다.  
시동 종료, EV/PHEV 충전 종료 시점을 기준으로 업데이트됩니다.

![GET](https://img.shields.io/badge/method-GET-green.svg) ![PUBLIC](https://img.shields.io/badge/service-PUBLIC-blue.svg)

```
https://dev.kr-ccapi.hyundai.com/api/v1/car/status/warning/:carId/engineOil
```

### Headers

|Name|Type|Description|
|---|---|---|
|Authorization|string|Bearer {access_token}|
|Content-Type ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|string|MIMETYPE _Default value : application/json_|

### Parameters

|Name|Type|Description|
|---|---|---|
|carId|string|당사 발급 차량 고유 식별자|

### Success 200

|Name|Type|Description|
|---|---|---|
|status|boolean|엔진 오일 경고등 상태 (true : on / false : off)|
|msgId|string|요청 결과 확인을 위한 메시지 ID|

### Success Response

Success Response (Example):

```
{
  "status": false,
  "msgId": "714dd6b9-af57-4c25-9630-0f0eef9175f9"
}
```

### Error 4xx

|Name|Type|Description|
|---|---|---|
|errCode|string|에러 코드|
|errMsg|string|에러에 대한 상세 설명|
|errId|string|에러 ID|

### Error Response

Error Response (Example):

```
{
  "errId": "123e4567-e89b-12d3-a456-426655440000",
  "errCode": "4002",
  "errMsg": "Invalid request body"
}
```

  

  

|에러 코드|에러 메시지|설명|
|---|---|---|
|4002|Invalid Request Body|호출 인자 값 오류|
|4011|Invalid Authorization Header|헤더 값 오류|
|4012|Invalid Session|세션 값 오류|
|4014|No Service term|약관 미등록 상태  <br>developers@hyundai.com에 문의하여 등록 요청해야 합니다.|
|4016|Unauthorized Client|서비스 인증 값 오류  <br>(adminKey 항목이 없거나 adminKey 이상)|
|4041|Unregistered Device|CCS 미가입 차량의 정보를 요청함  <br>(커넥티드서비스 미개통, 커넥티드서비스 해지, 커넥티드서비스 무료 기간 종료 후 유료 미전환)|
|4043|Unregistered User|CCS 미가입 고객의 정보를 요청함  <br>(입력된 생년월일 기준, 커넥티드서비스 계약자 정보 없음)|
|4045|No data|장기 미운행 차량, 단말 데이터 전송 오류 등으로 데이터 제공 불가|
|4046|No Registered Vehicles|차량 미보유 고객으로 데이터 제공 불가|
|4047|Agreement dose not exist|동의 이력이 없이 철회부터 진행 시 발생|
|4120|Pre-operation is required|선 호출 필요한 API를 호출하지 않은 경우 발생|
|5001|Internal Server Error|API 내부 에러|
|5003|Service Provider Error|연동 서비스 오류|
|5004|Internal Server Permission Error|API 내부 에러|
|5005|No Agreement Error|사용자가 정보 제공 미동의 상태로 데이터 제공 불가  <br>(커넥티드서비스 계약자가 제3자 제공 동의 '미동의')|
|5006|No Permission Error|API 호출 권한 없음|
|5007|Service not registered Error|등록된 서비스가 아닌 경우 발생|
|5008|Service not defined Error|서비스 정보 오류  <br>(맞지않는 서비스 ID)|
|5031|Unavailable remote control|차량 상태에 의해 원격제어가 불가능한 경우 발생|
|5032|Service Unavailable|데이터 조회 불가 차량으로 서비스 지원이 불가한 경우 발생|
|5041|Gateway Timeout|타임아웃 에러|
|9999|Undefined Error|API 내부 에러|

## Sample Test

CarID6d97337b-eb53-467b-baf4-7faec6d7065e3f979d64-1e57-4ead-90af-25da1756e206ce7dfc88-f6b3-41ad-9099-4eb57bce4944b23f1cd3-517c-4ac0-b574-cfc8eeca5fed10cc6538-82b5-48aa-9d85-16416b8e07fb

API 호출하기 초기화

## 데이터 API

### 데이터 조회 불가 상태 알림

커넥티드 서비스 해지, 차량 삭제, 제3자 제공 동의 철회 등 고객 요청에 의해 데이터를 더 이상 제공할 수 없는 경우, 이 정보를 전달받기 위한 규격입니다.  
Callback URL은 '설정 - 데이터 API' 페이지에서 등록 가능합니다.  
개인정보보호법 및 개인정보보호법시행령에 따라 해당 알림을 받은 즉시, API를 통해 제공된 데이터를 일괄 삭제하고 서비스에서 지속 표출되지 않도록 조치해야 합니다.

![POST](https://img.shields.io/badge/method-POST-blue.svg) ![PUBLIC](https://img.shields.io/badge/service-PUBLIC-blue.svg)

```
https://callback_url
```

### Success 200

|Name|Type|Description|
|---|---|---|
|type|string|알림 대상  <br>(account, vehicle, agreement)|
|action|string|callback event  <br>(delete, reject)|
|userId ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|string|당사 발급 사용자 고유 식별자|
|carId ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|string|당사 발급 차량 고유 식별자|
|vin ![OPTIONAL](https://img.shields.io/badge/optional-lightgrey.svg)|string|VIN(차대번호)  <br>VIN(차대번호) 데이터 접근 권한이 있는 서비스에 한하여 제공|

### Success Response

Success Response (계정 삭제):

```
{
  "type": "account",
  "action": "delete",
  "userId": "11e77efa-aff0-4b3c-a5a0-c4cde4674963",
}
```

  

Success Response (차량 삭제):

```
{
  "type": "vehicle",
  "action": "delete",
  "carId": "22e77efa-aff0-4b3c-a5a0-c4cde4674963"
}
```

  

Success Response (차량 삭제, VIN(차대번호) 접근 가능 서비스):

```
{
  "type": "vehicle",
  "action": "delete",
  "carId": "22e77efa-aff0-4b3c-a5a0-c4cde4674963",
  "vin": "KNAF000BEKA000000"
}
```

  

Success Response (제3자 제공 동의 철회):

```
{
  "type": "agreement",
  "action": "reject",
  "carId": "22e77efa-aff0-4b3c-a5a0-c4cde4674963"
}
```

  

Success Response (제3자 제공 동의 철회, VIN(차대번호) 접근 가능 서비스):

```
{
  "type": "agreement",
  "action": "reject",
  "carId": "22e77efa-aff0-4b3c-a5a0-c4cde4674963",
  "vin": "KNAF000BEKA000000"
}
```

  

  

|에러 코드|에러 메시지|설명|
|---|---|---|
|4002|Invalid Request Body|호출 인자 값 오류|
|4011|Invalid Authorization Header|헤더 값 오류|
|4012|Invalid Session|세션 값 오류|
|4014|No Service term|약관 미등록 상태  <br>developers@hyundai.com에 문의하여 등록 요청해야 합니다.|
|4016|Unauthorized Client|서비스 인증 값 오류  <br>(adminKey 항목이 없거나 adminKey 이상)|
|4041|Unregistered Device|CCS 미가입 차량의 정보를 요청함  <br>(커넥티드서비스 미개통, 커넥티드서비스 해지, 커넥티드서비스 무료 기간 종료 후 유료 미전환)|
|4043|Unregistered User|CCS 미가입 고객의 정보를 요청함  <br>(입력된 생년월일 기준, 커넥티드서비스 계약자 정보 없음)|
|4045|No data|장기 미운행 차량, 단말 데이터 전송 오류 등으로 데이터 제공 불가|
|4046|No Registered Vehicles|차량 미보유 고객으로 데이터 제공 불가|
|4047|Agreement dose not exist|동의 이력이 없이 철회부터 진행 시 발생|
|4120|Pre-operation is required|선 호출 필요한 API를 호출하지 않은 경우 발생|
|5001|Internal Server Error|API 내부 에러|
|5003|Service Provider Error|연동 서비스 오류|
|5004|Internal Server Permission Error|API 내부 에러|
|5005|No Agreement Error|사용자가 정보 제공 미동의 상태로 데이터 제공 불가  <br>(커넥티드서비스 계약자가 제3자 제공 동의 '미동의')|
|5006|No Permission Error|API 호출 권한 없음|
|5007|Service not registered Error|등록된 서비스가 아닌 경우 발생|
|5008|Service not defined Error|서비스 정보 오류  <br>(맞지않는 서비스 ID)|
|5031|Unavailable remote control|차량 상태에 의해 원격제어가 불가능한 경우 발생|
|5032|Service Unavailable|데이터 조회 불가 차량으로 서비스 지원이 불가한 경우 발생|
|5041|Gateway Timeout|타임아웃 에러|
|9999|Undefined Error|API 내부 에러|

## 설정

### 계정 API

|   |   |
|---|---|
|*Redirect URL|[저장](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/project_setting#)<br><br>개인정보 제공 동의 요청 API를 호출시, 제3자 제공 동의 페이지에서 고객이 동의를 완료하면 리턴 값 (Authorization Code)을 전달받기 위해 설정하는 URL 입니다.|

### 데이터 API

|   |   |
|---|---|
|*Redirect URL|[저장](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/project_setting#)<br><br>개인정보 제공 동의 요청 API 호출을 통해 연결된 제3자 제공 동의 페이지에서 사용자가 동의 완료하는 경우, 리턴 값을 받기 위해 설정하는 URL입니다.|
|*Callback URL|[저장](https://console.developers.hyundai.com/web/v1/project/detail/1743/prod/project_setting#)<br><br>커넥티드 서비스 해지, 차량 삭제, 제3자 제공 동의 철회 등 고객 요청에 의해 데이터를 더 이상 제공할 수 없는 경우, 이 정보를 전달받기 위해 설정하는 URL입니다.  <br>Port는 80, 443, 8080, 8443 권장합니다. 그 외 Port 번호 사용시 Callback 기능 사용에 제한이 있을 수 있습니다.|
## 내 차량 등록

내 차량 등록을 통해 본인이 CCS (커넥티드카 서비스) 계약자로 등록된 차량을 연동하여 테스트가 가능합니다.

본인이 CCS 계약자로 등록된 차량에 한하여 차량정보가 화면에 나타납니다.

연동을 원하는 차량을 활성화 한 뒤, 계정연동 및 서비스 이용 동의를 거쳐 해당 차량의 실제 데이터를 조회할 수 있습니다.

문의사항은 "기술지원요청" 메뉴를 통해 문의해주세요.

### 내 차량 등록

|No.|차량 모델명|개통 날짜|VIN|제공가능 API 정보|활성여부|
|---|---|---|---|---|---|
|1|Avante|2026.05.20|KMHLM41EERU806563|API 목록 보기|해제|