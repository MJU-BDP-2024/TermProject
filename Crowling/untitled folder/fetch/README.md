# 데이터 가져오기

## get_price.ipynb
### 셋업
#### `MAX_FETCH_COUNT`
- 매물 리스트 조회 횟수 조절
- `count` `1` 당 `250` 개의 매물 `id` 와 `price` 데이터를 가져옴
- 대략 `650` 정도 값이면 국산차 매물 데이터를 전부 가져올 수 있음
#### `OUTPUT_FILE_PATH`
- 파일 저장 경로를 설정
### 출력형식
```
id,price
38001407,999
38439771,4390
38483118,3470
38174011,5330
38257876,2190
```

## get_history.ipynb
### 셋업
#### `MAX_FETCH_COUNT`
- 보험이력 조회 횟수 조절
#### `INPUT_FILE_PATH`
- 매물 `id` 가 있는 `csv` 파일의 경로를 설정
#### `OUTPUT_FILE_PATH`
- 파일 저장 경로를 설정
### 출력형식
```
id,license,model,fuel,cc,registration_date,license_changed,owner_changed,total_loss,flood,theft,damaged_count,damaged_total,damaged_by_other_count,damaged_by_other_total
38001407,51로6542,그랜저 HG,가솔린,2999cc,2013/01/02,0,6,0,0,0,5,2161516,2,803470
38439771,162오1504,GV70,가솔린,2497cc,2022/12/14,0,1,0,0,0,1,1845420,0,0
38483118,334머3931,카니발 4세대,디젤,2151cc,2020/11/10,0,0,0,0,0,0,0,0,0
38207612,39더7577,코나,디젤,1582cc,2017/10/16,0,2,0,0,0,1,1044710,2,2862740
38275179,126라9549,올 뉴 투싼,가솔린,1591cc,2020/04/06,1,0,0,0,0,1,1634410,0,0
```

## get_status.ipynb
### 셋업
#### `MAX_FETCH_COUNT`
- 성능기록부 조회 횟수 조절
#### `INPUT_FILE_PATH`
- 매물 `id` 가 있는 `csv` 파일의 경로를 설정
#### `OUTPUT_FILE_PATH`
- 파일 저장 경로를 설정
### 출력형식
```
id,transmission,warranty,mileage,tuning_history,special_history,usage_change,accident,little_accident
38273842,수동,보험사보증,"87,115km",없음,없음,없음,없음,없음
37547281,-,보험사보증,"86,252km",없음,없음,없음,없음,없음
38599785,-,보험사보증,"319,323km",없음,없음,없음,없음,있음
38274834,-,보험사보증,"33,161km",없음,없음,있음 / 렌트,없음,없음
38478303,-,보험사보증,"11,798km",없음,없음,없음,없음,없음
```
