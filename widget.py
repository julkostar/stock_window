# Download rrequired libraries
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

stock_data["MA"] = stock_data["Close"].rolling(window=20).mean()

# Initialise tabs
tabs = st.tabs(["Raw Data", "Price Chart", "Moving Average", "Volume Chart", "Dividends and Splits"])

ticker = yf.Ticker(ticker_symbol)

with tabs[0]:
    st.subheader("Raw Stock Data")
    st.dataframe(stock_data.tail(10))
    st.button("Download Data as CSV", on_click=lambda: st.download_button(label="Download CSV", data=stock_data.to_csv(), file_name=f"{ticker_symbol}_data.csv", mime="text/csv"))
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
    plt.bar(stock_data.index, stock_data["Volume"], label="Volume", color="green")
    plt.title(f"{ticker_symbol} Trading Volume")
    plt.xlabel("Date")
    plt.ylabel("Volume")
    plt.legend()
    st.pyplot(plt)
with tabs[4]:
    st.subheader("Dividends and Splits")
    dividends = ticker.dividends
    splits = ticker.splits
    st.write("Dividends:")
    st.dataframe(dividends)
    st.write("Splits:")
    st.dataframe(splits)
