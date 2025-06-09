import streamlit as st
import yfinance as yf
import feedparser
from openai import OpenAI
import plotly.graph_objects as go
from textblob import TextBlob

# Initiera OpenAI-klienten med din API-nyckel (sätt i miljövariabel OPENAI_API_KEY)
client = OpenAI()

st.set_page_config(page_title="Avancerad Aktie & Nyhetsanalys", layout="wide")

def format_large_number(num):
    if num >= 1_000_000_000:
        return f"{num/1_000_000_000:.2f} miljarder"
    elif num >= 1_000_000:
        return f"{num/1_000_000:.2f} miljoner"
    elif num >= 1_000:
        return f"{num/1_000:.2f} tusen"
    else:
        return str(num)

def fetch_stock_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    financials = {
        "Marknadsvärde": format_large_number(info.get("marketCap", 0)),
        "P/E-tal": info.get("trailingPE", None),
        "PEG-tal": info.get("pegRatio", None),
        "Direktavkastning": info.get("dividendYield", None),
        "EPS": info.get("trailingEps", None),
        "Beta": info.get("beta", None),
        "52 veckors högsta": info.get("fiftyTwoWeekHigh", None),
        "52 veckors lägsta": info.get("fiftyTwoWeekLow", None),
        "Senaste pris": info.get("previousClose", None),
    }
    return financials

def analyze_sentiment(text):
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    if polarity > 0.1:
        return "Positiv"
    elif polarity < -0.1:
        return "Negativ"
    else:
        return "Neutral"

def fetch_news(ticker):
    rss_url = f"https://news.google.com/rss/search?q={ticker}"
    feed = feedparser.parse(rss_url)
    return feed.entries[:5]  # Ta max 5 nyheter

def create_pe_comparison_chart(pe, sector_pe=20):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pe if pe else 0,
        title={'text': "P/E-tal"},
        gauge={
            'axis': {'range': [0, 50]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, sector_pe], 'color': "lightgreen"},
                {'range': [sector_pe, 50], 'color': "lightcoral"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': sector_pe}
        }
    ))
    return fig

def generate_ai_analysis(news_text, financials):
    system_prompt = (
        "Du är en finansanalytiker som analyserar företagsnyheter och finansiella nyckeltal. "
        "Ge en kort analys om hur nyheterna kan påverka aktiens pris på kort och lång sikt. "
        "Ta hänsyn till P/E-tal, PEG-tal, direktavkastning, beta och senaste kvartalsrapportens betydelse."
    )
    user_prompt = f"Nyheter: {news_text}\nNyckeltal: {financials}\nGe en slutsats om börsen."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=400,
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()

def main():
    st.title("📈 Avancerad Aktie- och Nyhetsanalys")

    ticker = st.text_input("Ange bolagets ticker (t.ex. AAPL, TSLA, NOKIA):").upper()
    if not ticker:
        st.info("Ange en ticker för att börja analysen.")
        return

    with st.spinner("Hämtar data..."):
        financials = fetch_stock_data(ticker)
        news_items = fetch_news(ticker)

    # Finansiella nyckeltal
    st.header(f"Nyckeltal för {ticker}")
    cols = st.columns(3)
    with cols[0]:
        st.metric("Marknadsvärde", financials["Marknadsvärde"])
        with st.expander("Vad betyder Marknadsvärde?"):
            st.write("Totalt värde av alla aktier i företaget. Större värde betyder ofta större företag.")
    with cols[1]:
        st.metric("P/E-tal", f"{financials['P/E-tal'] if financials['P/E-tal'] else 'N/A'}")
        with st.expander("Vad betyder P/E-tal?"):
            st.write("Pris/Vinst-tal. Visar hur marknaden värderar vinsten. Lägre är ofta bättre, men beror på bransch.")
    with cols[2]:
        st.metric("Direktavkastning", f"{financials['Direktavkastning']*100:.2f}%" if financials["Direktavkastning"] else "N/A")
        with st.expander("Vad betyder Direktavkastning?"):
            st.write("Utdelning i procent av aktiekursen. Bra för investerare som vill ha utdelning.")

    # P/E-tal jämförelse
    sector_avg_pe = 20  # Sätt en standard för sektorn eller hämta dynamiskt om möjligt
    fig = create_pe_comparison_chart(financials['P/E-tal'], sector_avg_pe)
    st.plotly_chart(fig, use_container_width=True)

    # Visa nyheter och AI-analys
    st.header("Senaste nyheter och analys")
    for item in news_items:
        title = item.get("title", "")
        desc = item.get("summary", "")
        st.subheader(title)
        st.write(desc)

        sentiment = analyze_sentiment(title + " " + desc)
        st.markdown(f"**Sentiment:** {sentiment}")

        with st.spinner("Analyserar nyheter med AI..."):
            analysis = generate_ai_analysis(title + " " + desc, financials)
            st.markdown(f"**AI-Analys:** {analysis}")

        st.divider()

    # Slutgiltig ekonomisk analys
    st.header("Slutgiltig ekonomisk bedömning")
    pe = financials['P/E-tal']
    if pe is None:
        st.write("Ingen tillräcklig data för P/E-tal. Kontrollera kvartalsrapporter för mer info.")
    elif pe < sector_avg_pe:
        st.success("P/E-talet är lägre än sektorns genomsnitt, vilket kan indikera undervärdering. Det kan vara värt att gå igenom kvartalsrapporterna noggrant.")
    else:
        st.warning("P/E-talet är högre än sektorns genomsnitt, vilket kan indikera att aktien är högt värderad. Var försiktig och granska kvartalsrapporterna noga.")

    st.write("**Notera:** Denna analys är endast vägledande och bör kompletteras med egen research.")

if __name__ == "__main__":
    main()
