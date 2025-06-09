import streamlit as st
from GoogleNews import GoogleNews
import yfinance as yf
from openai import OpenAI

# Initiera OpenAI-klient
client = OpenAI()

st.set_page_config(page_title="Avancerad Nyhets- och Aktieanalys", layout="wide")

st.title("📈 Avancerad Nyhets- och Aktieanalys med AI")
st.markdown(
    "Denna app hämtar senaste nyheter om ett företag, kopplar ihop med aktiekursdata "
    "och ger AI-baserad kort- och långsiktig investeringsanalys."
)
st.markdown("---")

# Sidebar för input
with st.sidebar:
    st.header("Ange Företagsinfo")
    company_name = st.text_input("Företagsnamn (ex: Tesla)", value="Tesla")
    stock_ticker = st.text_input("Aktieticker (ex: TSLA)", value="TSLA")
    max_news = st.slider("Max antal nyheter att visa", 1, 10, 5)
    st.markdown("---")
    st.caption("Appen använder OpenAI GPT-3.5 Turbo för analys.")

def format_large_number(num):
    """Formatera stora tal till miljarder eller miljoner med svensk notation"""
    try:
        num = float(num)
    except (ValueError, TypeError):
        return "N/A"

    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f} Mdkr"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f} Mkr"
    elif num >= 1_000:
        return f"{num / 1_000:.1f} Tkr"
    else:
        return str(num)

# Förklaringar för finansiella nyckeltal
explanations = {
    "Marknadsvärde": "Totalt värde på bolaget på börsen (aktiekurs x antal aktier).",
    "P/E-tal": "Pris per vinstkrona; hög P/E = höga tillväxtförväntningar.",
    "PEG-tal": "P/E justerat för tillväxt; runt 1 är rättvist värderat.",
    "Utdelning (yield)": "Årlig utdelning i % av aktiekursen.",
    "Beta (volatilitet)": "Aktiens känslighet mot marknadsrörelser (risk).",
    "52-veckors högsta": "Högsta aktiekurs det senaste året.",
    "52-veckors lägsta": "Lägsta aktiekurs det senaste året.",
    "Antal anställda": "Hur många som jobbar på företaget.",
    "Bransch": "Vilken sektor eller industri företaget verkar inom.",
    "Hemort": "Företagets huvudkontor."
}

def fetch_news(company):
    googlenews = GoogleNews(lang='sv', period='7d')
    googlenews.search(company)
    results = googlenews.result()
    return results

def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    data = {
        "Nuvarande pris": info.get('currentPrice', 'N/A'),
        "Marknadsvärde": format_large_number(info.get('marketCap')),
        "P/E-tal": info.get('trailingPE', 'N/A'),
        "PEG-tal": info.get('pegRatio', 'N/A'),
        "Utdelning (yield)": f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "N/A",
        "Beta (volatilitet)": info.get('beta', 'N/A'),
        "52-veckors högsta": info.get('fiftyTwoWeekHigh', 'N/A'),
        "52-veckors lägsta": info.get('fiftyTwoWeekLow', 'N/A'),
        "Antal anställda": info.get('fullTimeEmployees', 'N/A'),
        "Bransch": info.get('industry', 'N/A'),
        "Hemort": info.get('city', 'N/A'),
    }
    return data

def analyze_news_with_stock(news_text, stock_ticker):
    system_prompt = (
        "Du är en erfaren finansiell analytiker som analyserar nyheter och bolagsdata. "
        f"Analysera nedanstående nyhetstext och bolagsdata för aktien {stock_ticker}. "
        "Ge en tydlig bedömning av hur detta påverkar aktiens kortsiktiga och långsiktiga utveckling."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": news_text},
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"AI API fel: {e}"

def final_overall_analysis(stock_data, news_summaries):
    system_prompt = (
        "Du är en skicklig finansiell rådgivare. Baserat på denna sammanfattning av nyheter och företagets finansiella data:\n\n"
        f"Finansiella data:\n{stock_data}\n\n"
        f"Nyhetssammanfattningar:\n{news_summaries}\n\n"
        "Ge en slutgiltig analys om företagets ekonomiska hälsa och huruvida det är värt att gå igenom bolagets kvartalsrapporter för djupare insikt. "
        "Håll svaret koncist men informativt."
    )
    messages = [
        {"role": "system", "content": system_prompt},
    ]
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"AI API fel: {e}"

if company_name and stock_ticker:
    news_items = fetch_news(company_name)
    stock_data = get_stock_data(stock_ticker)

    col1, col2 = st.columns([2, 3])

    with col1:
        st.header(f"📊 Aktiedata för {stock_ticker}")
        for key, value in stock_data.items():
            with st.expander(f"{key} - Förklaring"):
                st.markdown(f"**{key}:** {value}")
                st.caption(explanations.get(key, "Ingen förklaring tillgänglig."))

    with col2:
        st.header(f"📰 Senaste nyheter om {company_name}")
        if not news_items:
            st.write("Inga nyheter hittades.")
        else:
            news_analyses = []
            for idx, item in enumerate(news_items[:max_news]):
                st.markdown(f"### {item['title']}")
                st.write(item['desc'])
                combined_text = item['title'] + " " + item['desc']

                with st.expander("Se AI-driven aktieanalys"):
                    ai_analysis = analyze_news_with_stock(combined_text, stock_ticker)
                    news_analyses.append(ai_analysis)
                    st.markdown(ai_analysis)
                st.markdown("---")

            # Slutgiltig sammanfattning baserat på all nyhetsanalys + finansiell data
            with st.container():
                st.markdown("## 🔍 Slutgiltig Sammanfattande Analys")
                summary = final_overall_analysis(stock_data, "\n\n".join(news_analyses))
                st.markdown(summary)
else:
    st.info("Ange företagets namn och aktieticker i sidomenyn för att starta analysen.")
