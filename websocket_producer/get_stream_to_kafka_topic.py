import os
import time
import json
import asyncio
import websockets
from kafka import KafkaProducer

# Kafka-Server-URL setzen (so wie im Docker-Compose-File definiert)
KAFKA_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")

# Methode zum Erstellen des Kafka-Producer
# Nach 10 Versuchen wird eine Exception geworfen
def create_producer():
    retries = 30
    while retries > 0:
        try:
            return KafkaProducer(
                bootstrap_servers=KAFKA_SERVER,
                value_serializer=lambda m: json.dumps(m).encode("utf-8")
            )
        except Exception as e:
            print(f"Verbindung konnte nicht aufgebaut werden... ({retries} Versuche übrig)")
            retries -= 1
            time.sleep(3)
    raise Exception("Verbindung zu Kafka fehlgeschlagen.")


# Methode zum Streamen von Daten von Binance und Senden an Kafka
async def stream_data(stream_url: str, kafka_topic: str):
    async with websockets.connect(stream_url) as websocket:
        print(f"Verbindung zu WebSocket Stream {stream_url} erfolgreich, Daten werden in Kafka Topic '{kafka_topic}' geschrieben.")
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                producer.send(kafka_topic, data)
                print(f"[{kafka_topic}] Senden: {data['s']} @ {data['p']}")
            except Exception as e:
                print(f"[{kafka_topic}] Fehler: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    
    # Erstellen des Kafka-Producers
    producer = create_producer()
    
    # Stream-URLs und Kafka-Topics definieren
    streams = [
        # Bitcoin
        ("wss://stream.binance.com:9443/ws/btcusdt@trade", "binance.trades"), #Trades Stream
        ("wss://stream.binance.com:9443/ws/btcusdt@ticker_1h", "binance.ticker_1h"), #Ticker Stream (Zeitfenster 1h)
        ("wss://stream.binance.com:9443/ws/btcusdt@ticker", "binance.ticker_1d"), #Ticker Stream (Zeitfenster 1d)
        
        # Ethereum
        ("wss://stream.binance.com:9443/ws/ethusdt@trade", "binance.trades"), # Trades Stream
        ("wss://stream.binance.com:9443/ws/ethusdt@ticker_1h", "binance.ticker_1h"), #Ticker Stream (Zeitfenster 1h)
        ("wss://stream.binance.com:9443/ws/ethusdt@ticker_1d", "binance.ticker_1d"), #Ticker Stream (Zeitfenster 1d)
        
        # Solana
        ("wss://stream.binance.com:9443/ws/solusdt@trade", "binance.trades"), # Trades Stream
        ("wss://stream.binance.com:9443/ws/solusdt@ticker_1h", "binance.ticker_1h"), #Ticker Stream (Zeitfenster 1h)
        ("wss://stream.binance.com:9443/ws/solusdt@ticker_1d", "binance.ticker_1d") #Ticker Stream (Zeitfenster 1d)
        
        # hier ggf. neue URLs und entsprechende Kafka-Topics hinzufügen
    ]

    # Streamverarbeitung starten
    loop = asyncio.get_event_loop()
    tasks = [stream_data(url, topic) for url, topic in streams]
    loop.run_until_complete(asyncio.gather(*tasks))