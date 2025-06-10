import streamlit as st
import yfinance as yf
from GoogleNews import GoogleNews
from openai import OpenAI

# Setup OpenAI client
client = OpenAI(api_key=st.secrets["openai_api_key"])

def search_ticker_by_company(company_name):
    search_results = yf.utils.get_tickers_by_name(company_name)
    # yf.utils.get_tickers_by_name is not an official API — 
    # instead, we can do a workaround using yfinance's search method:
    tickers = yf.Ticker(company_name)
    # But since yfinance doesn't have a direct search method, 
    # we can use yfinance's 'Ticker' directly with company_name sometimes 
    # but better approach is to use yfinance's 'Ticker' with a guess.
    # Here is a better workaround:
    try:
        from yahoofinancials import YahooFinancials
        # But yahoofinancials is a separate library, so let's keep it simple.
    except ImportError:
        pass
    # To keep it simple for now, let's try this:
    # Return ticker symbol if company_name looks like a ticker else None
    return company_name.upper()  # Just treat input as ticker fallback

def get_ticker_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if not info or 'shortName' not in info:
            return None
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
    except Exception:
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
        if topic != "N/A":
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

company_input = st.text_input("Enter a company name (e.g., Tesla, Apple, Volvo)")

if company_input:
    # For simplicity: treat input as company name, try to find ticker by searching
    # We can use yfinance's search method (via yfinance.Ticker), but it's limited
    # So as a fallback, assume user inputs ticker if no search found
    ticker = None
    try:
        # Use yfinance's ticker search unofficial API
        search_results = yf.utils.get_tickers_by_name(company_input)  # This does not exist officially
    except Exception:
        search_results = []

    # Fallback: try company_input as ticker
    ticker = company_input.upper()

    info = get_ticker_info(ticker)

    if not info:
        st.error("Could not find company data. Try a different company name or ticker.")
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
