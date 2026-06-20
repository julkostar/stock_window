# Download rrequired libraries
import sqlite3
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

# Function to fetch stock data
def fetch_stock_data(ticker, start_date, end_date):
    stock_data = yf.download(ticker, start=start_date, end=end_date)
    return stock_data

# Initalize standard page configuration
st.title("Stock Price Visualization")

# Side Bar for User Input
st.sidebar.header("User Input")
ticker_symbol = st.sidebar.text_input("Enter Stock Ticker", "AAPL")
start_date = st.sidebar.date_input("Start Date", datetime.now() - timedelta(days=365))
end_date = st.sidebar.date_input("End Date", datetime.now())

# Fetch stock data
stock_data = fetch_stock_data(ticker_symbol, start_date, end_date)

if stock_data.empty:
    st.write("No data found for the given ticker and date range.")
    st.stop()


ticker = yf.Ticker(ticker_symbol)

# Initialise tabs
tabs = st.tabs(["Raw Data", "Price Chart", "Moving Average", "Volume Chart", "Dividends and Splits"])

if "tracked_tickers" not in st.session_state:
    try:
        conn = sqlite3.connect("stock_data.db")
        # Grab only unique ticker names from the database
        df = pd.read_sql("SELECT DISTINCT Ticker FROM historical_prices", conn)
        st.session_state.tracked_tickers = df["Ticker"].tolist()
        conn.close()
    except Exception:
        # If the database or table doesn't exist yet, start with an empty list
        st.session_state.tracked_tickers = []


st.sidebar.title("🗄️ Database Ticker Manager")

# Input field to fetch a brand-new ticker
new_ticker = st.sidebar.text_input("Search New Ticker:", value="").upper()

# If you have saved tickers, show them in a dropdown menu
selected_ticker = None
if st.session_state.tracked_tickers:
    st.sidebar.markdown("### Saved Stocks")
    
    # Dropdown menu containing all previously saved tickers
    selected_ticker = st.sidebar.selectbox(
        "Load a saved stock:", 
        options=["Select a stock..."] + st.session_state.tracked_tickers
    )
    
    # --- DELETE MECHANISM ---
    st.sidebar.markdown("---")
    ticker_to_delete = st.sidebar.selectbox("Select stock to delete:", options=st.session_state.tracked_tickers, key="delete_box")
    
    if st.sidebar.button("❌ Permanent Delete From DB", type="secondary"):
        conn = sqlite3.connect("stock_data.db")
        cursor = conn.cursor()
        # Delete all rows associated with this ticker
        cursor.execute("DELETE FROM historical_prices WHERE Ticker = ?", (ticker_to_delete,))
        conn.commit()
        conn.close()
        
        # Update our active app memory list so the dropdown removes it instantly
        st.session_state.tracked_tickers.remove(ticker_to_delete)
        st.sidebar.success(f"Deleted {ticker_to_delete} from local storage!")
        st.rerun()

# Determine which ticker the main dashboard should actually run
if new_ticker:
    ticker_symbol = new_ticker
elif selected_ticker and selected_ticker != "Select a stock...":
    ticker_symbol = selected_ticker
else:
    ticker_symbol = "AAPL" # Default backup ticker if everything is blank



    # Check if the requested stock is already sitting in our database
is_cached = ticker_symbol in st.session_state.tracked_tickers

if is_cached:
    st.info(f"⚡ Loading {ticker_symbol} instantly from local SQL database...")
    conn = sqlite3.connect("stock_data.db")
    # Read data back out of SQL
    stock_data = pd.read_sql(f"SELECT * FROM historical_prices WHERE Ticker = '{ticker_symbol}'", conn)
    conn.close()
    
    # Reconstruct the index into a proper Datetime format that Matplotlib expects
    stock_data['Date'] = pd.to_datetime(stock_data['Date'])
    stock_data.set_index('Date', inplace=True)
else:
    st.warning(f"🌐 Fetching {ticker_symbol} live from Yahoo Finance...")
    ticker = yf.Ticker(ticker_symbol)
    stock_data = ticker.history(period="1y") # or use your start_date/end_date variables


with tabs[0]:
    st.subheader("Raw Stock Data")
    st.dataframe(stock_data.tail(10))
    st.download_button(
        label="Download CSV", 
        data=stock_data.to_csv(), 
        file_name=f"{ticker_symbol}_data.csv", 
        mime="text/csv"
    )
with tabs[1]:
    st.subheader("Stock Price Chart")
    plt.figure(figsize=(10, 5))
    plt.plot(stock_data.index, stock_data["Close"], label="Close Price")
    plt.title(f"{ticker_symbol} Stock Price")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    st.pyplot(plt)
with tabs[2]:  
    stock_data["MA"] = stock_data["Close"].rolling(window=20).mean()
    
    st.subheader("Moving Average (20-day)")
    plt.figure(figsize=(10, 5))
    plt.plot(stock_data.index, stock_data["Close"], label="Close Price")
    plt.plot(stock_data.index, stock_data["MA"], label="20-day MA", color="orange")
    plt.title(f"{ticker_symbol} Moving Average")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    st.pyplot(plt)

with tabs[3]:
    st.subheader("Volume Chart")
    plt.figure(figsize=(10, 5))
    
    # 1. Ensure the index is a flat 1D array of datetimes
    plot_index = stock_data.index.to_numpy()
    
    # 2. Extract Volume safely, flattening it to 1D even if it's a MultiIndex DataFrame
    if isinstance(stock_data["Volume"], pd.DataFrame):
        plot_volume = stock_data["Volume"].iloc[:, 0].to_numpy()
    else:
        plot_volume = stock_data["Volume"].to_numpy()
        
    # 3. Explicitly set width to stop Matplotlib from guessing based on the array
    plt.bar(plot_index, plot_volume, width=0.8, label="Volume", color="green")
    
    plt.title(f"{ticker_symbol} Trading Volume")
    plt.xlabel("Date")
    plt.ylabel("Volume")
    plt.legend()
    st.pyplot(plt)
    plt.clf()  # Clear figure for safety

with tabs[4]:
    st.subheader("Dividends and Splits")
    
    # yfinance history handles dividends/splits cleanly, but let's make sure they display nicely
    dividends = ticker.dividends
    dividends = dividends[str(start_date):str(end_date)]  # Filter dividends by date range

    splits = ticker.splits
    splits = splits[str(start_date):str(end_date)]  # Filter splits by date range

    st.write("### Dividends:")
    if not dividends.empty:
        st.dataframe(dividends)
    else:
        st.info("No recent dividend data found for this ticker.")
        
    st.write("### Splits:")
    if not splits.empty:
        st.dataframe(splits)
    else:
        st.info("No recent stock split data found for this ticker.")

with tabs[6]: # Your Database Control Tab
    st.subheader("Cache Controls")
    
    if st.button("Save Current Ticker Data"):
        if not stock_data.empty:
            conn = sqlite3.connect("stock_data.db")
            db_df = stock_data.copy().reset_index()
            db_df['Date'] = db_df['Date'].astype(str)
            db_df['Ticker'] = ticker_symbol
            
            db_df.to_sql("historical_prices", conn, if_exists="append", index=False)
            conn.close()
            
            # Update our session memory if it isn't already there
            if ticker_symbol not in st.session_state.tracked_tickers:
                st.session_state.tracked_tickers.append(ticker_symbol)
                
            st.success(f"Saved {ticker_symbol} to your database cache!")
            st.rerun()