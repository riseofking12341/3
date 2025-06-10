import streamlit as st
import requests
from bs4 import BeautifulSoup
import openai
import yfinance as yf
import datetime
from textblob import TextBlob

# --- Konfigurera API-nycklar ---
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- Hjälpfunktioner ---

def format_large_number(num):
    if num is None:
        return "N/A"
    num = float(num)
    if num >= 1_000_000_000:
        return f"{num/1_000_000_000:.2f} miljarder"
    elif num >= 1_000_000:
        return f"{num/1_000_000:.2f} miljoner"
    elif num >= 1_000:
        return f"{num/1_000:.2f} tusen"
    else:
        return str(num)

def fetch_google_news(query, max_results=10):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    url = f"https://news.google.com/search?q={query}&hl=sv&gl=SE&ceid=SE:sv"
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        articles = []
        # Google News ändrar ofta sin struktur, detta är en grund
        for item in soup.select("article")[:max_results]:
            title_tag = item.select_one("h3")
            link_tag = item.select_one("a")
            summary_tag = item.select_one("span")
            if title_tag and link_tag:
                title = title_tag.text
                link = "https://news.google.com" + link_tag['href'][1:]  # Ta bort punkt (.) i href
                summary = summary_tag.text if summary_tag else ""
                articles.append({"title": title, "link": link, "summary": summary})
        return articles
    except Exception as e:
        return []

def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "name": info.get("shortName"),
            "currentPrice": info.get("currentPrice"),
            "marketCap": info.get("marketCap"),
            "peRatio": info.get("trailingPE"),
            "forwardPE": info.get("forwardPE"),
            "dividendYield": info.get("dividendYield"),
            "beta": info.get("beta"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "longBusinessSummary": info.get("longBusinessSummary"),
            "logo_url": info.get("logo_url")
        }
    except Exception:
        return {}

def explain_pe_ratio():
    return ("P/E-talet (Price/Earnings) visar hur mycket investerare är villiga att betala för varje krona av vinst. "
            "Ett högt P/E kan tyda på höga förväntningar, medan ett lågt P/E kan indikera undervärdering eller problem.")

def openai_analyze(text, system_prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
            max_tokens=350
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"AI API fel: {str(e)}"

def indirect_news_keywords(stock_info):
    # Exempel på ord kopplade till produktion/material/sektor, kan byggas på
    keywords = []
    sector = stock_info.get("sector", "").lower()
    industry = stock_info.get("industry", "").lower()
    summary = stock_info.get("longBusinessSummary", "").lower()

    # Kolla sektor och bransch och lägg till relaterade ord
    if "technology" in sector or "software" in industry:
        keywords.extend(["molntjänster", "cybersäkerhet", "chips", "semiconductor", "AI", "artificiell intelligens"])
    if "energy" in sector:
        keywords.extend(["olja", "gas", "förnybar energi", "vindkraft", "solenergi", "koldioxidutsläpp", "miljöregleringar"])
    if "automotive" in industry or "car" in summary:
        keywords.extend(["elektrisk bil", "batteri", "kolfiber", "ståltullar", "leverantörskedja", "halvledarbrist"])
    if "healthcare" in sector:
        keywords.extend(["läkemedel", "FDA", "kliniska studier", "vaccin", "medicinsk utrustning"])
    if not keywords:
        # Generella ekonomiska nyckelord
        keywords.extend(["ränta", "inflation", "recession", "konjunktur", "aktiemarknad"])

    # Döp till sträng för sökning (max 5 ord)
    return " OR ".join(keywords[:5])

# --- Streamlit UI ---

st.set_page_config(page_title="Aktie- och Nyhetsanalys", layout="wide")

st.title("🔎 Aktie- & Nyhetsanalys med Indirekt & Direkt Påverkan")
st.write("Få insikter om företagets ekonomi och nyheter som påverkar aktiekursen, både direkt och indirekt.")

# Input
stock_ticker = st.text_input("Ange aktiens ticker-symbol (t.ex. TSLA, AAPL):", value="TSLA").upper()

if stock_ticker:
    stock_info = get_stock_data(stock_ticker)
    if not stock_info:
        st.error("Kunde inte hämta aktiedata. Kontrollera ticker-symbolen.")
    else:
        col1, col2 = st.columns([3,1])

        with col1:
            st.header(f"{stock_info.get('name')} ({stock_ticker})")

            st.markdown(f"**Aktuell pris:** {stock_info.get('currentPrice', 'N/A')} SEK")
            st.markdown(f"**Marknadsvärde:** {format_large_number(stock_info.get('marketCap'))}")
            st.markdown(f"**P/E-tal:** {stock_info.get('peRatio', 'N/A')}")
            with st.expander("Vad är P/E-tal?"):
                st.write(explain_pe_ratio())
            st.markdown(f"**Utdelningsavkastning:** {stock_info.get('dividendYield', 'N/A')}")
            st.markdown(f"**Beta (volatilitet):** {stock_info.get('beta', 'N/A')}")
            st.markdown(f"**Sektor:** {stock_info.get('sector', 'N/A')}")
            st.markdown(f"**Bransch:** {stock_info.get('industry', 'N/A')}")

            st.markdown("### Kort sammanfattning:")
            st.write(stock_info.get("longBusinessSummary", "Ingen sammanfattning tillgänglig."))

            if stock_info.get("logo_url"):
                st.image(stock_info["logo_url"], width=100)

        with col2:
            # Nyheter direkt kopplade till företaget
            st.subheader("Senaste nyheter direkt om företaget")
            direct_news = fetch_google_news(stock_info.get("name", stock_ticker))
            if direct_news:
                for item in direct_news:
                    st.markdown(f"**[{item['title']}]({item['link']})**")
                    st.write(item['summary'])
                    # AI-analys per nyhet
                    prompt = (f"Ge en kort analys om hur denna nyhet kan påverka aktiekursen för {stock_info.get('name')}: \n\n"
                              f"Nyhet: {item['title']} - {item['summary']}")
                    ai_result = openai_analyze(prompt, "Du är en duktig finansanalytiker.")
                    st.info(ai_result)
            else:
                st.write("Inga direkta nyheter hittades.")

            # Indirekta nyheter via relaterade nyckelord
            st.subheader("Indirekta nyheter baserat på företagets material, sektor och bransch")
            indirect_query = indirect_news_keywords(stock_info)
            indirect_news = fetch_google_news(indirect_query)
            if indirect_news:
                for item in indirect_news:
                    st.markdown(f"**[{item['title']}]({item['link']})**")
                    st.write(item['summary'])
                    # AI-analys per indirekt nyhet
                    prompt_indirect = (f"Ge en kort analys om hur denna indirekta nyhet kan påverka aktiekursen för {stock_info.get('name')}:\n\n"
                                       f"Nyhet: {item['title']} - {item['summary']}")
                    ai_result_indirect = openai_analyze(prompt_indirect, "Du är en erfaren finansanalytiker.")
                    st.info(ai_result_indirect)
            else:
                st.write("Inga indirekta nyheter hittades.")

            # Slutlig analys
            st.subheader("Slutlig investeringsanalys")
            combined_text = f"{stock_info.get('longBusinessSummary', '')}\nDirekta nyheter: {', '.join([n['title'] for n in direct_news])}\nIndirekta nyheter: {', '.join([n['title'] for n in indirect_news])}"
            final_prompt = ("Sammanfatta företagets nuvarande läge och ge en bedömning om aktien verkar ha potential baserat på "
                            "ekonomisk data och nyheter, både direkt och indirekt relaterade.")
            final_analysis = openai_analyze(combined_text, final_prompt)
            st.success(final_analysis)
