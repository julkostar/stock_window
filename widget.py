    # Download required libraries
import sqlite3
import widget

import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

    # Function to fetch stock data
def fetch_stock_data(ticker, start_date, end_date):
     ticker_obj = yf.Ticker(ticker)
     # history() accepts start and end inputs cleanly and keeps schemas uniform
     stock_data = ticker_obj.history(start=start_date, end=end_date)
     return stock_data

def render_comparison_mode():
    st.header("⚖️ Multi-Stock Comparison Mode")
    st.write("Analyze the variance, covariance, and relationship matrices between two assets.")

    start_date = st.sidebar.date_input("Start Date", datetime.now() - timedelta(days=365))
    end_date = st.sidebar.date_input("End Date", datetime.now())

    # 1. Inputs for two tickers
    col1, col2 = st.columns(2)
    with col1:
        ticker_1 = st.text_input("First Stock Ticker", "AAPL").upper()
    with col2:
        ticker_2 = st.text_input("Second Stock Ticker", "MSFT").upper()

    # Use your existing date sliders (they can stay global in your sidebar)
    with st.spinner(f"Correlating data for {ticker_1} and {ticker_2}..."):
        # 2. Fetch both (Using your existing fetch function)
        data1 = fetch_stock_data(ticker_1, start_date, end_date)
        data2 = fetch_stock_data(ticker_2, start_date, end_date)

        if data1.empty or data2.empty:
            st.error("Could not retrieve clean historical data for one or both symbols.")
            return

        # 3. Align datasets using Pandas Inner Join on Date index
        combined = pd.DataFrame({
            ticker_1: data1["Close"],
            ticker_2: data2["Close"]
        }).dropna()

        # Calculate daily percentage returns (crucial for accurate financial covariance)
        returns = combined.pct_change().dropna()

    # 4. Display Core Metrics
    st.subheader("📊 Statistical Relationship Data")
    
    # Calculate Covariance and Correlation Matrices
    cov_matrix = returns.cov()
    cor_matrix = returns.corr()

    # Isolate cross-asset values
    covariance_val = cov_matrix.loc[ticker_1, ticker_2]
    correlation_val = cor_matrix.loc[ticker_1, ticker_2]

    m_col1, m_col2 = st.columns(2)
    with m_col1:
        # Volatility correlation value scale is always between -1 and +1
        st.metric(label="Correlation Coefficient", value=f"{correlation_val:.4f}")
        st.caption("Measures direction and strength of linear movement (-1 to +1)")
    with m_col2:
        st.metric(label="Daily Covariance", value=f"{covariance_val:.6f}")
        st.caption("Measures how their directional returns scale together")

    # 5. Comparative Visual Charts
    st.subheader("📈 Performance Trajectory Scaling")
    
    # Normalize price indices to start at 100% so users can compare growth scale evenly
    normalized_df = (combined / combined.iloc[0]) * 100
    
    plt.figure(figsize=(10, 4))
    plt.plot(normalized_df.index, normalized_df[ticker_1], label=f"{ticker_1} Normalized")
    plt.plot(normalized_df.index, normalized_df[ticker_2], label=f"{ticker_2} Normalized")
    plt.title("Growth Comparison Baseline (Starting point scaled to 100)")
    plt.xlabel("Date")
    plt.ylabel("Relative Performance Score")
    plt.legend()
    st.pyplot(plt)
    plt.clf()

import pmdarima as pm

def render_prediction_mode():
    st.header("🤖 Advanced Machine Learning Prediction Mode")
    st.write("Train analytical forecasting engines on historical pricing parameters.")

    start_date = st.sidebar.date_input("Start Date", datetime.now() - timedelta(days=365))
    end_date = st.sidebar.date_input("End Date", datetime.now())

    target_ticker = st.text_input("Enter Target Ticker for ML Model", "AAPL").upper()
    tab = st.tabs(["ARIMA Forecasting", "LSTM Neural Network (Coming Soon)", "Monte Carlo Simulation (Coming Soon)", "Sentiment Analysis (Coming Soon)"])
    with tab[0]:
        # Run a simple 30-day requirement boundary check
        hist_data = fetch_stock_data(target_ticker, start_date, end_date)
        
        if len(hist_data) < 40:
            st.warning("Please extend your historical sidebar dates. Models require a minimum footprint of 40 active daily rows to map trend variables properly.")
            return

        if st.button("🚀 Train ARIMA & Generate Forecast"):
            with st.spinner("Processing statistical patterns..."):
                close_series = hist_data["Close"].dropna()
                
                # Auto-fit structural parameters
                model = pm.auto_arima(close_series, seasonal=False, error_action="ignore", suppress_warnings=True)
                forecast, conf_int = model.predict(n_periods=7, return_conf_int=True)
                
                # Map forward business calendar dates
                future_dates = pd.date_range(start=close_series.index[-1], periods=8, freq='B')[1:]

                # Render
                plt.figure(figsize=(10, 4))
                plt.plot(close_series.index[-30:], close_series[-30:], label="Recent Actual Close", color="blue")
                plt.plot(future_dates, forecast, label="7-Day Predictive Target Path", color="red", linestyle="--")
                plt.fill_between(future_dates, conf_int[:, 0], conf_int[:, 1], color="red", alpha=0.15, label="Model Error Boundary")
                plt.title(f"{target_ticker} Forward Estimation Analysis")
                plt.legend()
                st.pyplot(plt)
                plt.clf()
                
                forecast.index = future_dates
                st.dataframe(pd.DataFrame({"Predicted Valuation": forecast}, index=future_dates))
    with tab[1]:
        st.info("LSTM Neural Network forecasting is currently in development and will be available in a future update. Stay tuned for deep learning-powered insights!")
    with tab[2]:
        st.info("Monte Carlo Simulation for stock price forecasting is currently in development and will be available in a future update. Stay tuned for probabilistic modeling insights!")
    with tab[3]:
        st.info("Sentiment Analysis integration is currently in development and will be available in a future update. Stay tuned for news-driven market insights!")

