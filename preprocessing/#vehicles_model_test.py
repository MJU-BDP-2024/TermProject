#초기 버전 
# 파일 받기
historys = spark.read.csv("vehicles_history.csv", header="true",sep=",", inferSchema="true")

prices = spark.read.csv("vehicles_price.csv", header="true",sep=",", inferSchema="true")

status = spark.read.csv("vehicles_status.csv", header="true",sep=",", inferSchema="true")

#join 하게 될때 csv 파일모두 "id"라는 컬럼이 있으면 오류날 수 있음!! 
prices = prices.withColumnRenamed("id", "price_id")
status = status.withColumnRenamed("id", "status_id")

#조인 코드
historys_prices=historys.join(prices,historys["id"] == prices["price_id"],"inner")

df=historys_prices.join(status,historys_prices["id"] == status["status_id"],"inner")

#필요없는 컬럼 삭제
df = df.drop("status_id", "price_id")

#------------------------------------------------<전처리 1 모델별 price outlier 제거>
from pyspark.sql import Window
from pyspark.sql.functions import mean, stddev, col, abs
from pyspark.sql.functions import regexp_replace
from pyspark.sql.functions import col, log1p, exp
# 1. 모델별 평균 및 표준편차 계산
window_spec = Window.partitionBy("model")

# 평균 및 표준편차 추가
df = df.withColumn("mean_price", mean(col("price")).over(window_spec))
df = df.withColumn("stddev_price", stddev(col("price")).over(window_spec))

# 2. z-score 계산
df = df.withColumn("z_score", (col("price") - col("mean_price")) / col("stddev_price"))

# 3. z-score 기준으로 이상치 필터링 (-3 <= z_score <= 3)
df = df.filter((col("z_score") > -3) & (col("z_score") < 3))

# 4. 불필요한 컬럼 삭제
df = df.drop("mean_price", "stddev_price", "z_score")

#------------------------------------------------<전처리 2 불필요한 컬럼 제거>
df = df.drop("license_changed")
df = df.drop("license")
df = df.drop("theft")
df = df.drop("id")
df = df.drop("warranty")

#------------------------------------------------<전처리 3 [ 0, 1 ]라벨 인코딩 제거>
#little_accident ,accident ,usage_change ,special_history , tuning_history
#little_accident 전처리 -> 없음 = 0 , 있음 = 1
from pyspark.sql.functions import when
df = df.withColumn("little_accident", when(df.little_accident == "없음", 0).otherwise(1))

#accident 전처리 -> 없음 = 0 , 있음 = 1
df = df.withColumn("accident", when(df.accident == "없음", 0).otherwise(1))

#usage_change 전처리 -> 없음 = 0 , 있음 = 1
df = df.withColumn("usage_change", when(df.usage_change == "없음", 0).otherwise(1))

#special_history 전처리 -> 없음 = 0 , 있음 = 1
df = df.withColumn("special_history", when(df.special_history == "없음", 0).otherwise(1))

#tuning_history 전처리 -> 없음 = 0 , 있음 = 1
df = df.withColumn("tuning_history", when(df.tuning_history == "없음", 0).otherwise(1))

#위 5컬럼은 데이터 중 "없음"이 90%를 차지한다. 

#+ transmission의 "-" => 0 , 수동 => 1 , 나머지도 => 0
df = df.withColumn("manual_transmission", when(col("transmission") == "수동", 1).otherwise(0))
df = df.drop("transmission")

#------------------------------------------------<전처리 4 사고이력 하나로 합친다>
# 예시) damaged_count <= damaged_count + damaged_by_other_count

## 두 컬럼을 더하여 새로운 컬럼 "total_damage_count" 생성

df = df.withColumn("damaged_count", col("damaged_count") + col("damaged_by_other_count"))

# 결과 확인
df.select("damaged_count", "damaged_by_other_count").show()

