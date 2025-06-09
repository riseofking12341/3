import streamlit as st
import yfinance as yf
import requests
from openai import OpenAI
import datetime

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Företags- och Aktieanalys", layout="wide")

# Format large numbers nicely
def human_format(num):
    if num is None:
        return "N/A"
    for unit in ['','K','M','B','T']:
        if abs(num) < 1000:
            return f"{num:.2f}{unit}"
        num /= 1000
    return f"{num:.2f}P"

# Sidebar input
st.sidebar.header("Sök företag")
stock_ticker = st.sidebar.text_input("Ange bolags ticker (t.ex. AAPL, VOLV-B.ST):").upper()
if not stock_ticker:
    st.info("Ange en bolags ticker för att börja analysen.")
    st.stop()

@st.cache_data(ttl=3600)
def fetch_company_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return info
    except Exception:
        return None

@st.cache_data(ttl=1800)
def fetch_news(ticker):
    # Using Finnhub news API as example, replace with your own news API
    api_key = st.secrets.get("FINNHUB_API_KEY", "")
    if not api_key:
        return []
    url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={(datetime.date.today() - datetime.timedelta(days=7)).isoformat()}&to={datetime.date.today().isoformat()}&token={api_key}"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            return res.json()
        else:
            return []
    except Exception:
        return []

def analyze_news_and_stock(news_text, stock_info):
    system_message = """
    Du är en erfaren aktieanalytiker som analyserar bolagsnyheter kopplat till deras finansiella nyckeltal och aktiekurs.
    Ge en kortfattad analys om hur nyheten kan påverka aktiekursen på kort och lång sikt.
    Ta hänsyn till bolagets senaste kvartalsrapport, P/E-tal, utdelning, och marknadssituation.
    """
    user_message = f"Nyhet: {news_text}\n\nFinansiella nyckeltal: {stock_info}"

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        max_tokens=300,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def generate_final_analysis(stock_info):
    # Summarize if the company looks worth deeper review
    system_message = """
    Du är en senior finansanalytiker.
    Basera din slutsats på följande data och avgör om det är värt att gå igenom företagets kvartalsrapport för investering.
    """
    user_message = f"Finansiella nyckeltal: {stock_info}"

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        max_tokens=200,
        temperature=0.6
    )
    return response.choices[0].message.content.strip()

# Fetch data
stock_info = fetch_company_data(stock_ticker)
if not stock_info:
    st.error("Kunde inte hitta data för ticker: " + stock_ticker)
    st.stop()

news_items = fetch_news(stock_ticker)

# Show company info
st.title(f"{stock_info.get('longName', stock_ticker)} ({stock_ticker})")

col1, col2 = st.columns([2,3])

with col1:
    st.subheader("Nyckeltal")
    market_cap = stock_info.get('marketCap')
    pe_ratio = stock_info.get('trailingPE')
    forward_pe = stock_info.get('forwardPE')
    dividend_yield = stock_info.get('dividendYield')
    revenue = stock_info.get('totalRevenue')
    net_income = stock_info.get('netIncomeToCommon')

    st.write(f"**Marknadsvärde:** {human_format(market_cap)} SEK")
    st.write(f"**P/E-tal (bakåt):** {pe_ratio if pe_ratio else 'N/A'}")
    st.write(f"**Framtida P/E-tal:** {forward_pe if forward_pe else 'N/A'}")
    st.write(f"**Utdelningsavkastning:** {dividend_yield * 100:.2f}% " if dividend_yield else "Utdelningsavkastning: N/A")
    st.write(f"**Omsättning (Senaste året):** {human_format(revenue)} SEK")
    st.write(f"**Nettoinkomst (Senaste året):** {human_format(net_income)} SEK")

    with st.expander("Vad betyder dessa nyckeltal?"):
        st.markdown("""
        - **Marknadsvärde:** Total värdering av företaget på börsen.
        - **P/E-tal:** Pris per vinst, visar hur mycket du betalar för varje krona i vinst.
        - **Utdelningsavkastning:** Hur stor del av aktiekursen som betalas ut som utdelning.
        - **Omsättning:** Företagets intäkter under senaste året.
        - **Nettoinkomst:** Vinst efter kostnader och skatt.
        """)

with col2:
    st.subheader("Senaste nyheter och analys")
    if news_items:
        for item in news_items[:5]:  # show max 5 news
            news_text = item.get('headline', '') + "\n\n" + (item.get('summary') or item.get('description') or '')
            st.markdown(f"### [{item.get('headline')}]({item.get('url')})")
            st.write(news_text)

            stock_summary = (
                f"Marknadsvärde: {human_format(market_cap)} SEK, "
                f"P/E-tal: {pe_ratio if pe_ratio else 'N/A'}, "
                f"Utdelningsavkastning: {dividend_yield*100:.2f}% " if dividend_yield else "N/A"
            )
            analysis = analyze_news_and_stock(news_text, stock_summary)
            st.info(f"**Analys:** {analysis}")
            st.markdown("---")
    else:
        st.info("Inga nyheter hittades för detta företag senaste veckan.")

# Final overall analysis
st.subheader("Slutgiltig analys")
final_analysis = generate_final_analysis(stock_info)
st.success(final_analysis)
