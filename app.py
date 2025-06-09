import streamlit as st
import openai
import yfinance as yf
import datetime
import requests
import numpy as np
import pandas as pd
from textblob import TextBlob  # För enkel sentimentanalys, installera med pip install textblob
import plotly.graph_objects as go
import plotly.express as px

# --- KONFIGURATION ---
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- Funktioner ---

def format_large_number(num):
    """Formaterar stora tal till miljarder/miljoner."""
    try:
        num = float(num)
        if num >= 1e12:
            return f"{num / 1e12:.2f} T"
        elif num >= 1e9:
            return f"{num / 1e9:.2f} miljarder"
        elif num >= 1e6:
            return f"{num / 1e6:.2f} miljoner"
        elif num >= 1e3:
            return f"{num / 1e3:.2f} tusen"
        else:
            return f"{num:.2f}"
    except:
        return "N/A"

def fetch_company_data(ticker):
    """Hämtar finansiella data från yfinance."""
    stock = yf.Ticker(ticker)
    info = stock.info

    data = {
        "Namn": info.get("longName", "N/A"),
        "Ticker": ticker,
        "Marknadsvärde": format_large_number(info.get("marketCap", 0)),
        "P/E": info.get("trailingPE", "N/A"),
        "PEG": info.get("pegRatio", "N/A"),
        "Beta": info.get("beta", "N/A"),
        "Skuldsättningsgrad": info.get("debtToEquity", "N/A"),
        "Direktavkastning (%)": info.get("dividendYield", 0)*100 if info.get("dividendYield") else "N/A",
        "Senaste kvartalsrapport": info.get("lastFiscalYearEnd", "N/A"),
        "Aktuell kurs": info.get("regularMarketPrice", "N/A"),
        "52v hög": info.get("fiftyTwoWeekHigh", "N/A"),
        "52v låg": info.get("fiftyTwoWeekLow", "N/A"),
    }
    return data

def fetch_news(ticker):
    """Mockup nyhetsfunktion - byt till riktig RSS eller nyhets-API."""
    # Exempel RSS URL från Yahoo Finance
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
    try:
        resp = requests.get(url)
        from xml.etree import ElementTree
        root = ElementTree.fromstring(resp.content)
        items = root.findall(".//item")
        news = []
        for item in items[:10]:
            title = item.find("title").text
            desc = item.find("description").text
            pubDate = item.find("pubDate").text
            news.append({"title": title, "desc": desc, "date": pubDate})
        return news
    except Exception as e:
        return []

def sentiment_analysis(text):
    """Gör enkel sentimentanalys med TextBlob."""
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.1:
        return "Positiv", polarity
    elif polarity < -0.1:
        return "Negativ", polarity
    else:
        return "Neutral", polarity

