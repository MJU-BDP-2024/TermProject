# 자동차 가격 예측 모델
## 실행 방법
### 터미널에서 `bash run_insert.sh` 실행
`csv` 파일이 `hadoop` 환경에 있어야 하고, `csv` 파일 `3`개를 `join`해서 `hive database`에 저장한다.
### 터미널에서 `bash run_model.sh` 실행
`hive database`에 있는 데이터를 받아와서 가격 예측 `RandomForestClassifier` 모델을 생성한다.
### Hadoop 환경에서 작업
