# Bharat Equity Research

A small, hostable Indian stock research app. It combines a curated large-company watchlist, fetched market data, calculated price-risk measures, and optional Sarvam AI analysis. This README is the handoff guide for what is implemented, where its data comes from, how to run it, and how to publish and host it.

## Current project status

- The app source, 20-company watchlist, dependency list, setup example, and sample AI brief are in this repository.
- The local repository has a clean commit history on branch `main`; the handoff ZIP includes the repository metadata. Cloud deployment has not been configured.
- The `.env` file is ignored by Git and was excluded from the repository commit. `.env.example` is safe to commit and contains no key.
- Streamlit was not launched in this environment: virtual-environment setup did not bootstrap `pip`, and the subsequent package download stalled. The local `.venv` is incomplete and ignored. Install the requirements in a normal Python environment before running; the hosted service will install them from `requirements.txt`.
- The sample in [`sample_report.md`](sample_report.md) is a real Sarvam response to dated Reliance facts gathered for this project. It demonstrates the analysis flow; it is not live app data.

## What the app does

1. Lets a user choose a company from `companies.csv`.
2. Fetches up to one year of adjusted closing prices and available quote/fundamental fields at runtime.
3. Displays the latest provider price, market cap, available trailing revenue/net income/cash flow/debt fields, and selected valuation/profitability fields.
4. Calculates one-year adjusted-close return, annualized volatility, and maximum drawdown from the fetched history.
5. When the user selects **Generate research brief**, sends the retrieved facts, source label, and retrieval timestamp to Sarvam's `sarvam-105b-conversations` chat model. Sarvam is instructed to use only supplied facts, label unsupported risks as questions to investigate, and avoid buy/sell instructions.

The dashboard caches fetched data for five minutes. Missing provider fields display as `—`. Sarvam is called only after the button is pressed; the dashboard can show market data without making a Sarvam request.

## Data scope and limits

- **Watchlist:** `companies.csv` contains 20 selected large Indian listed companies. It is a curated starter list informed by the Economic Times market-cap screen as of 30 October 2026, not an exact or automatically updated top-20 ranking. The list includes Jio Platforms (NSE symbol JPL), listed on 28 October 2026. The order in the CSV is for display and is not a rank.
- **Live app data:** prices and fundamentals are fetched by `yfinance` from Yahoo Finance. This is an unofficial data feed; quotes may be delayed, rate-limited, incomplete, or unavailable. The app shows the retrieval time and the date range of price history. Check exchange disclosures and company filings for important decisions, and review Yahoo Finance's terms before public or commercial use.
- **AI analysis:** Sarvam sees only the data that the app sends in the request. It does not independently browse or verify prices, filings, results, or news. AI output can still be wrong; review every claim against the supplied figures and primary disclosures.
- **Not included:** news ingestion, company-filing extraction, forecasts, portfolio advice, buy/sell signals, user accounts, or order execution.
- This app is for general research support and does not provide personalized investment advice.

## Run locally

Requires Python 3.10 or later.

### Hand off to another Windows computer

Send the repository ZIP. On the recipient's computer, install Python 3.10+ with the Python launcher (`py`) enabled, extract the ZIP, and double-click `run_windows.bat`. It creates an isolated environment, installs the packages on first launch, and opens the app in that computer's browser. An internet connection is required for setup and market-data retrieval. The recipient can add their own Sarvam key to `.env` for AI briefs; the dashboard works without one.

The ZIP does not contain your `.env`, API key, Python environment, or cached packages. Each recipient supplies their own key. This is a computer-run app rather than a hosted public URL; for a shareable online URL, use the Streamlit Community Cloud steps below.

For a manual setup instead of the launcher:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Add your Sarvam key to `.env` as `SARVAM_API_KEY=...`, then run:

```powershell
streamlit run app.py
```

The dashboard can display fetched prices and fundamentals without calling Sarvam. The Sarvam request runs only when you select **Generate research brief**. Put your own `SARVAM_API_KEY` in `.env` locally or in the host's secrets settings. Never commit `.env` or place a key in source code.

## Hosting on Streamlit Community Cloud

1. Create an empty GitHub repository. This local folder already has a `main` branch and an initial commit; do not run `git init` again. Add the remote and push:

   ```powershell
   git remote add origin https://github.com/<your-user>/bharat-equity-research.git
   git push -u origin main
   ```

2. Create a Streamlit Community Cloud app from that repository, with `app.py` as the entry point.
3. Add `SARVAM_API_KEY` in the app's **Secrets** settings. Never commit `.env` or paste the key into source code.
4. Deploy. `requirements.txt` installs the dependencies.

## Sources

- [NSE Nifty 50 index reference](https://www.nseindia.com/static/products-services/indices-nifty50-index)
- [Economic Times market-cap screen](https://economictimes.indiatimes.com/markets/stock-screener/top-companies-by-market-cap/screens/scrid-3033)
- [yfinance project and data-use notice](https://github.com/ranaroussi/yfinance)
- [NSE issue information for Jio Platforms (JPL)](https://www.nseindia.com/market-data/issue-information?series=EQ&symbol=JPL&type=Active)
- [Reliance FY2025-26 results release](https://www.ril.com/sites/default/files/2026-04/24042026_Media_Release_RIL_Q4_FY2025-26_Financial_and_Operational_Performance.pdf)
- [Reliance historical prices via Investing.com](https://in.investing.com/equities/reliance-industries-historical-data)
- [Sarvam API documentation](https://docs.sarvam.ai/api/getting-started/welcome)
