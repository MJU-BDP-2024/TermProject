from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("vehicles") \
    .enableHiveSupport() \
    .getOrCreate()

df = spark.read.csv("vehicles_price.csv", header="true", sep=",", inferSchema="true")
historys = spark.read.csv("vehicles_history.csv", header="true", sep=",", inferSchema="true")
status = spark.read.csv("vehicles_status.csv", header="true", sep=",", inferSchema="true")

df = df.join(historys, on = 'id', how = 'inner')
df = df.join(status, on = 'id', how = 'inner')

# Save data into database table as 'vehicles'
df.write.saveAsTable("vehicles", mode="overwrite")
