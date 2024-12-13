from datetime import datetime
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import RandomForestRegressor
from pyspark.sql import SparkSession, Window
from pyspark.sql.functions import regexp_extract, mean, stddev, col, abs, regexp_replace, log1p, exp, to_date, datediff, lit, when

# SparkSession 생성
spark = SparkSession.builder \
    .appName("VehiclesModel") \
    .enableHiveSupport() \
    .getOrCreate()

df = spark.sql("SELECT * FROM vehicles")

#------------------------------------------------<전처리 1 모델별 price outlier 제거>
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
df = df.drop("flood") 
df = df.drop("license")
df = df.drop("theft")
df = df.drop("id")
df = df.drop("warranty")

#------------------------------------------------<전처리 3 [ 0, 1 ]라벨 인코딩 제거>
# little_accident 전처리 -> 없음 = 0 , 있음 = 1
# accident 전처리 -> 없음 = 0 , 있음 = 1
# usage_change 전처리 -> 없음 = 0 , 있음 = 1
# special_history 전처리 -> 없음 = 0 , 있음 = 1
# tuning_history 전처리 -> 없음 = 0 , 있음 = 1
# transmission의 "-" => 0 , 수동 => 1 , 나머지도 => 0
df = df.withColumn("little_accident", when(df.little_accident == "없음", 0).otherwise(1))
df = df.withColumn("accident", when(df.accident == "없음", 0).otherwise(1))
df = df.withColumn("usage_change", when(df.usage_change == "없음", 0).otherwise(1))
df = df.withColumn("special_history", when(df.special_history == "없음", 0).otherwise(1))
df = df.withColumn("tuning_history", when(df.tuning_history == "없음", 0).otherwise(1))
df = df.withColumn("manual_transmission", when(col("transmission") == "수동", 1).otherwise(0))
df = df.drop("transmission")

#------------------------------------------------<전처리 4 사고이력 하나로 합친다>
# 예시) damaged_count <= damaged_count + damaged_by_other_count
# 두 컬럼을 더하여 새로운 컬럼 "total_damage_count" 생성
df = df.withColumn("damaged_count", col("damaged_count") + col("damaged_by_other_count"))

# 필요없어진 damage_by_other_count 삭제
df = df.drop("damage_by_other_count") 

# 두 컬럼을 더하여 새로운 컬럼 "total_damage_count" 생성
df = df.withColumn("damaged_total", col("damaged_total") + col("damaged_by_other_total"))

# 필요없어진 damaged_total ,  damaged_by_other_total
df = df.drop("damaged_by_other_total") 

#------------------------------------------------<전처리  5 mileage, cc 전처리>
#mileage 에서 숫자만 추출 , cc 전처리
df = df.withColumn("mileage", regexp_extract(col("mileage"), r"(\d[\d,]*)", 1))
df = df.withColumn("cc", regexp_replace("cc", "cc", ""))  # cc 컬럼에서 "cc" 제거
df = df.withColumn("mileage", regexp_replace("mileage", ",", ""))
df = df.withColumn("cc", col("cc").cast("int"))
df = df.withColumn("mileage", col("mileage").cast("int"))

#------------------------------------------------<전처리  6 날씨처리 >
today = datetime.today().strftime("%Y-%m-%d")
df = df.withColumn("registration_date", to_date(col("registration_date"), "yyyy/MM/dd"))
df = df.withColumn("car_age", datediff(lit(today), col("registration_date")) / 365.25)
df = df.drop("registration_date")

df = df.filter(col("price") >= 200)

# #------------------------------------------------<전처리  7 큰 숫자 로그 처리 >
# # 1. log1p를 모든 컬럼에 적용
# columns = ['owner_changed', 'damaged_count', 'damaged_total', 'mileage', 'car_age']
# for column in columns:
#     df = df.withColumn(column, log1p(col(column)))

# # 2. mileage에 비선형 변환 적용
# df = df.withColumn("mileage", -exp(-col("mileage") / 100000) + 1)

# columns = ['owner_changed', 'damaged_count', 'damaged_total', 'mileage', 'car_age']
# select_df=df.select('owner_changed', 'damaged_count', 'damaged_total', 'mileage', 'car_age')
# select_df.show()

#------------------------------------------------<모 델 학 습 >
# 1. '그랜저 IG' 데이터 필터링
grandeur_data = df.filter(col("model") == "그랜저 IG 하이브리드")

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

# 4. Random Forest 모델 학습
rf = RandomForestRegressor(featuresCol="features", labelCol="label", numTrees=100, maxDepth=10)
model = rf.fit(train_data)

# 5. 예측
predictions = model.transform(test_data)

# 6. 평가
evaluator = RegressionEvaluator(labelCol="label", predictionCol="prediction", metricName="rmse")
rmse = evaluator.evaluate(predictions)

# MSE 계산 (optional)
mse = evaluator.evaluate(predictions, {evaluator.metricName: "mse"})

# 결과 출력
print(f"RMSE: {rmse}")
print(f"MSE: {mse}")
# 예측 값과 실제 값 확인
predictions.select("prediction", "label").show()

#예측값과 실제 값 확인

