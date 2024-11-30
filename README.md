kbcchacha.com -> 중고차 데이터 크롤링 -> csv 파일 저장

※ 보험정보 / 성능점검 / 차량번호 등을 조회하기 위해 url "https://www.kbchachacha.com/public/car/detail.kbc?carSeq="에

str(page)를 더하는 방식으로 페이지 로드했으나 연결 거부 (보안 이유로 막아놓은 듯 함)

encar.com 혹은 다른 중고차 매매 사이트에서 시도해봐도 결과는 동일하다.

추출가능 데이터 => (사이트 내 차량등록번호, 모델명, 사양, 가격, 주행거리) 로 car_data.csv 파일에 pandas 활용한 csv 파일로 저장함.
