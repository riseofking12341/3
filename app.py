import streamlit as st
from GoogleNews import GoogleNews
import yfinance as yf
from openai import OpenAI

client = OpenAI()

st.set_page_config(page_title="Avancerad Aktie & Nyhetsanalys", layout="wide")

# --- DESIGN ---
st.markdown(
    """
    <style>
    .stApp {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #f9f9f9;
    }
    .header {
        color: #2c3e50;
        font-weight: 700;
    }
    .subheader {
        color: #34495e;
        font-weight: 600;
        margin-bottom: 10px;
    }
    .fin-metric {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .news-item {
        background-color: #ffffff;
        border-left: 5px solid #2980b9;
        padding: 15px;
        margin-bottom: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .analysis-box {
        background-color: #ecf0f1;
        padding: 15px;
        border-radius: 8px;
        margin-top: 20px;
        font-style: italic;
        color: #2c3e50;
    }
    </style>
    """, unsafe_allow_html=True
)

st.markdown('<h1 class="header">📊 Avancerad Aktie- och Nyhetsanalys</h1>', unsafe_allow_html=True)
st.markdown(
    "<p>Appen hämtar senaste nyheter och bolagsdata, "
    "ger en djup AI-analys av påverkan på aktien – både kort och lång sikt.</p>", unsafe_allow_html=True)
st.markdown("<hr>")

# SIDEBAR
with st.sidebar:
    st.header("Företagsinformation")
    company_name = st.text_input("Företagsnamn", value="Tesla")
    stock_ticker = st.text_input("Aktieticker", value="TSLA")
    max_news = st.slider("Max antal nyheter", 1, 10, 5)
    st.markdown("---")
    st.caption("AI driven av OpenAI GPT-3.5 Turbo")

# HJÄLPFUNKTIONER

def format_large_number(num):
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
        "P/E-tal": info.get('trailingPE', None),
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

def pe_indicator(pe_value):
    """Returnerar procentvärde (max 100), färg och kommentar baserat på PE."""
    if pe_value is None:
        return 0, "gray", "P/E-tal saknas"
    if pe_value <= 10:
        return min(100, pe_value * 10), "green", "Lågt P/E – kan indikera undervärderad aktie"
    elif pe_value <= 25:
        return min(100, (pe_value-10)*6.67), "orange", "Medelhögt P/E – normalt för tillväxtbolag"
    else:
        return 100, "red", "Högt P/E – höga förväntningar, risk för övervärdering"

def analyze_news_with_stock(news_text, stock_ticker):
    system_prompt = (
        "Du är en erfaren finansiell analytiker som analyserar nyheter och bolagsdata. "
        f"Analysera nedanstående nyhetstext och bolagsdata för aktien {stock_ticker}. "
        "Fokusera på sannolik påverkan på aktiekursen – kommer nyheten sannolikt att göra aktien stiga, falla eller vara neutral, och varför? "
        "Ge en tydlig bedömning för både kort och lång sikt."
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
        st.markdown('<h2 class="subheader">📊 Aktieinfo & Nyckeltal</h2>', unsafe_allow_html=True)
        for key, value in stock_data.items():
            with st.expander(f"{key} – Förklaring"):
                st.markdown(f"**{key}:** {value}")
                st.caption(explanations.get(key, "Ingen förklaring tillgänglig."))

        # PE-tal visuellt
        pe_val = stock_data.get("P/E-tal")
        if isinstance(pe_val, (float, int)):
            percent, color, comment = pe_indicator(pe_val)
            st.markdown(f"<b>P/E-tal Indikator:</b> <span style='color:{color}; font-weight:bold'>{comment}</span>", unsafe_allow_html=True)
            st.progress(percent / 100)
        else:
            st.info("P/E-tal saknas för att visa indikator.")

    with col2:
        st.markdown('<h2 class="subheader">📰 Senaste Nyheter</h2>', unsafe_allow_html=True)

        summarized_news = []
        for i, item in enumerate(news_items[:max_news]):
            st.markdown(f'<div class="news-item">', unsafe_allow_html=True)
            st.markdown(f"**{item['title']}**")
            st.markdown(f"<i>{item['date']}</i>")
            st.markdown(f"{item['desc']}")
            with st.expander("Analys av denna nyhet med AI"):
                analysis = analyze_news_with_stock(item['title'] + ". " + item['desc'], stock_ticker)
                st.write(analysis)
                summarized_news.append(analysis)
            st.markdown("</div>", unsafe_allow_html=True)

        # Slutgiltig analys
        if summarized_news:
            final_analysis = final_overall_analysis(stock_data, "\n\n".join(summarized_news))
            st.markdown('<div class="analysis-box">')
            st.markdown(f"### 🤖 Slutgiltig AI-analys\n\n{final_analysis}")
            st.markdown('</div>')
else:
    st.info("Vänligen ange både företagsnamn och aktieticker i sidofältet.")
