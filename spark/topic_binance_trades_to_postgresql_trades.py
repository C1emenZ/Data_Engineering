# Benötigte Bibliotheken importieren - müssen im Dockerfile installiert werden
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, LongType, StringType, BooleanType

from dotenv import load_dotenv

import time
import os
from kafka import KafkaAdminClient
from kafka.errors import NoBrokersAvailable, KafkaError
import sys


# .env-Datei laden - Environment-Variablen initialisieren
load_dotenv()

# Parameter für Kafka Verbindungstest
BOOTSTRAP_SERVERS = "kafka:29092"
TOPIC_NAME = "binance.trades"
MAX_RETRIES = 10
SLEEP_INTERVAL = 3  


# Methode zum Schreiben in PostgreSQL-Datenbank
# DB-User,DB-Password und DB-Name werden aus .env-Datei geladen und müssen dort gesetzt werden
# Dieser Stream wird in die Tabelle trades geschrieben
def write_to_postgres(postgresql_df, epoch_id):
     postgresql_df.write \
         .format("jdbc") \
        .option("url", "jdbc:postgresql://postgres:5432/" + os.getenv('POSTGRESQL_DB')) \
         .option("dbtable", "trades") \
         .option("user", os.getenv('POSTGRESQL_USER')) \
         .option("password", os.getenv('POSTGRESQL_PASSWORD')) \
         .option("driver", "org.postgresql.Driver") \
         .mode("append") \
         .save()     


# Methode zum Testen, ob Kafka Topic erreichbar ist
def wait_for_kafka_topic():
    for attempt in range(MAX_RETRIES):
        try:
            admin = KafkaAdminClient(bootstrap_servers=BOOTSTRAP_SERVERS)
            topics = admin.list_topics()
            if TOPIC_NAME in topics:
                print(f"Kafka Topic '{TOPIC_NAME}' ist verfügbar.")
                return True
            else:
                print(f"Kafka erreichbar, aber Kafka Topic '{TOPIC_NAME}' wurde nicht gefunden (Versuch: {attempt + 1}/{MAX_RETRIES})")
        except (NoBrokersAvailable, KafkaError) as e:
            print(f"Kafka nicht erreichbar (Versuch: {attempt + 1}/{MAX_RETRIES}): {e}")
        time.sleep(SLEEP_INTERVAL)

    print(f"Kafka Topic '{TOPIC_NAME}' nicht erreichbar nach {MAX_RETRIES} Versuchen.")
    return False



# Vor dem Start von Spark
if not wait_for_kafka_topic():
    sys.exit(1)



# Ab hier beginnt die eigentliche Spark-Streaming-Anwendung
# Spark Session starten
# Setzen der verschiedenen Jars, welche im Dockerfile heruntergeladen und installiert werden
# Diese müssen hier angegeben werden, damit Spark sie auch findet
# Limitieren der Anzahl an Cores auf 16, da sonst ein Stream alle Ressourcen belegen würde und die
# anderen Streams nicht ausgeführt werden können
spark = SparkSession.builder \
     .appName("Kafka_Trades_to_Postgresql_Trades") \
     .master("spark://spark-master:7077") \
     .config("spark.jars",   "/opt/bitnami/spark/jars/postgresql-42.7.5.jar,"
                             "/opt/bitnami/spark/jars/kafka-clients-3.3.0.jar,"
                             "/opt/bitnami/spark/jars/spark-token-provider-kafka-0-10_2.12-3.5.0.jar,"
                             "/opt/bitnami/spark/jars/spark-sql-kafka-0-10_2.12-3.5.0.jar,"
                             "/opt/bitnami/spark/jars/commons-pool2-2.12.1.jar,"
                             "/opt/bitnami/spark/jars/spark-streaming-kafka-0-10_2.12-3.5.0.jar") \
     .config("spark.cores.max", "16") \
     .config("spark.ui.port", "4041") \
     .config("spark.ui.prometheus.enabled", "true") \
     .getOrCreate()


# Wichtig, damit die Felder des Streams eindeutig auseinandergehalten werden können
# Nicht immer notwendig, aber hier wichtig, da die Felder in der JSON-Message z.B.: "t" und "T" heißen
spark.conf.set('spark.sql.caseSensitive', True)

# Nur Fehler sollen geloggt werden
spark.sparkContext.setLogLevel("ERROR")

# Schema definieren - Muss 1:1 mit dem Schema der JSON-Message übereinstimmen
# Double kann nicht benutzt werden, da die Werte in der JSON-Message als String übergeben werden  
schema = StructType() \
    .add("e", StringType()) \
    .add("E", LongType()) \
    .add("s", StringType()) \
    .add("t", LongType()) \
    .add("p", StringType()) \
    .add("q", StringType()) \
    .add("T", LongType()) \
    .add("m", BooleanType()) \
    .add("M", BooleanType())
       
# Stream aus Kafka Topic lesen
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:29092") \
    .option("subscribe", "binance.trades") \
    .option("startingOffsets", "latest") \
    .load()

# Eigentliche Werte aus der JSON-Message extrahieren
value_df = df.select(from_json(col("value").cast("string"),schema).alias("value"))

# Schema der JSON-Message ausgeben -> Sollte jetzt genau auf den Websocket-Stream von Binance passen
value_df.printSchema()

# Benötigte Felder aus der JSON-Message extrahieren
# Da Double-Werte als String übergeben werden, müssen sie hier in Double umgewandelt werden 
postgresql_df = value_df.select(
      col("value.t").alias("trade_id"),
      col("value.s").alias("symbol"),
      col("value.T").alias("event_time"),
      col("value.p").alias("price").cast("Decimal(18, 8)"),
      col("value.q").alias("quantity").cast("Decimal(18, 8)")
    )

# Schema der extrahierten Felder ausgeben -> Sollte jetzt genau auf die PostgreSQL-Tabelle passen
postgresql_df.printSchema()


# Ausgabe in Konsole (zum Testen)
# query = postgresql_df.writeStream \
#        .outputMode("append") \
#        .format("console") \
#        .start()
    
# Transformierten Stream in PostgreSQL-Datenbank schreiben
query = postgresql_df.writeStream \
       .foreachBatch(write_to_postgres) \
       .outputMode("append") \
       .start()

query.awaitTermination()     




