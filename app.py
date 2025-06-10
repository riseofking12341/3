import streamlit as st
import yfinance as yf
from GoogleNews import GoogleNews
from openai import OpenAI

client = OpenAI(api_key=st.secrets["openai_api_key"])

def get_company_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "shortName": info.get("shortName", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "description": info.get("longBusinessSummary", "N/A")
        }
    except Exception:
        return None

def fetch_news(query):
    googlenews = GoogleNews(lang='en', period='7d')
    googlenews.search(query)
    return googlenews.results(sort=True)

def analyze_with_ai(company_name, news_list, company_info):
    news_text = "\n".join([f"{n['title']}: {n['desc']}" for n in news_list[:10]])
    prompt = f"""
You are a financial analyst. Based on the following company info:

Name: {company_name}
Sector: {company_info.get('sector', 'N/A')}
Industry: {company_info.get('industry', 'N/A')}
Description: {company_info.get('description', 'N/A')}

And these recent news headlines and summaries:

{news_text}

Provide a clear and concise analysis of what this means for the company, including risks and opportunities.
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful financial analyst."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

st.title("Simple AI Stock News Analyzer")

company_name = st.text_input("Enter the company name (e.g. Tesla, Apple, Volvo)")

ticker = st.text_input("Enter the ticker symbol (optional, e.g. TSLA, AAPL)")

if company_name:
    news = fetch_news(company_name)
    st.subheader(f"News for {company_name}")
    for n in news[:10]:
        st.markdown(f"**{n['title']}**  \n{n['desc']}  \n[Read more]({n['link']})")

    if ticker:
        info = get_company_info(ticker)
        if info:
            st.subheader(f"Company info for ticker: {ticker}")
            st.write(info)
        else:
            st.warning("Could not fetch company info for this ticker.")
    else:
        info = {"shortName": company_name, "sector": "N/A", "industry": "N/A", "description": "N/A"}

    if st.button("Run AI Analysis"):
        with st.spinner("Analyzing news and company info..."):
            analysis = analyze_with_ai(company_name, news, info)
            st.subheader("AI Analysis")
            st.write(analysis)
