-- Initialisierungsskript für die Datenbank
-- Dieses Skript erstellt die notwendigen Tabellen für die Speicherung der Daten

-- Tabelle für alle Käufe/Verkäufe (Trades) erstellen
CREATE TABLE IF NOT EXISTS trades (
    trade_id BIGINT,
    symbol TEXT,  
    event_time BIGINT,
    price DOUBLE PRECISION,
    quantity DOUBLE PRECISION,
    PRIMARY KEY (trade_id, symbol)
);


-- Tabelle für aggregierte Daten der letzten Stunde (1h) erstellen
CREATE TABLE IF NOT EXISTS ticker_1h (
    event_time BIGINT,
    symbol TEXT,
    price_change FLOAT,
    price_change_percent FLOAT,
    last_price FLOAT,
    open_price FLOAT,
    high_price FLOAT,
    low_price FLOAT,
    volume FLOAT,
    total_trades BIGINT,
    PRIMARY KEY (event_time, symbol)
);


-- Tabelle für aggregierte Daten der letzten 24 Stunden (1d) erstellen
CREATE TABLE IF NOT EXISTS ticker_1d (
    event_time BIGINT,
    symbol TEXT,
    price_change FLOAT,
    price_change_percent FLOAT,
    last_price FLOAT,
    open_price FLOAT,
    high_price FLOAT,
    low_price FLOAT,
    volume FLOAT,
    total_trades BIGINT,
    PRIMARY KEY (event_time, symbol)
);