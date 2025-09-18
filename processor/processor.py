from pyspark.sql import SparkSession
from db.connect import get_redis_conn
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType
import os


def write_to_redis(batch_df, batch_id):
    def write_partition(partition):
        rdb = get_redis_conn()
        for row in partition:
            rdb.rpush("raw_data", row.value)
        rdb.close()

    # partition the dataframe to avoid
    # processing the entire dataframe at once since it could overwhelm the memory used by the driver(processor.py) code
    # each partition is handled by a task, which Spark runs in a thread inside an executor (jvm process created by the cluster manager (eg. kubernetes in test/prod or a local built in manager for dev testing) to manage partitions and perform other data processing operations)
    # a connection to redis is opened for each thread (which manages a single partition)
    # and the partitioned data is appended to the redis list
    batch_df.foreachPartition(write_partition)


def write_login_counts_to_redis(batch_df, batch_id):
    def write_partition(partition):
        rdb = get_redis_conn()
        for row in partition:
            # increment Redis counter atomically
            rdb.hset("metrics", "login", row.ct)
        rdb.close()

    batch_df.foreachPartition(write_partition)


def main():
    # retrieve the list of jars to be used by spark
    # to connect to a kafka broker and stream data from it
    jars = ",".join([f"./jars/{jar}" for jar in os.listdir("./jars")])

    ## create the spark session
    # allow security manager to avoid xception in thread "main" java.lang.UnsupportedOperationException: getSubject is supported only if a security manager is allowed
    # add spark.jars.packages config to ensure that data can be streamed from a kafka broker
    spark = (
        SparkSession.builder.config(
            "spark.driver.extraJavaOptions", "-Djava.security.manager=allow"
        )
        .config("spark.executor.extraJavaOptions", "-Djava.security.manager=allow")
        # use spark.jars.packages for local testing
        # spark-submit to be used when testing in a kubernetes cluster
        # .config(
        #    "spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.13:4.0.0"
        # )
        # use when running spark driver + worker + master in the same pod
        .config("spark.jars", jars)
        .appName("KafkaStructuredStreaming")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    ###

    # create a dataframe which will hold the contents
    # retrieved from the kafka broker running on localhost:9092/os.environ["KAFKA_BROKER"]
    # after subscribing to the metrics topic
    kafka_broker = (
        "localhost:9092"
        if "KAFKA_BROKER" not in os.environ
        else os.environ["KAFKA_BROKER"]
    )
    df = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", kafka_broker)
        .option("subscribe", "metrics")
        # .option("startingOffsets", "earliest")  # Read existing messages
        .load()
    )

    processed_df = df.selectExpr("CAST(value AS STRING)")

    # Define schema of incoming messages (will be used to compute the count of a particular action)
    schema = StructType().add("user", StringType()).add("action", StringType())
    # Parse JSON
    # the "value" column contains a json in the form {"userId": <guid>, "action": "login", "timestamp": <iso formatted time>}
    # from_json(col("value"), schema) parses the "value" column into a MapType corresponding to the types specified in the schema
    # and returns a column corresponding to the parsed data
    # the returned column is renamed as "data" (alias)
    # and another select is run to return a data frame containing all the contents in the data column
    json_df = processed_df.select(from_json(col("value"), schema).alias("data")).select(
        "data.*"
    )
    ###

    ## query the processed data frame and display the results to the console
    # query = (
    #     processed_df.writeStream.format("console")
    #     .outputMode("append")  # or "complete", "update"
    #     .option("truncate", False)  # To display full content of messages
    #     .start()
    # )

    ##  write query results to redis for each batch of raw data retrieved from the kafka message broker
    # set checkpointLocation to match the mount path specified in the processor.yaml manifest
    # this allows the processor to persist checkpoint data (in simple terms it tells the processor from where to resume streaming data from the kafka broker)
    # to disk so that
    # if the pod restarts, it can resume processing from the last checkpoint
    query = (
        processed_df.writeStream.foreachBatch(write_to_redis)
        .option("checkpointLocation", "/checkpoint/raw-data")
        .start()
    )

    # count a specific action (in this case login)
    login_counts = (
        json_df.filter(col("action") == "login")
        .groupBy()  # global aggregation
        .count()  # count per micro-batch
        .withColumnRenamed("count", "ct")
    )

    # # Run login count query to update the login counts
    # set checkpointLocation in a similar manner as above
    login_query = (
        login_counts.writeStream.outputMode("complete")
        .foreachBatch(write_login_counts_to_redis)
        .option("checkpointLocation", "/checkpoint/metrics")
        .start()
    )

    # Keep the streaming query running to pull updates from the kafka message broker
    query.awaitTermination()
    login_query.awaitTermination()


main()
