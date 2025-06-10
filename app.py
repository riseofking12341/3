import streamlit as st
import yfinance as yf
from GoogleNews import GoogleNews
from openai import OpenAI

# Initialize OpenAI client using your secret API key
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
        if topic and topic != "N/A":
            for keyword in material_keywords:
                topic_query = f"{topic} {keyword}"
                indirect_news += fetch_news(topic_query)
    return direct_news[:5], indirect_news[:5]

def fetch_global_news():
    global_topics = ["global economy", "trade war", "inflation", "interest rates", "geopolitical tension", "oil prices"]
    googlenews = GoogleNews(lang='en', period='7d')
    global_news = []
    for topic in global_topics:
        googlenews.search(topic)
        results = googlenews.results(sort=True)
        global_news += results
    # Remove duplicates by link
    seen_links = set()
    unique_global_news = []
    for article in global_news:
        if article['link'] not in seen_links:
            unique_global_news.append(article)
            seen_links.add(article['link'])
    return unique_global_news[:5]

def analyze_with_ai(company, direct_news, indirect_news, global_news, financials):
    def news_to_text(news_list):
        return "\n".join([f"{n['title']}. {n.get('desc', '')}" for n in news_list])

    direct_text = news_to_text(direct_news)
    indirect_text = news_to_text(indirect_news)
    global_text = news_to_text(global_news)

    message = f"""
You are a financial analyst. Analyze the company {company} with a summary of its financials: {financials}.

Here are recent direct news headlines about the company:
{direct_text}

Here are indirect/industry-related news headlines:
{indirect_text}

And here are relevant global news headlines that might impact the company:
{global_text}

Please provide a clear breakdown of:
- What these direct news items mean for the company’s prospects.
- How the indirect industry news could affect the company.
- The potential impact of the global news on the company’s future.
- Any hidden risks or opportunities you can identify based on this information.
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a financial analyst who gives short, clear, and actionable investment summaries."},
            {"role": "user", "content": message}
        ]
    )
    return response.choices[0].message.content

# Streamlit UI setup
st.set_page_config(page_title="Stock Deep Dive AI", layout="wide")
st.title("📈 AI-Powered Stock Analysis Tool")

company_input = st.text_input("Enter a company's ticker symbol (e.g., TSLA)")

if company_input:
    ticker = company_input.strip().upper()
    info = get_ticker_info(ticker)
    if not info:
        st.error("Error fetching stock data. Please check the symbol.")
    else:
        # Display basic stock info
        st.subheader(f"Basic Info about {info['shortName']}")
        st.markdown(f"**Sector:** {info['sector']}")
        st.markdown(f"**Industry:** {info['industry']}")
        st.markdown(f"**P/E Ratio:** {info['peRatio']}")
        st.markdown(f"**Forward P/E:** {info['forwardPE']}")
        st.markdown(f"**Market Cap:** {info['marketCap']}")
        st.markdown(f"**Dividend Yield:** {info['dividendYield']}")

        with st.expander("📄 Company Description"):
            st.write(info['description'])

        # Fetch news
        direct, indirect = extract_relevant_news(info)
        global_news = fetch_global_news()

        # Show news in UI
        st.subheader("📰 News Analysis")
        st.markdown("### 🔍 Direct News")
        for n in direct:
            st.markdown(f"**{n['title']}**\n{n.get('desc', '')}\n[Read more]({n['link']})")

        st.markdown("### 🌐 Indirect/Industry-related News")
        for n in indirect:
            st.markdown(f"**{n['title']}**\n{n.get('desc', '')}\n[Read more]({n['link']})")

        st.markdown("### 🌍 Global News Affecting Markets")
        for n in global_news:
            st.markdown(f"**{n['title']}**\n{n.get('desc', '')}\n[Read more]({n['link']})")

        # AI analysis
        st.subheader("📊 AI Investment Insight")
        with st.spinner("Analyzing with AI..."):
            ai_analysis = analyze_with_ai(info["shortName"], direct, indirect, global_news, info)
        st.write(ai_analysis)
