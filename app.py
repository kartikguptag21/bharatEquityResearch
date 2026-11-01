import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st
import yfinance as yf

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / ".sarvam_packages"))


def load_local_env():
    """Load the local .env file without requiring another package."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        name, separator, value = line.partition("=")
        if separator and name.strip() and value.strip():
            os.environ.setdefault(name.strip(), value.strip().strip("\"'"))


def sarvam_key():
    load_local_env()
    key = os.environ.get("SARVAM_API_KEY", "").strip()
    if key:
        return key
    try:
        return str(st.secrets.get("SARVAM_API_KEY", "")).strip()
    except Exception:
        return ""


@st.cache_data(ttl=300, show_spinner=False)
def get_company_data(symbol):
    ticker = yf.Ticker(symbol)
    history = ticker.history(period="1y", auto_adjust=True, actions=False)
    if history.empty:
        raise ValueError("No price history was returned for this symbol.")

    try:
        info = ticker.get_info()
    except Exception:
        info = {}

    close = history["Close"].dropna()
    returns = close.pct_change().dropna()
    high = close.cummax()
    drawdown = (close / high - 1).min() if not close.empty else None
    current = info.get("currentPrice") or info.get("regularMarketPrice") or float(close.iloc[-1])
    prior_close = info.get("previousClose")
    if not prior_close and len(close) > 1:
        prior_close = float(close.iloc[-2])

    metrics = {
        "company": info.get("longName") or info.get("shortName") or symbol,
        "symbol": symbol,
        "sector": info.get("sector", "Not reported"),
        "industry": info.get("industry", "Not reported"),
        "currency": info.get("currency", "INR"),
        "price": current,
        "previous_close": prior_close,
        "market_cap": info.get("marketCap"),
        "revenue_ttm": info.get("totalRevenue"),
        "net_income_ttm": info.get("netIncomeToCommon"),
        "free_cash_flow_ttm": info.get("freeCashflow"),
        "operating_cash_flow_ttm": info.get("operatingCashflow"),
        "total_debt": info.get("totalDebt"),
        "cash_and_equivalents": info.get("totalCash"),
        "trailing_pe": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "price_to_book": info.get("priceToBook"),
        "return_on_equity": info.get("returnOnEquity"),
        "profit_margin": info.get("profitMargins"),
        "revenue_growth": info.get("revenueGrowth"),
        "debt_to_equity": info.get("debtToEquity"),
        "dividend_yield": info.get("dividendYield"),
        "52w_high": info.get("fiftyTwoWeekHigh"),
        "52w_low": info.get("fiftyTwoWeekLow"),
        "one_year_adjusted_return": float(close.iloc[-1] / close.iloc[0] - 1) if len(close) > 1 else None,
        "annualized_volatility": float(returns.std() * (252**0.5)) if len(returns) > 1 else None,
        "max_drawdown": float(drawdown) if drawdown is not None else None,
        "history_start": close.index[0].strftime("%Y-%m-%d"),
        "history_end": close.index[-1].strftime("%Y-%m-%d"),
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "Yahoo Finance via yfinance (unofficial; may be delayed or incomplete)",
    }

    history = history[["Close"]].rename(columns={"Close": "Adjusted close"})
    return metrics, history


def fmt_number(value, digits=2):
    if value is None or pd.isna(value):
        return "—"
    return f"{value:,.{digits}f}"


def fmt_percent(value):
    if value is None or pd.isna(value):
        return "—"
    return f"{value * 100:.1f}%"


def fmt_market_cap(value, currency):
    if value is None or pd.isna(value):
        return "—"
    if currency == "INR":
        return f"₹{value / 1e7:,.0f} crore"
    return f"{currency} {value:,.0f}"


def sarvam_analysis(metrics, question):
    key = sarvam_key()
    if not key:
        raise RuntimeError("Add SARVAM_API_KEY to your local .env file or app secrets.")
    from sarvamai import SarvamAI

    client = SarvamAI(api_subscription_key=key)
    evidence = json.dumps(metrics, ensure_ascii=False, indent=2, default=str)
    response = client.chat.completions(
        model="sarvam-105b-conversations",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an equity research assistant. Analyze only the supplied data. "
                    "Do not invent current facts, filings, news, or numbers. State when data is missing. "
                    "Separate observed facts from interpretation. Discuss business quality, financial "
                    "strengths, risks, valuation context, and questions for further research. State a "
                    "company-specific risk only when supplied data supports it; otherwise list it as "
                    "an unverified question to investigate. Do not infer facts from background knowledge. "
                    "give a buy/sell instruction or personalized investment advice. Mention the data "
                    "source and retrieval time in your response."
                ),
            },
            {
                "role": "user",
                "content": f"User's research question: {question}\n\nCompany data (JSON):\n{evidence}",
            },
        ],
        temperature=0.2,
        max_tokens=1200,
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Sarvam returned an empty reply. Please try again.")
    return content


st.set_page_config(page_title="Bharat Equity Research", page_icon="📊", layout="wide")
st.title("Bharat Equity Research")
st.caption("Indian large-company snapshots with evidence-led Sarvam AI analysis")

companies = pd.read_csv(ROOT / "companies.csv")
company_by_label = {
    f"{row.company} · {row.symbol.replace('.NS', '')}": row.symbol
    for row in companies.itertuples()
}

with st.sidebar:
    st.header("Company")
    selected_label = st.selectbox("Choose a listed company", list(company_by_label))
    symbol = company_by_label[selected_label]
    st.caption("Large-company watchlist; membership and rankings can change.")
    st.markdown("[NSE Nifty 50 reference](https://www.nseindia.com/static/products-services/indices-nifty50-index)")

try:
    with st.spinner("Loading recent price history and company metrics…"):
        metrics, history = get_company_data(symbol)
except Exception as exc:
    st.error(f"Could not load data for {symbol}: {exc}")
    st.info("Try again later or select another company. The price feed may be delayed or temporarily unavailable.")
    st.stop()

st.subheader(f"{metrics['company']} ({symbol.replace('.NS', '')})")
st.caption(f"{metrics['sector']} · {metrics['industry']} · Data retrieved {metrics['retrieved_at_utc']} UTC")

one_day = None
if metrics["previous_close"]:
    one_day = metrics["price"] / metrics["previous_close"] - 1
cols = st.columns(5)
cols[0].metric("Latest price", f"{metrics['currency']} {fmt_number(metrics['price'])}", fmt_percent(one_day) if one_day is not None else None)
cols[1].metric("Market cap", fmt_market_cap(metrics["market_cap"], metrics["currency"]))
cols[2].metric("Trailing P/E", fmt_number(metrics["trailing_pe"]))
cols[3].metric("Revenue growth", fmt_percent(metrics["revenue_growth"]))
cols[4].metric("Return on equity", fmt_percent(metrics["return_on_equity"]))

left, right = st.columns([1.5, 1])
with left:
    st.subheader("Price history · 1 year")
    st.line_chart(history, height=320)
with right:
    st.subheader("More fundamentals")
    detail_rows = [
        ("Revenue (TTM)", fmt_market_cap(metrics["revenue_ttm"], metrics["currency"])),
        ("Net income (TTM)", fmt_market_cap(metrics["net_income_ttm"], metrics["currency"])),
        ("Free cash flow (TTM)", fmt_market_cap(metrics["free_cash_flow_ttm"], metrics["currency"])),
        ("Operating cash flow (TTM)", fmt_market_cap(metrics["operating_cash_flow_ttm"], metrics["currency"])),
        ("Total debt", fmt_market_cap(metrics["total_debt"], metrics["currency"])),
        ("Cash and equivalents", fmt_market_cap(metrics["cash_and_equivalents"], metrics["currency"])),
        ("Forward P/E", fmt_number(metrics["forward_pe"])),
        ("Price to book", fmt_number(metrics["price_to_book"])),
        ("Profit margin", fmt_percent(metrics["profit_margin"])),
        ("Debt to equity", fmt_number(metrics["debt_to_equity"], 1)),
        ("Dividend yield", fmt_percent(metrics["dividend_yield"])),
        ("52-week range", f"{fmt_number(metrics['52w_low'])} – {fmt_number(metrics['52w_high'])}"),
        ("1-year adjusted return", fmt_percent(metrics["one_year_adjusted_return"])),
        ("Annualized volatility", fmt_percent(metrics["annualized_volatility"])),
        ("Maximum drawdown", fmt_percent(metrics["max_drawdown"])),
    ]
    st.dataframe(pd.DataFrame(detail_rows, columns=["Metric", "Value"]), hide_index=True, use_container_width=True)

st.subheader("Ask Sarvam to analyze this company")
question = st.text_input("Research question", "Summarize the company's financial strengths, key risks, and valuation context.")
if st.button("Generate research brief", type="primary"):
    try:
        with st.spinner("Sarvam is reviewing the available data…"):
            st.session_state["research_brief"] = sarvam_analysis(metrics, question)
    except Exception as exc:
        st.error(f"Sarvam request failed: {exc}")
if st.session_state.get("research_brief"):
    st.markdown(st.session_state["research_brief"])

with st.expander("Data sources and limitations"):
    st.write(f"Price history and company metrics: {metrics['source']}.")
    st.write(f"Price history covers {metrics['history_start']} through {metrics['history_end']}. Provider data can be delayed, missing, or revised; verify important figures against company filings and exchange disclosures.")
    st.write("This tool provides general research support, not investment advice. Sarvam analyzes the data passed to it and does not independently verify it.")
