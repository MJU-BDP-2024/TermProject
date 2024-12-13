#강건희 60192328 코드 1 _ join 코드

# 2024 년 12월 5일 커밋내용 csv 파일 pyspark에서 조인하기

#UnicodeEncodeError: 'ascii' codec can't encode 가 계속 생기는데 아래 코드 사용해서 바꿔줘야함
#터미널에서 Python 인코딩 설정
export PYTHONIOENCODING=utf8

##PySpark에 Python 3.6 설정 
export PYSPARK_PYTHON=/usr/bin/python3.6
export PYSPARK_DRIVER_PYTHON=/usr/bin/python3.6



# pyspark 열어서 csv 파일받기
historys = spark.read.csv("vehicles_history.csv", header="true",sep=",", inferSchema="true")

prices = spark.read.csv("vehicles_price.csv", header="true",sep=",", inferSchema="true")

status = spark.read.csv("vehicles_status", header="true",sep=",", inferSchema="true")

df = spark.read.csv("vehicles_data/vehicles_data.csv", header="true",sep=",", inferSchema="true")


#join 하게 될때 csv 파일모두 "id"라는 컬럼이 있으면 오류날 수 있음!! 
prices = prices.withColumnRenamed("id", "price_id")
status = status.withColumnRenamed("id", "status_id")

#조인 코드
historys_prices=historys.join(prices,historys["id"] == prices["price_id"],"inner")

vehicles_data=historys_prices.join(status,historys_prices["id"] == status["status_id"],"inner")


# vehicles_data에서 10,000개의 데이터만 추출

vehicles_data_sample = vehicles_data.limit(10000)

#필요없는 컬럼 삭제
vehicles_data = vehicles_data.drop("status_id", "price_id")

#이거는 pysprak에서 만든 데이터를 hdfs로 보내는 코드
vehicles_data.write.csv("/user/maria_dev/vehicles_data", header=True)

vehicles_data_sample.write.csv("/user/maria_dev/vehicles_data_sample", header=True)

df.write.csv("/user/maria_dev/vehicles_data_preprocessing1", header=True)

---------------------------------
git fetch chore/csv-upload