app_mode = st.sidebar.selectbox("🎯 Select App Mode", ["Standard Dashboard", "Stock Comparison", "ML Prediction"])
st.sidebar.markdown("---")

if app_mode == "Standard Dashboard":
    # Initialize standard page configuration
    st.title("Stock Price Visualization")

    # --- STEP 1: INITIALIZE SESSION STATE MEMORY ---
    if "tracked_tickers" not in st.session_state:
        try:
            conn = sqlite3.connect("stock_data.db")
            df = pd.read_sql("SELECT DISTINCT Ticker FROM historical_prices", conn)
            st.session_state.tracked_tickers = df["Ticker"].tolist()
            conn.close()
        except Exception:
            st.session_state.tracked_tickers = []

    # --- STEP 2: SIDEBAR USER CONFIGURATIONS ---
    st.sidebar.header("User Input")
    base_ticker_symbol = st.sidebar.text_input("Enter Stock Ticker", "AAPL").upper()
    start_date = st.sidebar.date_input("Start Date", datetime.now() - timedelta(days=365))
    end_date = st.sidebar.date_input("End Date", datetime.now())

    st.sidebar.title("🗄️ Database Ticker Manager")
    new_ticker = st.sidebar.text_input("Search New Ticker:", value="").upper()

    selected_ticker = None
    if st.session_state.tracked_tickers:
        st.sidebar.markdown("### Saved Stocks")
        selected_ticker = st.sidebar.selectbox(
            "Load a saved stock:", 
            options=["Select a stock..."] + st.session_state.tracked_tickers
        )
        
        st.sidebar.markdown("---")
        ticker_to_delete = st.sidebar.selectbox("Select stock to delete:", options=st.session_state.tracked_tickers, key="delete_box")
        
        if st.sidebar.button("❌ Permanent Delete From DB", type="secondary"):
            conn = sqlite3.connect("stock_data.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM historical_prices WHERE Ticker = ?", (ticker_to_delete,))
            conn.commit()
            conn.close()
            
            st.session_state.tracked_tickers.remove(ticker_to_delete)
            st.sidebar.success(f"Deleted {ticker_to_delete} from local storage!")
            st.rerun()

    # --- STEP 3: RESOLVE ACTIVE TICKER LOGIC ---
    if new_ticker:
        ticker_symbol = new_ticker
    elif selected_ticker and selected_ticker != "Select a stock...":
        ticker_symbol = selected_ticker
    else:
        ticker_symbol = base_ticker_symbol

    # --- STEP 4: FETCH TARGET SOURCE DATA (DB vs Live) ---
    # --- STEP 4: FETCH TARGET SOURCE DATA (DB vs Live) ---
    is_cached = ticker_symbol in st.session_state.tracked_tickers
    load_from_db = False

    if is_cached:
        conn = sqlite3.connect("stock_data.db")
        date_bounds = pd.read_sql(
            "SELECT MIN(Date) as min_d, MAX(Date) as max_d FROM historical_prices WHERE Ticker = ?", 
            conn, 
            params=(ticker_symbol,)
        ).iloc[0]
        conn.close()
        
        if date_bounds['min_d'] is not None and date_bounds['max_d'] is not None:
            # FORCE BOTH BOUNDS TO PURE .date() OBJECTS (No timezones, no hours/minutes)
            db_min = pd.to_datetime(date_bounds['min_d'], format='mixed', utc=True).date()
            db_max = pd.to_datetime(date_bounds['max_d'], format='mixed', utc=True).date()
            
            # Ensure the user input variables are also cast explicitly to standard dates
            user_start = pd.to_datetime(start_date).date()
            user_end = pd.to_datetime(end_date).date()
            
            # Compare pure date vs pure date
            if user_start >= db_min and user_end <= db_max:
                load_from_db = True

    # --- EXECUTE THE FETCH ---
    if load_from_db:
        st.info(f"⚡ Loading {ticker_symbol} instantly from local SQL database...")
        conn = sqlite3.connect("stock_data.db")
        query = "SELECT * FROM historical_prices WHERE Ticker = ? AND Date BETWEEN ? AND ?"
        stock_data = pd.read_sql(query, conn, params=(ticker_symbol, str(start_date), str(end_date)))
        conn.close()
        
        stock_data = stock_data.drop_duplicates(subset=['Date', 'Ticker'], keep='first')
        
        stock_data['Date'] = pd.to_datetime(stock_data['Date'], format='mixed', utc=True)
        stock_data['Date'] = stock_data['Date'].dt.tz_localize(None)
        stock_data.set_index('Date', inplace=True)
    else:
        st.warning(f"🌐 requested dates outside local cache. Fetching {ticker_symbol} live from Yahoo Finance...")
        stock_data = fetch_stock_data(ticker_symbol, start_date, end_date)
    
    if stock_data.empty:
        st.write("No data found for the given ticker and date range.")
        st.stop()

    ticker = yf.Ticker(ticker_symbol)

    # --- STEP 5: TABS PRESENTATION ---
    tabs = st.tabs(["Raw Data", "Price Chart", "Moving Average", "Volume Chart", "Dividends and Splits", "Database Controls"])


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
        
        # 1. Fetch data safely
        dividends = ticker.dividends
        splits = ticker.splits
        
        st.write("### Dividends:")
        # Check if dividends exists and is a valid Pandas Series/DataFrame before slicing
        if dividends is not None and not dividends.empty:
            dividends = dividends[str(start_date):str(end_date)]  # Now safe to filter
            
            if not dividends.empty:
                st.dataframe(dividends)
            else:
                st.info(f"No dividends paid out between {start_date} and {end_date}.")
        else:
            st.info("No historical dividend data found for this ticker.")
            
        st.write("### Splits:")
        # Check if splits exists and is a valid Pandas Series/DataFrame before slicing
        if splits is not None and not splits.empty:
            splits = splits[str(start_date):str(end_date)]  # Now safe to filter
            
            if not splits.empty:
                st.dataframe(splits)
            else:
                st.info(f"No stock splits occurred between {start_date} and {end_date}.")
        else:
            st.info("No historical stock split data found for this ticker.")

    with tabs[5]:
        st.subheader("Cache Controls")
        
        if st.button("Save Current Ticker Data"):
            if not stock_data.empty:
                conn = sqlite3.connect("stock_data.db")
                
                # 1. Prepare your incoming dataframe
                db_df = stock_data.copy()
                
                # Drop the index name if it's messing with column alignments
                if db_df.index.name == 'Date' or 'Date' not in db_df.columns:
                    db_df = db_df.reset_index()
                
                # CRUCIAL: Flatten multi-layered columns from yfinance
                if isinstance(db_df.columns, pd.MultiIndex):
                    db_df.columns = [col[0] if col[1] == '' else col[0] for col in db_df.columns]
                
                # Force columns to match standard expected SQLite table schema names exactly
                # This strips away structural columns like 'Adj Close' if your database didn't start with them
                expected_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                
                # Clean and isolate dates as clean YYYY-MM-DD string records
                db_df['Date'] = pd.to_datetime(db_df['Date'], format='mixed', utc=True).dt.date.astype(str)
                db_df['Ticker'] = ticker_symbol
                
                # Dynamically filter out columns that are not part of your primary historical table schema
                final_cols = [col for col in db_df.columns if col in expected_columns or col == 'Ticker']
                db_df = db_df[final_cols]

                try:
                    # 2. Fetch all unique dates currently logged in SQL for this stock
                    query = "SELECT Date FROM historical_prices WHERE Ticker = ?"
                    existing_dates_df = pd.read_sql_query(query, conn, params=(ticker_symbol,))
                    
                    if not existing_dates_df.empty:
                        existing_dates_set = set(existing_dates_df['Date'].astype(str).tolist())
                        
                        # 3. Filter down incoming data to ONLY dates missing from the DB
                        mask = [row_date not in existing_dates_set for row_date in db_df['Date']]
                        new_rows_to_save = db_df[mask]
                    else:
                        new_rows_to_save = db_df
                        
                except Exception:
                    # Fallback if the table schema doesn't exist yet in the database file
                    new_rows_to_save = db_df

                # 4. Safely append ONLY the fresh historical rows with clean column matching
                if not new_rows_to_save.empty:
                    new_rows_to_save.to_sql("historical_prices", conn, if_exists="append", index=False)
                    st.success(f"Successfully added {len(new_rows_to_save)} new daily records to the cache!")
                else:
                    st.info("All selected dates are already backed up in your local database.")
                    
                conn.close()
                
                if ticker_symbol not in st.session_state.tracked_tickers:
                    st.session_state.tracked_tickers.append(ticker_symbol)
                    
                st.rerun()

elif app_mode == "Stock Comparison":
        render_comparison_mode()

elif app_mode == "ML Prediction":
        render_prediction_mode()


