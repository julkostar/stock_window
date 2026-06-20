import sqlite3
import pandas as pd

class DatabaseManager:
    def __init__(self, db_name="stock_data.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS stock_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER
        )
        """
        self.conn.execute(query)
        self.conn.commit()

    def insert_stock_data(self, ticker, date, open_price, high_price, low_price, close_price, volume):
        query = """
        INSERT INTO stock_data (ticker, date, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(query, (ticker, date, open_price, high_price, low_price, close_price, volume))
        self.conn.commit()

    def fetch_stock_data(self, ticker):
        query = "SELECT * FROM stock_data WHERE ticker = ?"
        df = pd.read_sql_query(query, self.conn, params=(ticker,))
        return df

    def close_connection(self):
        self.conn.close()



def addtodatabase(ticker, stock_data):
    db_manager = DatabaseManager()
    # Find the most recent date in the database for the given ticker
    if db_manager.fetch_stock_data(ticker, stock_data) is not None:
        query = "SELECT MAX(date) FROM stock_data WHERE ticker = ?"
        latest_date = pd.read_sql_query(query, db_manager.conn, params=(ticker,)).iloc[0, 0]
        if latest_date is not None:
            stock_data = stock_data[stock_data.index > latest_date]

    for index, row in stock_data.iterrows():
        db_manager.insert_stock_data(
            ticker,
            index.strftime("%Y-%m-%d"),
            row["Open"],
            row["High"],
            row["Low"],
            row["Close"],
            row["Volume"]
        )
    db_manager.close_connection()
