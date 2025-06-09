import streamlit as st
from GoogleNews import GoogleNews
import yfinance as yf
from openai import OpenAI

# Initiera OpenAI-klient
client = OpenAI()

st.title("Nyhetsanalys med aktiekoppling")

# Ange företag (bolagsnamn och ticker)
company_name = st.text_input("Ange företagets namn (exempel: Tesla)")
stock_ticker = st.text_input("Ange aktiens ticker (exempel: TSLA)")

def fetch_news(company):
    googlenews = GoogleNews(lang='sv', period='7d')
    googlenews.search(company)
    results = googlenews.result()
    return results

def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    current_price = info.get('currentPrice', 'N/A')
    market_cap = info.get('marketCap', 'N/A')
    return current_price, market_cap

def analyze_news_with_stock(news_text, stock_ticker):
    system_prompt = (
        "Du är en finansiell analytiker. Analysera nyheten och bolagsdata och ge en kort och långsiktig prognos "
        f"för aktien {stock_ticker} baserat på följande information:\n\n{news_text}"
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Ge en analys av hur detta påverkar aktiekursen på kort och lång sikt."}
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

if company_name and stock_ticker:
    st.subheader(f"Nyheter för {company_name}")
    news_items = fetch_news(company_name)
    if not news_items:
        st.write("Inga nyheter hittades.")
    else:
        current_price, market_cap = get_stock_data(stock_ticker)
        st.write(f"Aktuellt pris: {current_price}")
        st.write(f"Marknadsvärde: {market_cap}")
        
        for item in news_items[:5]:  # Visa max 5 nyheter
            st.markdown(f"**{item['title']}**")
            st.write(item['desc'])
            
            # Kombinera nyhet och bolagsnamn för analys
            combined_text = item['title'] + " " + item['desc']
            ai_analysis = analyze_news_with_stock(combined_text, stock_ticker)
            st.markdown(f"**AI-analys:** {ai_analysis}")
            st.markdown("---")

else:
    st.info("Ange företagets namn och aktiens ticker för att starta analysen.")
