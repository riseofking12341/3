import streamlit as st
from GoogleNews import GoogleNews
import yfinance as yf
import openai
import matplotlib.pyplot as plt
from datetime import datetime

# --- OpenAI API-nyckel ---
openai.api_key = st.secrets["OPENAI_API_KEY"]  # alternativt: openai.api_key = "din_nyckel"

st.set_page_config(page_title="Bolagsnyheter + Aktieanalys", layout="wide")

st.title("Bolagsnyheter med aktie- och AI-analys")

# Input från användaren
company_name = st.text_input("Skriv bolagsnamn (t.ex. 'Tesla'):")
stock_ticker = st.text_input("Skriv bolagets börsticker (t.ex. 'TSLA'):")

if company_name and stock_ticker:

    # Funktion: hämta nyheter
    @st.cache_data(ttl=3600)
    def fetch_news(query):
        googlenews = GoogleNews(lang='sv', region='SE')
        googlenews.search(query)
        result = googlenews.result()
        return result

    # Funktion: hämta aktiekurs och finansiell info
    @st.cache_data(ttl=3600)
    def fetch_stock_data(ticker):
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        info = stock.info
        return hist, info

    # Funktion: plottar kursdata
    def plot_stock(history):
        fig, ax = plt.subplots()
        ax.plot(history.index, history['Close'], label='Stängningspris')
        ax.set_xlabel('Datum')
        ax.set_ylabel('Pris (USD)')
        ax.set_title('Aktiekurs senaste månaden')
        ax.legend()
        st.pyplot(fig)

    # Funktion: analysera med OpenAI
    @st.cache_data(ttl=3600)
    def analyze_news_with_stock(news_text, ticker):
        hist, info = fetch_stock_data(ticker)
        close_prices = list(hist['Close'])
        dates = [d.strftime("%Y-%m-%d") for d in hist.index]

        price_summary = f"Stängningspriser senaste månaden: \n"
        for date, price in zip(dates, close_prices):
            price_summary += f"{date}: {price:.2f} USD\n"

        financials = (
            f"PE-ratio: {info.get('trailingPE', 'N/A')}, "
            f"Marknadsvärde: {info.get('marketCap', 'N/A')}, "
            f"Beta: {info.get('beta', 'N/A')}"
        )

        prompt = f"""
        Här är en nyhet om bolaget {company_name}:
        "{news_text}"

        Aktiekursdata (senaste månaden):
        {price_summary}

        Finansiella nyckeltal:
        {financials}

        Analysera kortsiktiga och långsiktiga effekter av denna nyhet på bolagets aktiekurs.
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()

    # --- Hämta och visa nyheter ---
    news_items = fetch_news(company_name)
    if not news_items:
        st.warning("Inga nyheter hittades för detta bolag.")
    else:
        st.subheader(f"Senaste nyheter om {company_name}:")
        for i, item in enumerate(news_items[:5]):
            st.markdown(f"### {item['title']}")
            st.write(f"*Datum:* {item['date']}  \n*Beskrivning:* {item['desc']}  \n[Artikel]( {item['link']} )")

            # Analysera varje nyhet
            with st.spinner(f"Analyserar nyhet {i+1}..."):
                ai_analysis = analyze_news_with_stock(item['title'] + " " + item['desc'], stock_ticker)
                st.info(f"**AI-analys:**  \n{ai_analysis}")

            st.markdown("---")

        # Visa aktiekursdiagram
        st.subheader(f"Aktiekurs för {stock_ticker}")
        hist, _ = fetch_stock_data(stock_ticker)
        plot_stock(hist)

else:
    st.info("Fyll i både bolagsnamn och börsticker för att börja.")

