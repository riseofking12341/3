import streamlit as st
import openai
import yfinance as yf
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
import plotly.graph_objects as go

# API-nycklar
openai.api_key = 'din-openai-nyckel'

# Funktion för att hämta aktiedata
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    stock_data = stock.history(period="1d", interval="1h")
    return stock_data

# Funktion för att hämta nyheter om ett företag och dess bransch
def get_related_news(company_name):
    # Nyckelord som kan vara relaterade till företagets verksamhet
    keywords = [company_name, f"{company_name} raw materials", f"{company_name} market", "global trade tariffs", "carbon fiber", "steel tariffs"]
    
    news_articles = []
    for keyword in keywords:
        url = f"https://newsapi.org/v2/everything?q={keyword}&apiKey=din-news-api-nyckel"
        response = requests.get(url).json()
        
        for article in response['articles']:
            news_articles.append({
                'title': article['title'],
                'description': article['description'],
                'url': article['url'],
                'published_at': article['publishedAt'],
            })
    return news_articles

# Funktion för att analysera nyheterna med GPT-3
def analyze_news_with_gpt(news_articles, company_name):
    news_text = " ".join([article['title'] + " " + article['description'] for article in news_articles])
    
    # Be GPT att analysera hur nyheterna påverkar företaget
    prompt = f"Given the following news related to {company_name}, analyze how they can affect the company's stock price in the short and long term:\n\n{news_text}"
    
    try:
        response = openai.Completion.create(
            engine="gpt-3.5-turbo",  # För den senaste modellen
            prompt=prompt,
            max_tokens=500,
            temperature=0.7,
        )
        analysis = response.choices[0].text.strip()
        return analysis
    except Exception as e:
        return f"Error in analysis: {e}"

# Funktion för att bedöma aktiens framtida potential baserat på ekonomiska siffror
def stock_price_potential(stock_data, news_analysis):
    latest_price = stock_data['Close'][-1]
    percent_change = (stock_data['Close'][-1] - stock_data['Close'][0]) / stock_data['Close'][0] * 100
    
    # Här kan vi också lägga till sentimentanalys på nyheterna
    sentiment = TextBlob(news_analysis).sentiment.polarity
    
    # Visualisera aktiekursens förändring
    fig = go.Figure(go.Candlestick(x=stock_data.index,
                                 open=stock_data['Open'],
                                 high=stock_data['High'],
                                 low=stock_data['Low'],
                                 close=stock_data['Close']))
    fig.update_layout(title=f"{company_name} Stock Price Analysis", xaxis_title="Date", yaxis_title="Price (USD)")
    
    # Slutlig bedömning av aktiens framtida potential
    future_trend = "Positive" if sentiment > 0 else "Negative"
    
    return fig, f"Sentiment: {sentiment:.2f}, Short-term price change: {percent_change:.2f}%, Long-term outlook: {future_trend}"

# Använd Streamlit för UI
st.title("Stock News and Analysis")
company_name = st.text_input("Enter Company Name:", "Astor")
stock_ticker = st.text_input("Enter Stock Ticker (e.g., TSLA, AAPL):", "ASTOR")

if st.button("Get Analysis"):
    st.write("Fetching stock data and news...")
    
    # Hämta aktiedata och nyheter
    stock_data = get_stock_data(stock_ticker)
    news_articles = get_related_news(company_name)
    
    # Analysera nyheterna med GPT-3
    news_analysis = analyze_news_with_gpt(news_articles, company_name)
    
    # Visa aktiekursanalys
    fig, price_analysis = stock_price_potential(stock_data, news_analysis)
    
    st.plotly_chart(fig)
    st.write(price_analysis)
    
    # Visa detaljerad nyhetsanalys
    st.subheader("News Analysis")
    st.write(news_analysis)
    
    st.subheader("Related News")
    for article in news_articles:
        st.write(f"[{article['title']}]({article['url']})")
        st.write(f"Published on: {article['published_at']}")
        st.write(f"Description: {article['description']}")
        st.markdown("---")



