import streamlit as st
import yfinance as yf
import pandas as pd
from GoogleNews import GoogleNews
from openai import OpenAI
import datetime

# Setup OpenAI client
client = OpenAI(api_key=st.secrets["openai_api_key"])

def get_ticker_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "shortName": info.get("shortName", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "peRatio": info.get("trailingPE", "N/A"),
            "marketCap": info.get("marketCap", "N/A"),
            "forwardPE": info.get("forwardPE", "N/A"),
            "dividendYield": info.get("dividendYield", "N/A"),
            "description": info.get("longBusinessSummary", "N/A")
        }
    except Exception as e:
        return None

def fetch_news(query):
    googlenews = GoogleNews(lang='en', period='7d')
    googlenews.search(query)
    return googlenews.results(sort=True)

def extract_relevant_news(company_info):
    direct_news = fetch_news(company_info["shortName"])
    indirect_queries = [company_info["sector"], company_info["industry"]]

    material_keywords = ["raw material", "supply chain", "tariff", "shortage"]
    indirect_news = []
    for topic in indirect_queries:
        for keyword in material_keywords:
            topic_query = f"{topic} {keyword}"
            indirect_news += fetch_news(topic_query)
    return direct_news[:5], indirect_news[:5]

def analyze_with_ai(company, direct_news, indirect_news, financials):
    news_text = "\n".join([n["title"] + ". " + n["desc"] for n in direct_news + indirect_news])
    message = f"""
You are a financial analyst. Analyze the potential upside and downside of the company {company}. 
Here is a summary of the financials: {financials}. 
And here are recent news headlines:
{news_text}

Explain how these factors may affect the stock's future and if there are hidden risks or opportunities based on indirect news.
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a financial analyst who gives short and clear investment summaries."},
            {"role": "user", "content": message}
        ]
    )
    return response.choices[0].message.content

# Streamlit UI
st.set_page_config(page_title="Stock Deep Dive AI", layout="wide")
st.title("📈 AI-Powered Stock Analysis Tool")

company_input = st.text_input("Enter a company's ticker symbol (e.g., TSLA)")

if company_input:
    info = get_ticker_info(company_input)
    if not info:
        st.error("Error fetching stock data. Please check the symbol.")
    else:
        st.subheader(f"Basic Info about {info['shortName']}")
        st.markdown(f"**Sector:** {info['sector']}")
        st.markdown(f"**Industry:** {info['industry']}")
        st.markdown(f"**P/E Ratio:** {info['peRatio']}")
        st.markdown(f"**Forward P/E:** {info['forwardPE']}")
        st.markdown(f"**Market Cap:** {info['marketCap']}")
        st.markdown(f"**Dividend Yield:** {info['dividendYield']}")

        with st.expander("📄 Company Description"):
            st.write(info['description'])

        st.subheader("📰 News Analysis")
        direct, indirect = extract_relevant_news(info)

        st.markdown("### 🔍 Direct News")
        for n in direct:
            st.markdown(f"**{n['title']}**\n{n['desc']}\n[Read more]({n['link']})")

        st.markdown("### 🌐 Indirect/Industry-related News")
        for n in indirect:
            st.markdown(f"**{n['title']}**\n{n['desc']}\n[Read more]({n['link']})")

        st.subheader("📊 AI Investment Insight")
        ai_analysis = analyze_with_ai(info["shortName"], direct, indirect, info)
        st.write(ai_analysis)
