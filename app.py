import streamlit as st
import yfinance as yf
import requests
from datetime import datetime, timedelta
import openai
import os
import plotly.graph_objects as go
from textblob import TextBlob

# Hämta OpenAI-nyckel från secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]
NEWS_API_KEY = st.secrets["NEWS_API_KEY"]

st.set_page_config(page_title="AI-Bolagsanalys", layout="wide")
st.title("🔍 AI-Drivna Aktieinsikter")
st.markdown("Ge små investerare ett *unfair advantage* på börsen. Få direkt och indirekt nyhetsanalys, viktiga nyckeltal och framtidspotential.")

# Indata från användare
company_name = st.text_input("Ange ett företagsnamn (t.ex. Tesla, Astor, Volvo)")
if not company_name:
    st.stop()

# Hämta ticker med yfinance
@st.cache_data(show_spinner=False)
def get_ticker_symbol(company_name):
    try:
        return yf.Ticker(company_name).info['symbol']
    except:
        try:
            data = yf.Ticker(company_name).info
            return data.get('symbol', None)
        except:
            return None

stock_ticker = get_ticker_symbol(company_name)
if not stock_ticker:
    st.error("Kunde inte hitta ticker för bolaget.")
    st.stop()

col1, col2 = st.columns(2)

# Hämta aktiedata och nyckeltal
@st.cache_data(show_spinner=False)
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    return {
        "P/E": info.get("trailingPE"),
        "PEG": info.get("pegRatio"),
        "Marknadsvärde": info.get("marketCap"),
        "Bransch": info.get("sector"),
        "Material": info.get("longBusinessSummary", "").lower()
    }

with col1:
    st.subheader("Nyckeltal")
    stock_data = get_stock_data(stock_ticker)
    st.metric("P/E-tal", round(stock_data["P/E"], 2) if stock_data["P/E"] else "-")
    st.metric("PEG-tal", round(stock_data["PEG"], 2) if stock_data["PEG"] else "-")
    if stock_data["Marknadsvärde"]:
        cap = stock_data["Marknadsvärde"] / 1e9
        st.metric("Marknadsvärde", f"{cap:.1f} miljarder USD")

    with st.expander("Vad betyder dessa nyckeltal?"):
        st.markdown("**P/E-tal:** Pris/Vinst per aktie. Högt värde kan betyda övervärderad aktie.")
        st.markdown("**PEG-tal:** Tar tillväxt i beaktning. Lågt värde kan innebära bra köpläge.")

# Direkt nyhetssökning
@st.cache_data(show_spinner=False)
def fetch_direct_news(company):
    today = datetime.now().date()
    from_date = today - timedelta(days=7)
    url = f"https://newsapi.org/v2/everything?q={company}&from={from_date}&sortBy=publishedAt&apiKey={NEWS_API_KEY}&language=sv"
    response = requests.get(url)
    return response.json().get("articles", [])

# Indirekt nyhetssökning via material och bransch
@st.cache_data(show_spinner=False)
def fetch_indirect_news(company_info):
    keywords = []
    if company_info["Bransch"]:
        keywords.append(company_info["Bransch"])
    if "carbon" in company_info["Material"]:
        keywords.append("kolfiber")
    if "steel" in company_info["Material"]:
        keywords.append("ståltullar")
    if "semiconductor" in company_info["Material"]:
        keywords.append("chip-politik")

    query = " OR ".join(keywords)
    if not query:
        return []

    today = datetime.now().date()
    from_date = today - timedelta(days=7)
    url = f"https://newsapi.org/v2/everything?q={query}&from={from_date}&sortBy=publishedAt&apiKey={NEWS_API_KEY}&language=sv"
    response = requests.get(url)
    return response.json().get("articles", [])

# AI-analys
@st.cache_data(show_spinner=False)
def ai_news_insight(news_list, company_name):
    prompts = [f"Hur kan denna nyhet påverka {company_name}s aktiekurs? {item['title']} - {item['description']}" for item in news_list]
    summaries = []
    for prompt in prompts:
        try:
            res = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            summaries.append(res.choices[0].message.content)
        except:
            summaries.append("Kunde inte analysera nyheten just nu.")
    return summaries

# Visa nyheter
with col2:
    st.subheader("📢 Relevanta Nyheter")
    direct_news = fetch_direct_news(company_name)
    indirect_news = fetch_indirect_news(stock_data)

    all_news = direct_news + indirect_news
    if not all_news:
        st.info("Inga relevanta nyheter hittades.")
    else:
        insights = ai_news_insight(all_news, company_name)
        for i, item in enumerate(all_news):
            with st.expander(item['title']):
                st.markdown(f"🗞️ [{item['source']['name']}]({item['url']})")
                st.write(item['description'])
                st.markdown(f"**AI-analys:** {insights[i]}")

# Slutanalys
st.subheader("🧠 Slutgiltig analys")
final_prompt = f"Givet dessa nyckeltal och bransch: {stock_data}, är det värt att som investerare fördjupa sig i {company_name}s kvartalsrapporter?" 
try:
    completion = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": final_prompt}]
    )
    st.success(completion.choices[0].message.content)
except:
    st.warning("Kunde inte generera slutanalys just nu.")
