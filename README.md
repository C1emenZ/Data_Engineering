<div align="center">

# Data Engineering - Echtzeitverarbeitung von Binance WebSocket Streams

</div>

## Inhaltsverzeichnis
1. [Einleitung](#1-einleitung)
2. [Technische Rahmenbedingungen und Konzepte](#2-technische-rahmenbedingungen-und-konzepte)
   - [2.1 Komponenten der Architektur](#21-komponenten-der-architektur)   
   - [2.2 Voraussetzungen](#22-voraussetzungen)
   - [2.3 Architekturkonzeption](#23-architekturkonzeption)
3. [Datenquelle](#3-datenquelle)
   - [3.1 Binance WebSocket Streams](#31-binance-websocket-streams)
   - [3.2 Datenstruktur](#32-datenstruktur)
4. [Installationsanleitung](#4-installationsanleitung)
5. [Beispiel](#5-beispiel)
   - [5.1 Start der Pipeline](#51-start-der-pipeline)
   - [5.2 Grafana - Dashboards](#52-grafana---dashboards)
   - [5.3 Prometheus](#53-prometheus)
   - [5.4 Promtail](#54-promtail)
   - [5.5 Spark](#55-spark)

## 1. Einleitung

Dieses Projekt implementiert eine Echtzeit-Datenverarbeitungspipeline für Kryptodaten der Krptobörse Binance und verwendet dabei Microservices, welche in Docker Containern betrieben werden. Die Daten werden über WebSocket Streams gesendet und mittels Apache Kafka, Apache Spark und PostgreSQL verarbeitet und gespeichert. Die Visualisierung der Kryptodaten sowie des Monitorings und Loggings erfolgt über Grafana-Dashboards. Gleichzeitig werden Standards in Bezug auf Datensicherheit, Datenschutz, Data Governance, Skalierbarkeit, Zuverlässigkeit und Wartbarkeit umgesetzt. 


## 2. Technische Rahmenbedingungen und Konzepte

### 2.1 Komponenten der Architektur

**Datenerfassung und -streaming:**
- **WebSocket Producer**: Service zur Erfassung der Binance WebSocket Streams
- **Apache Kafka Broker**: Message Broker für die Datenstreamverarbeitung


**Datenverarbeitung:**
- **Spark Master**: Koordination der Spark-Verarbeitung
- **Spark Worker**: Ausführung der Datenverarbeitungsjobs
- **Spark Submit Services**: Drei separate Services für die Verarbeitung von:
  - Trade-Daten
  - aggregierte Daten der letzten Stunde (Ticker_1h)
  - aggregierte Daten des letzten Tages (Ticker_1d)

**Datenspeicherung:**
- **PostgreSQL**: Speicherung der verarbeiteten Binance Datenstreams

**Datenvisualisierung:**
- **Grafana**: Visualisierung der Datenstreams von Binance sowie von Metriken und Logs

**Monitoring und Logging:**
- **Prometheus**: Sammlung und Speicherung von Metriken der einzelnen Services
- **Postgres Exporter**: Erfassung von PostgreSQL-Metriken für das Monitoring
- **Loki**: Zentrale Log-Aggregation
- **Promtail**: Log-Sammler für Container-Logs

### 2.2 Voraussetzungen

Für die Installation und Ausführung des Projekts werden folgende Tools benötigt:
- IDE wie zum Beispiel VS Code
- Docker Desktop 

### 2.3 Architekturkonzeption
<div align="center">
  <img src="abbildungen/Architektur_Erweitert.png" alt="Architekturkonzeption">
</div>

## 3. Datenquelle

### 3.1 Binance WebSocket Streams
Die Binance WebSocket Streams bieten Echtzeit-Markdaten für Kryptowährungen. In diesem Projekt werden folgende Streams verwendet:

**Trade Stream:**
```
wss://stream.binance.com:9443/ws/<symbol>@trade
```
Beispiel: `wss://stream.binance.com:9443/ws/btcusdt@trade`

<br>

**Ticker Stream:**
```
wss://stream.binance.com:9443/ws/<symbol>@ticker_1h  // 1-Stunden-Ticker
```
Beispiel: `wss://stream.binance.com:9443/ws/btcusdt@ticker_1h`

<br>

```
wss://stream.binance.com:9443/ws/<symbol>@ticker     // 24-Stunden-Ticker
```
Beispiel: `wss://stream.binance.com:9443/ws/btcusdt@ticker`
`

<br>

### 3.2 Datenstruktur
**Trade Stream Felder:**

| Feldname | Datentyp | Beschreibung                                                                                |
|------|-----|--------------------------------------------------------------------------------------------|
| e    | String | Ereignistyp des WebSocket-Events (konstant "trade" für Handelsereignisse)                |
| E    | Long   | Zeitstempel der Eventverarbeitung auf Binance-Servern (Unix Timestamp in Millisekunden) |
| s    | String | Handelspaarsymbol in Großbuchstaben (z.B. "BTCUSDT" für Bitcoin-USDT-Handel)           |
| t    | Long   | Eindeutige Trade-ID des ausgeführten Handels auf Binance                                |
| p    | Double | Ausführungspreis des Trades in Quote Asset (USDT)                                       |
| q    | Double | Ausgeführte Handelsmenge des Base Assets (BTC, ETH, SOL)                                |
| T    | Long   | Zeitstempel der Handelsausführung (Unix Timestamp in Millisekunden)                     |
| m    | Boolean| Market Maker Flag (true = Käufer ist Market Maker, false = Verkäufer ist Market Maker)  |

<br>

**Ticker Stream Felder:**

| Feldname | Datentyp | Beschreibung                                                                                |
|------|-----|--------------------------------------------------------------------------------------------|
| e    | String | Ereignistyp des WebSocket-Events ("24hrTicker" für 24h-Ticker, "1hTicker" für 1h-Ticker) |
| E    | Long   | Zeitstempel der Eventverarbeitung auf Binance-Servern (Unix Timestamp in Millisekunden)  |
| s    | String | Handelspaarsymbol in Großbuchstaben (z.B. "BTCUSDT" für Bitcoin-USDT-Ticker)            |
| p    | Double | Absolute Preisänderung im Betrachtungszeitraum (1h oder 24h)                            |
| P    | Double | Relative Preisänderung im Betrachtungszeitraum (in Prozent)                             |
| w    | Double | Volumengewichteter Durchschnittspreis (VWAP) im Betrachtungszeitraum                    |
| c    | Double | Schlusskurs (aktueller Preis) des letzten ausgeführten Trades                           |
| Q    | Double | Handelsmenge des letzten ausgeführten Trades                                             |
| o    | Double | Eröffnungspreis zu Beginn des Betrachtungszeitraums                                     |
| h    | Double | Höchster Handelspreis im Betrachtungszeitraum                                            |
| l    | Double | Niedrigster Handelspreis im Betrachtungszeitraum                                         |
| v    | Double | Gesamtes Handelsvolumen im Base Asset (BTC, ETH, SOL)                                   |
| q    | Double | Gesamtes Handelsvolumen im Quote Asset (USDT)                                            |

## 4. Installationsanleitung

1. **Arbeitsverzeichnis vorbereiten**
   - erzeichnis für das Projekt auswählen
   - Terminal öffnen und zu diesem Verzeichnis navigieren

2. ** GitHub Repository klonen**
```bash
git clone https://github.com/C1emenZ/Data_Engineering.git
```

3. **In Projektverzeichnis wechseln**
```bash
cd Data_Engineering
```

4. **Umgebungsvariablen einrichten**
   - Die Datei `.env.beispiel` in `.env` umbenennen
   - Die Parameter für PostgreSQL und Grafana anpassen

5. **Services starten**
```bash
docker-compose up -d
```

## 5. Beispiel

### 5.1 Start der Pipeline
Nach dem Start der Docker Container mit `docker-compose up -d` kann der Start der Pipeline über zwei Möglichkeiten überprüft werden:

1. **Terminal-Ausgabe:**
<div align="center">
  <img src="abbildungen/Dockercontainer_Terminal.png" alt="Erfolgreicher Start der Container im Terminal">
</div>

2. **Docker Desktop Ansicht:**
<div align="center">
  <img src="abbildungen/Dockercontainer.png" alt="Laufende Container in Docker Desktop">
</div>

### 5.2 Grafana - Dashboards 
Über http://localhost:3000 kann Grafana geöffnet werden. Dabei muss sich zuerst mit dem User und Passwort angemeldet werden, welches vorher in der .env-Datei gesetzt wurde.
<div align="center">
  <img src="abbildungen/Grafana_Login.png" alt="Grafana_Login">
</div>

<br>

Um das Dashboard zu wechseln, kann die Navigation auf der linken Seite verwendet werden.
<div align="center">
  <img src="abbildungen/Grafana_Navigation.png" alt="Grafana_Navigation">
</div>

1. **Kryptodaten:** 
Standardmäßig wird das Dashboard mit den Kryptodaten angezeigt. Über die Dropdown-Auswahl am oberen linken Rand kann die Kryptowährung geändert werden.
<div align="center">
  <img src="abbildungen/Krypto_Dashboard.png" alt="Krypto">
</div>

<br>

2. **Monitoring-Dashboard:** 
Auf dem Monitoring Dashboard werden verschiedene Metriken angezeigt. In der ersten Reihe wird für ausgewählte Services angezeigt, ob die entsprechenden Containern aktuell laufen.
Die ersten drei Blöcke in der zweiten Zeile zeigen die Anzahl der Nachrichten pro Sekunde für das entsprechende Kafka Topic. Die drei Fenster daneben zeigen die aktuelle Anzahl der Tabelleneinträge. 
Im größereren Fenster darunter werden alle Logs der aktuell laufenden Docker Container ausgegeben.
<div align="center">
  <img src="abbildungen/Monitoring_Dashboard.png" alt="Monitoring">
</div>

### 5.3 Prometheus
Über http://localhost:9090/targets können alle Services überprüft werden, welche aktuell in Prometheus definiert sind und aus denen regelmäßig Metriken abgeholt werden. 
<div align="center">
  <img src="abbildungen/Prometheus_Targets.png" alt="Prometheus">
</div>

### 5.4 Promtail
Die Logs der Container werden über Promtail gesammelt. Dabei wird zuerst das Verzeichnis definiert, welches durch Promtail überwacht werden soll. Werden neue Zeilen zu den dort gespeicherten Logdateien hinzugefügt, werden diese automatisch an Loki gesendet und dort für die Visualisierung in Grafana gespeichert. Promtail kann über http://localhost:9080/targets aufgerufen werden. 
<div align="center">
  <img src="abbildungen/Promtail_Targets.png" alt="Promtail">
</div>

### 5.5 Spark
Die eigentliche Datenverarbeitung findet in den Spark-Workern statt. Dabei werden die Aufgaben über den Spark-Master an die verschiedenen Spark-Worker verteilt. Über http://localhost:8088/ kann diese Ausführung überwacht werden.
<div align="center">
  <img src="abbildungen/Spark_Master.png" alt="Spark_Master">
</div>

<br>

In den Spark-Submits (http://localhost:4041/jobs/, http://localhost:4042/jobs/, ...) sieht man die eigentliche Ausführung der Streamverarbeitung. Der Job wird zwar kontinuierlich ausgeführt, die Daten werden aber in einzelnen Batches verarbeitet, welche hier angezeigt werden können.
<div align="center">
  <img src="abbildungen/Spark_Submit.png" alt="Spark_Submit">
</div>