#필요없어진 damage_by_other_count 삭제
df = df.drop("damage_by_other_count") 


## 두 컬럼을 더하여 새로운 컬럼 "total_damage_count" 생성
df = df.withColumn("damaged_total", col("damaged_total") + col("damaged_by_other_total"))
df.select("damaged_total", "damaged_by_other_total").show()

# 필요없어진 damaged_total ,  damaged_by_other_total
df = df.drop("damaged_by_other_total") 

#------------------------------------------------<전처리  5 mileage, cc 전처리>
#mileage 에서 숫자만 추출 , cc 전처리
from pyspark.sql.functions import regexp_extract
df = df.withColumn("mileage", regexp_extract(col("mileage"), r"(\d[\d,]*)", 1))
df = df.withColumn("cc", regexp_replace("cc", "cc", ""))  # cc 컬럼에서 "cc" 제거
df = df.withColumn("mileage", regexp_replace("mileage", ",", ""))
df = df.withColumn("cc", col("cc").cast("int"))
df = df.withColumn("mileage", col("mileage").cast("int"))

#------------------------------------------------<전처리  6 날씨처리 >

from pyspark.sql.functions import to_date, datediff, lit
from datetime import datetime
today = datetime.today().strftime("%Y-%m-%d")
df = df.withColumn("registration_date", to_date(col("registration_date"), "yyyy/MM/dd"))
df = df.withColumn("car_age", datediff(lit(today), col("registration_date")) / 365.25)
df = df.drop("registration_date")


select_df=df.select("little_accident","accident","tuning_history","special_history","usage_change","manual_transmission","mileage","cc")
select_df.show()

#------------------------------------------------<전처리  7 큰 숫자 로그 처리 >

# 1. log1p를 모든 컬럼에 적용
columns = ['owner_changed', 'damaged_count', 'damaged_total', 'mileage', 'car_age']
for column in columns:
    df = df.withColumn(column, log1p(col(column)))

# 2. mileage에 비선형 변환 적용
df = df.withColumn("mileage", -exp(-col("mileage") / 100000) + 1)

columns = ['owner_changed', 'damaged_count', 'damaged_total', 'mileage', 'car_age']
select_df=df.select('owner_changed', 'damaged_count', 'damaged_total', 'mileage', 'car_age')
select_df.show()


#------------------------------------------------<모 델 학 습 >
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import LinearRegression
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.sql.functions import col
# 1. '그랜저 IG' 데이터 필터링
grandeur_data = df.filter(col("model") == "그랜저 IG")

# 2. 독립 변수와 종속 변수 분리
# 사용할 컬럼 정의
feature_columns = [col for col in df.columns if col not in ['model', 'fuel', 'cc', 'price', 'owner_changed']]

# VectorAssembler로 독립 변수를 하나의 벡터로 변환
assembler = VectorAssembler(inputCols=feature_columns, outputCol="features")
grandeur_data = assembler.transform(grandeur_data)

# 종속 변수(price)와 독립 변수(features)만 선택
grandeur_data = grandeur_data.select("features", col("price").alias("label"))

# 3. 데이터 분리 (train-test split)
train_data, test_data = grandeur_data.randomSplit([0.8, 0.2], seed=42)

# 4. Linear Regression 모델 학습
lr = LinearRegression(featuresCol="features", labelCol="label")
model = lr.fit(train_data)

# 5. 예측
predictions = model.transform(test_data)

# 6. 평가
evaluator = RegressionEvaluator(labelCol="label", predictionCol="prediction", metricName="rmse")
rmse = evaluator.evaluate(predictions)

# MSE 계산 (optional)
mse = evaluator.evaluate(predictions, {evaluator.metricName: "mse"})

# 결과 출력
print(f"Mean Squared Error (MSE): {mse}")
print(f"Root Mean Squared Error (RMSE): {rmse}")

# 예측 값과 실제 값 확인
predictions.select("prediction", "label").show()