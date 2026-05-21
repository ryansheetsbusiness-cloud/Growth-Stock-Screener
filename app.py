import streamlit as st
import pandas as pd
import yfinance as yf
import time

st.set_page_config(page_title="Growth Stock Hunter", page_icon="🚀", layout="wide")

st.title("🚀 Multi-Index Growth Stock Hunter")
st.subheader("Custom Built Screener: Auto-Calculating PEG and CAGR Profiles")

# --- TICKER DATABASES ---
# --- TICKER DATABASES (EXPANDED GROWTH WATCHLISTS) ---
russell_1000_watchlist = [
    # Mega-Cap Tech & AI Infrastructure
    "MSFT", "AAPL", "NVDA", "AMZN", "META", "GOOGL", "AVGO", "AMD", "NFLX", "QCOM", "ORCL", "CRM", "INTU", "NOW",
    # Semiconductors & High-Growth Tech
    "SMCI", "ASML", "LRCX", "KLAC", "PANW", "CRWD", "FTNT", "DDOG", "NET", "SNOW", "PLTR", "TST", "MDB",
    # Weight-Loss, Biotech & Healthcare Innovators
    "LLY", "NVO", "REGN", "VRTX", "ISRG", "BSX", "ABV",
    # High-Growth Financials, Visa/MC Alternatives & Payments
    "V", "MA", "AXP", "SQ", "PYPL", "COIN", "HOOD", "NU",
    # Discretionary Momentum, Retail & Consumer Giants
    "COST", "CMG", "MELI", "UBER", "ABNB", "TSLA", "DECK", "NKE", "LULU",
    # Industrial, Aerospace & Energy Innovators
    "GE", "CAT", "ETN", "PH", "TDG", "CEG", "VST", "DE"
]

russell_2000_watchlist = [
    # Energy, Clean Tech & Power Infrastructure
    "VRT", "AMPS", "NXT", "SHLS", "CLNE", "GEOS", 
    # Consumer & Beverage Compounders
    "CELH", "ELF", "CROX", "SG", "WING", "LOCO", "BROS", "CAVA",
    # Medical Technology, Defense & Aerospace
    "AXON", "HALO", "AAON", "PODD", "LNTH", "SWAV", "NTRA", "HAE",
    # Software, Enterprise SaaS & Cybersecurity
    "STEP", "KNSL", "FIX", "SPSC", "QLYS", "APPS", "ALTR", "BASE", "PRO", "YEXT",
    # Niche Industrial & FinTech Disruption
    "POWI", "UPST", "LMND", "SOFI", "LC", "FLYV", "MEDP"
]

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
