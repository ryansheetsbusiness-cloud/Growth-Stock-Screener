import streamlit as st
import pandas as pd
import yfinance as yf
import time

st.set_page_config(page_title="Growth Stock Hunter", page_icon="🚀", layout="wide")

st.title("🚀 Multi-Index Growth Stock Hunter")
st.subheader("Custom Built Screener: Auto-Calculating PEG and CAGR Profiles")

# --- TICKER DATABASES ---
russell_1000_watchlist = ["MSFT", "AAPL", "NVDA", "AMZN", "META", "GOOGL", "LLY", "AVGO", "V", "COST", "AMD", "NFLX"]
russell_2000_watchlist = ["CELH", "ELF", "CROX", "POWI", "AXON", "STEP", "SG", "HALO", "AAON", "KNSL", "FIX", "SPSC"]

market_choice = st.selectbox(
    "🎯 Select Market Index to Scan:",
    options=["Russell 1000 (Large/Mid-Cap Leaders)", "Russell 2000 (Small-Cap Compounders)"]
)

if "Russell 1000" in market_choice:
    active_watchlist = list(set(russell_1000_watchlist))
    max_debt_allowed = 120  
    st.info("💡 Target: Large-cap structural market leaders.")
else:
    active_watchlist = list(set(russell_2000_watchlist))
    max_debt_allowed = 65   
    st.info("💡 Target: Agile, high-velocity small caps.")

# --- DATA EXTRACTOR & CUSTOM CALCULATOR ---
def analyze_stock(ticker, max_debt):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        pe_ratio = info.get('trailingPE')
        debt_to_equity = info.get('debtToEquity')
        
        if pe_ratio is None or debt_to_equity is None:
            return None
            
        if debt_to_equity > max_debt:
            return None
            
        financials = stock.financials
        if 'Total Revenue' not in financials.index or financials.shape[1] < 4:
            return None
            
        rev_series = financials.loc['Total Revenue'].values
        rev_recent = rev_series[0]
        rev_4years_ago = rev_series[3]
        
        if rev_recent <= 0 or rev_4years_ago <= 0:
            return None
            
        cagr = (rev_recent / rev_4years_ago) ** (1/3) - 1
        cagr_percentage = cagr * 100
        
        if cagr_percentage < 10: 
            return None
            
        custom_peg = pe_ratio / cagr_percentage
        
        if 0.2 <= custom_peg <= 1.8:
            return {
                "Ticker": ticker,
                "Company": info.get('shortName', 'N/A'),
                "Trailing P/E": round(pe_ratio, 2),
                "3-Yr Rev CAGR (%)": round(cagr_percentage, 2),
                "Calculated PEG": round(custom_peg, 2),
                "Debt/Equity (%)": round(debt_to_equity, 2),
                "Price ($)": info.get('currentPrice', 'N/A')
            }
    except Exception:
        pass
    return None

if st.button("🔍 Initialize Live Filter Scan", type="primary"):
    matches = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    total = len(active_watchlist)
    
    for idx, ticker in enumerate(active_watchlist, 1):
        status_text.text(f"Processing calculations for: {ticker} ({idx}/{total})")
        progress_bar.progress(idx / total)
        
        data = analyze_stock(ticker, max_debt_allowed)
        if data:
            matches.append(data)
        time.sleep(0.1)
        
    status_text.text("🎉 Scan finalized successfully!")
    progress_bar.empty()
    
    st.markdown("### 📊 Qualified Growth Matrix")
    if matches:
        df = pd.DataFrame(matches)
        st.dataframe(
            df.sort_values(by="Calculated PEG", ascending=True),
            use_container_width=True,
            column_config={
                "Trailing P/E": st.column_config.NumberColumn(format="%.2f"),
                "3-Yr Rev CAGR (%)": st.column_config.NumberColumn(format="%.1f%%"),
                "Calculated PEG": st.column_config.NumberColumn(format="%.2f"),
                "Debt/Equity (%)": st.column_config.NumberColumn(format="%.1f%%"),
                "Price ($)": st.column_config.NumberColumn(format="$%.2f")
            }
        )
    else:
        st.info("No companies matched our precise growth-to-valuation parameters today.")
