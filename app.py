import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from textblob import TextBlob
import requests
from openai import OpenAI
import datetime

# --- API-nycklar ---
OPENAI_API_KEY = "din-openai-nyckel-har"
NEWS_API_KEY = "din-news-api-nyckel-har"

client = OpenAI(api_key=OPENAI_API_KEY)

# --- Funktion: Hämta bolagsdata ---
def get_stock_info(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    return {
        "longName": info.get("longName", "N/A"),
        "sector": info.get("sector", "N/A"),
        "marketCap": info.get("marketCap", 0),
        "trailingPE": info.get("trailingPE", None),
        "forwardPE": info.get("forwardPE", None),
        "priceToBook": info.get("priceToBook", None),
        "dividendYield": info.get("dividendYield", None),
        "earningsGrowth": info.get("earningsQuarterlyGrowth", None),
        "summary": info.get("longBusinessSummary", "")
    }

# --- Funktion: Hämta relaterade nyheter ---
def get_related_news(company_name, sector):
    keywords = [company_name, sector, "supply chain", "trade tariffs", "commodity prices"]
    all_articles = []
    for kw in keywords:
        url = f"https://newsapi.org/v2/everything?q={kw}&apiKey={NEWS_API_KEY}&language=sv"
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            all_articles.extend(data["articles"])
    return all_articles[:5]  # Top 5 nyheter

# --- Funktion: AI-analys av nyheter ---
def analyze_news_with_openai(text):
    prompt = f"Analysera följande nyhet i relation till företagets framtid: {text}. Hur kan detta påverka aktiekursen kortsiktigt och långsiktigt?"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Du är en finansanalytiker."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=400,
        temperature=0.6
    )
    return response.choices[0].message.content

# --- Funktion: Sentimentanalys ---
def sentiment_score(text):
    blob = TextBlob(text)
    return blob.sentiment.polarity

# --- Format för miljardtal ---
def format_market_cap(val):
    if val >= 1e9:
        return f"{val / 1e9:.1f} miljarder"
    elif val >= 1e6:
        return f"{val / 1e6:.1f} miljoner"
    return str(val)

# --- Streamlit UI ---
st.set_page_config(page_title="AI Aktieanalys", layout="wide")
st.title("🔍 AI-baserad aktieanalys")

user_input = st.text_input("Sök företagsnamn eller ticker (ex. TSLA för Tesla):")

if user_input:
    try:
        st.subheader(f"📊 Data för {user_input.upper()}")
        stock_data = get_stock_info(user_input)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Bolagsnamn:** {stock_data['longName']}")
            st.markdown(f"**Sektor:** {stock_data['sector']}")
            st.markdown(f"**Marknadsvärde:** {format_market_cap(stock_data['marketCap'])}")
            st.markdown(f"**P/E (trailing):** {stock_data['trailingPE']}")
            st.markdown(f"**P/E (forward):** {stock_data['forwardPE']}")
        with col2:
            with st.expander("ℹ️ Vad betyder nyckeltalen?"):
                st.markdown("**P/E-tal:** Pris per aktie delat med vinst per aktie. Högt P/E kan innebära hög förväntan på tillväxt.")
                st.markdown("**Price to Book:** Visar marknadens värdering jämfört med företagets bokförda värde.")
                st.markdown("**Earnings Growth:** Hur mycket vinsten växt jämfört med tidigare kvartal.")

            st.markdown(f"**Pris / Bokfört värde:** {stock_data['priceToBook']}")
            st.markdown(f"**Direktavkastning:** {round(stock_data['dividendYield'] * 100, 2) if stock_data['dividendYield'] else 'N/A'}%")
            st.markdown(f"**Vinsttillväxt (QoQ):** {stock_data['earningsGrowth']}")

        st.subheader("🧾 Företagsbeskrivning")
        st.markdown(stock_data['summary'])

        st.subheader("📰 Relaterade nyheter och analys")
        articles = get_related_news(stock_data['longName'], stock_data['sector'])

        for article in articles:
            st.markdown(f"#### [{article['title']}]({article['url']})")
            if article['description']:
                st.markdown(article['description'])
                sentiment = sentiment_score(article['description'])
                st.markdown(f"**🧠 AI-analys:** {analyze_news_with_openai(article['description'])}")
                st.progress((sentiment + 1) / 2)

        st.subheader("📈 Slutanalys")
        st.markdown("Utifrån tillgänglig finansiell data och relevanta nyheter kan det vara värt att gå igenom bolagets senaste kvartalsrapport för att:")
        st.markdown("- Bekräfta vinsttillväxt")
        st.markdown("- Utvärdera risker kopplat till externa händelser (ex. handelsregler, råvarupriser)")
        st.markdown("- Jämföra värdering (P/E) mot konkurrenter i samma sektor")

    except Exception as e:
        st.error(f"Något gick fel: {e}")