def ai_stock_analysis(news_summary, financial_data):
    """Använder OpenAI för att analysera nyheter och finansdata."""
    prompt = f"""
    Du är en erfaren aktieanalytiker.
    Här är kort nyhetssammanfattning: {news_summary}
    Här är bolagets nyckeltal:
    Marknadsvärde: {financial_data['Marknadsvärde']}
    P/E: {financial_data['P/E']}
    PEG: {financial_data['PEG']}
    Beta: {financial_data['Beta']}
    Skuldsättningsgrad: {financial_data['Skuldsättningsgrad']}
    Direktavkastning (%): {financial_data['Direktavkastning (%)']}
    Aktuell kurs: {financial_data['Aktuell kurs']}
    52 veckors högsta: {financial_data['52v hög']}
    52 veckors lägsta: {financial_data['52v låg']}
    
    Ge en kort analys om hur nyheter och finansiell data kan påverka aktiekursen på kort och lång sikt.
    Ge också en slutlig rekommendation: är det värt att gå igenom kvartalsrapporterna och varför?
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Du är en hjälpsam aktieanalysassistent."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"AI API fel: {e}"

def normalize_pe(pe, industry_pe=20):
    """Jämför P/E med branschstandard och ger risknivå."""
    if pe == "N/A" or pe is None:
        return "Ingen data"
    try:
        pe = float(pe)
        if pe < industry_pe * 0.7:
            return "Lågt (kan vara undervärderat)"
        elif pe > industry_pe * 1.3:
            return "Högt (kan vara övervärderat)"
        else:
            return "Normal"
    except:
        return "Ingen data"

# --- UI ---

st.set_page_config(page_title="Avancerad Aktie & Nyhetsanalys", layout="wide")

st.title("📈 Avancerad Aktie & Nyhetsanalys")

st.sidebar.header("Välj Aktie")
ticker = st.sidebar.text_input("Ange aktiens ticker (t.ex. AAPL, TSLA, ABB)", value="AAPL").upper()

if ticker:
    with st.spinner("Hämtar data..."):
        financials = fetch_company_data(ticker)
        news_items = fetch_news(ticker)

    st.header(f"{financials['Namn']} ({financials['Ticker']})")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Finansiella nyckeltal")
        st.markdown(f"- **Marknadsvärde:** {financials['Marknadsvärde']}")
        st.markdown(f"- **P/E-tal:** {financials['P/E']} ({normalize_pe(financials['P/E'])})")
        st.markdown(f"- **PEG-tal:** {financials['PEG']}")
        st.markdown(f"- **Beta (volatilitet):** {financials['Beta']}")
        st.markdown(f"- **Skuldsättningsgrad:** {financials['Skuldsättningsgrad']}")
        st.markdown(f"- **Direktavkastning (%):** {financials['Direktavkastning (%)']}")
        st.markdown(f"- **Aktuell kurs:** {financials['Aktuell kurs']}")
        st.markdown(f"- **52 veckors hög/låg:** {financials['52v hög']} / {financials['52v låg']}")
        
        with st.expander("Vad betyder P/E-tal?"):
            st.write("""
            P/E-tal (Price-to-Earnings) visar hur marknaden värderar bolagets vinst. 
            Ett högt P/E kan indikera höga förväntningar på framtida tillväxt, men också övervärdering. 
            Ett lågt P/E kan tyda på undervärdering eller problem i bolaget.
            """)

        with st.expander("Vad betyder Beta?"):
            st.write("""
            Beta mäter hur volatil aktien är jämfört med marknaden. 
            En beta på 1 innebär att aktien rör sig i takt med marknaden. 
            Högre beta betyder högre volatilitet och risk.
            """)

    with col2:
        st.subheader("Senaste nyheter och sentiment")
        for item in news_items:
            sentiment, polarity = sentiment_analysis(item["title"])
            color = "green" if sentiment == "Positiv" else "red" if sentiment == "Negativ" else "grey"
            st.markdown(f"**{item['title']}**  ({item['date']})")
            st.markdown(f"*Sentiment:* <span style='color:{color}'>{sentiment}</span>", unsafe_allow_html=True)
            st.markdown(f"{item['desc']}")
            st.markdown("---")

    # Sammanfatta nyheterna för AI-analys
    news_text = " ".join([item["title"] + ". " + item["desc"] for item in news_items])
    if len(news_text) > 2000:
        news_text = news_text[:2000]  # Begränsa längd för API

    st.subheader("AI-driven analys av aktien och nyhetsläget")
    ai_result = ai_stock_analysis(news_text, financials)
    st.info(ai_result)

    # Portfölj och scoring (mockup)
    st.header("Din portfölj")
    portfolio = st.text_area("Lista dina tickers separerade med kommatecken", value="AAPL,TSLA,MSFT")
    if st.button("Analysera portfölj"):
        tickers = [t.strip().upper() for t in portfolio.split(",") if t.strip()]
        scores = []
        for t in tickers:
            d = fetch_company_data(t)
            pe = d.get("P/E")
            pe_score = 0
            try:
                pe_val = float(pe)
                pe_score = max(0, min(10, 10 - (pe_val / 50 * 10)))  # Simpelt poängsystem: lägre PE = högre score
            except:
                pe_score = 5
            scores.append({"Ticker": t, "PE-poäng": pe_score})
        df_scores = pd.DataFrame(scores)
        fig = px.bar(df_scores, x="Ticker", y="PE-poäng", title="PE-poäng per aktie i portföljen")
        st.plotly_chart(fig)

    # Notifiering (mockup)
    st.header("Notifikationer")
    email = st.text_input("Ange din e-post för notifikationer (ej aktiverat ännu)")
    if st.button("Aktivera notifikationer"):
        st.warning("Notifikationer är ännu inte implementerade men kommer snart!")

    # Utbildning
    st.header("Utbildning om aktieanalys")
    with st.expander("Vad är P/E-tal?"):
        st.write("""
        P/E-tal (Price/Earnings ratio) visar hur mycket investerare är villiga att betala för varje krona i vinst. 
        Ett högt P/E kan tyda på höga framtidsförväntningar, medan ett lågt P/E kan tyda på undervärdering eller risk.
        """)

    with st.expander("Hur tolka Beta?"):
        st.write("""
        Beta visar hur mycket aktien rör sig jämfört med marknaden.
        En beta på 1 betyder att aktien rör sig lika mycket som marknaden. 
        En beta över 1 innebär högre volatilitet och risk.
        """)

    with st.expander("Vad är PEG-tal?"):
        st.write("""
        PEG-tal (P/E tillväxt) justerar P/E efter förväntad vinsttillväxt. Ett PEG under 1 kan tyda på undervärdering.
        """)

    with st.expander("Hur tolka nyhetssentiment?"):
        st.write("""
        Positiva nyheter kan driva upp aktiekursen medan negativa nyheter kan skapa osäkerhet och säljtryck.
        Sentimentanalys hjälper dig bedöma om nyheterna är bra eller dåliga för aktien.
        """)

    st.markdown("---")
    st.caption("Appen är en demo och bör inte ses som investeringsråd. Kontrollera alltid flera källor.")

