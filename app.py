# stock_analysis_app.py
import streamlit as st
from yfinance import Ticker
from GoogleNews import GoogleNews
import pandas as pd
import openai
import os

# -- Configuration and API keys --
openai.api_key = st.secrets.get("openai_api_key") or os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Stock Analyzer", layout="wide")
st.title("📈 AI-Powered Stock Analysis")

# -- Input: Company name --
company_name = st.text_input("Enter a company name (e.g. Tesla)", value="Tesla").strip()
if company_name:
    # -- 1. Find stock ticker using GPT-4 --
    try:
        ticker_resp = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides stock ticker symbols."},
                {"role": "user", "content": f"What is the stock ticker symbol for the company {company_name}?"}
            ]
        )
        ticker_symbol = ticker_resp['choices'][0]['message']['content'].split()[0].upper().strip()
    except Exception as e:
        st.error("Error finding ticker: " + str(e))
        ticker_symbol = None

    if ticker_symbol:
        st.write(f"**Ticker:** {ticker_symbol}")

        # -- 2. Fetch recent news (direct) --
        googlenews = GoogleNews(lang='en', period='7d')
        googlenews.search(company_name)
        direct_news = googlenews.results()
        # Extract relevant fields
        direct_articles = []
        for item in direct_news:
            title = item.get("title")
            media = item.get("media")
            date = item.get("date")
            link = item.get("link")
            direct_articles.append({"title": title, "media": media, "date": date, "link": link})

        # -- 3. Fetch related topics using GPT-4 for indirect news --
        try:
            topics_resp = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert in business research."},
                    {"role": "user", "content": f"Suggest 3-5 related industry topics or supply-chain terms for the company {company_name} (comma-separated)."}
                ]
            )
            topics_list = topics_resp['choices'][0]['message']['content']
            # Parse comma-separated list
            related_topics = [t.strip() for t in topics_list.replace(".", "").split(",") if t.strip()]
        except Exception:
            related_topics = []

        # -- 4. Fetch news on related topics (indirect) --
        indirect_articles = []
        for topic in related_topics:
            googlenews.search(topic)
            for item in googlenews.results():
                indirect_articles.append({
                    "title": item.get("title"),
                    "media": item.get("media"),
                    "date": item.get("date"),
                    "link": item.get("link")
                })
            googlenews.clear()

        # -- UI: News Overview --
        st.header("📰 News Overview")
        if direct_articles:
            st.subheader("Direct News (Company-specific)")
            for art in direct_articles:
                st.markdown(f"- **{art['date']}** – [{art['title']}]({art['link']}) ({art['media']})")
        else:
            st.write("No direct news found.")

        if related_topics:
            st.subheader("Indirect News (Related Topics)")
            for art in indirect_articles:
                st.markdown(f"- **{art['date']}** – [{art['title']}]({art['link']}) ({art['media']})")
        else:
            st.write("No indirect topics or news found.")

        # -- 5. Fetch financial metrics with yfinance --
        try:
            ticker = Ticker(ticker_symbol)
            info = ticker.info
        except Exception as e:
            st.error("Error fetching financial data: " + str(e))
            info = {}

        # Extract metrics
        market_cap = info.get("marketCap")
        pe_ratio = info.get("trailingPE")
        eps = info.get("trailingEps")
        roe = info.get("returnOnEquity")
        debt = info.get("totalDebt")

        # Format large numbers (e.g., market cap in billions)
        def fmt_number(x):
            if x is None:
                return "N/A"
            for unit in [("T", 1e12), ("B", 1e9), ("M", 1e6), ("k", 1e3)]:
                if abs(x) >= unit[1]:
                    return f"{x/unit[1]:.2f}{unit[0]}"
            return str(x)

        market_cap_str = fmt_number(market_cap) if market_cap else "N/A"
        pe_str = f"{pe_ratio:.2f}" if pe_ratio else "N/A"
        eps_str = f"{eps:.2f}" if eps else "N/A"
        roe_str = f"{roe*100:.1f}%" if roe else "N/A"
        debt_str = fmt_number(debt) if debt else "N/A"

        # -- UI: Financial Metrics --
        st.header("💰 Financial Metrics")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Market Cap", market_cap_str)
        col2.metric("P/E Ratio", pe_str)
        col3.metric("EPS (TTM)", eps_str)
        col4.metric("Return on Equity (ROE)", roe_str)
        col5.metric("Total Debt", debt_str)

        # Expanders for definitions
        with st.expander("What is Market Cap?"):
            st.write("Market capitalization (market cap) is the total value of all a company's outstanding shares. It’s calculated as share price × total shares:contentReference[oaicite:8]{index=8}.")
        with st.expander("What is P/E Ratio?"):
            st.write("The Price/Earnings (P/E) ratio equals the stock price divided by earnings per share:contentReference[oaicite:9]{index=9}. A lower P/E can imply a stock is undervalued, while a higher P/E may suggest high growth expectations.")
        with st.expander("What is EPS?"):
            st.write("Earnings Per Share (EPS) is the portion of a company’s profit allocated to each outstanding share. It’s net income divided by shares outstanding:contentReference[oaicite:10]{index=10}.")
        with st.expander("What is ROE?"):
            st.write("Return on Equity (ROE) measures profitability relative to shareholder equity (net income ÷ equity):contentReference[oaicite:11]{index=11}. A higher ROE means the company is efficient at generating profits from its equity.")
        with st.expander("What is Total Debt?"):
            st.write("Total Debt is the sum of a company’s short- and long-term interest-bearing liabilities. High debt levels can affect financial risk and leverage.")

        # -- 6. AI Insights (GPT-4 Analysis) --
        st.header("🤖 AI Insights")
        ai_prompt = f"""
        You are a financial analyst assistant. The company is **{company_name}** ({ticker_symbol}). 
        Recent direct news headlines:\n""" + "\n".join([f"- {art['title']}" for art in direct_articles[:5]]) + \
        "\nIndirect news topics: " + ", ".join(related_topics[:5]) + \
        f"\nFinancial metrics: Market Cap {market_cap_str}, P/E {pe_str}, EPS {eps_str}, ROE {roe_str}, Debt {debt_str}.\n" + \
        "Based on this information, write an analysis structured with sections for **Risk Factors**, **Upside Potential**, **Macro Events** to watch, and a **Final Verdict** on the investment outlook."
        try:
            analysis_resp = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert stock analysis assistant."},
                    {"role": "user", "content": ai_prompt}
                ]
            )
            analysis_text = analysis_resp['choices'][0]['message']['content']
        except Exception as e:
            analysis_text = "Error running AI analysis: " + str(e)

        # Display the AI analysis (which includes risk, upside, macro, verdict)
        st.markdown(analysis_text)
