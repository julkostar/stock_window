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
    
    if stock_data.empty:
        return
    
    # 1. Make sure the incoming stock_data index consists of string dates matching your DB format
    # This ensures smooth comparisons regardless of timezone/datetime typing
    incoming_df = stock_data.copy()
    if not isinstance(incoming_df.index, pd.Index):
        incoming_df = incoming_df.reset_index()
    
    # Standardize incoming dates to strings matching how they sit in your DB
    incoming_dates = incoming_df.index.strftime('%Y-%m-%d').tolist()
    
    try:
        # 2. Fetch ALL dates currently recorded in the database for this specific ticker
        query = "SELECT Date FROM historical_prices WHERE Ticker = ?"
        existing_dates_df = pd.read_sql_query(query, db_manager.conn, params=(ticker,))
        
        if not existing_dates_df.empty:
            # Convert existing DB dates into a set for O(1) lightning-fast lookups
            existing_dates_set = set(existing_dates_df['Date'].astype(str).tolist())
            
            # 3. Filter incoming data down to rows where the date string does NOT exist in the set
            # We map the index dates to strings temporarily to perform the mask filter
            mask = [str(date.date()) not in existing_dates_set for date in stock_data.index]
            new_data_to_append = stock_data[mask]
        else:
            # If the database returns nothing for this ticker, everything incoming is new
            new_data_to_append = stock_data

        # 4. Append only the genuinely unique, non-duplicated rows
        if not new_data_to_append.empty:
            db_df = new_data_to_append.copy().reset_index()
            db_df['Date'] = db_df['Date'].astype(str)
            db_df['Ticker'] = ticker
            
            db_df.to_sql("historical_prices", db_manager.conn, if_exists="append", index=False)
            
    except Exception as e:
        # Handle cases where the table doesn't even exist yet (first-time run initialization)
        db_df = stock_data.copy().reset_index()
        db_df['Date'] = db_df['Date'].astype(str)
        db_df['Ticker'] = ticker
        db_df.to_sql("historical_prices", db_manager.conn, if_exists="append", index=False)

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
