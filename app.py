import streamlit as st
from GoogleNews import GoogleNews
import datetime
from openai import OpenAI

# Initiera OpenAI-klienten
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("AI Nyhetsanalys för Företag & Aktier")

company = st.text_input("Ange företagsnamn (t.ex. Astor Scandinavian Group):")

@st.cache_data(ttl=1800)  # Cache nyhetssökning i 30 minuter
def fetch_news(company_name):
    googlenews = GoogleNews(lang='sv')
    start_date = (datetime.datetime.now() - datetime.timedelta(days=14)).strftime("%m/%d/%Y")
    end_date = datetime.datetime.now().strftime("%m/%d/%Y")
    googlenews.set_time_range(start_date, end_date)
    googlenews.search(company_name)
    results = googlenews.results(sort=True)
    
    news_items = []
    for article in results[:8]:
        title = article.get("title", "")
        desc = article.get("desc", "")
        link = article.get("link", "")
        news_items.append(f"- {title}\n{desc}\n{link}")
    
    return "\n\n".join(news_items) if news_items else "Inga nyheter hittades."

def get_ai_analysis(prompt, model="gpt-3.5-turbo"):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI API fel: {e}"

if company:
    with st.spinner("Hämtar nyheter..."):
        news_text = fetch_news(company)

    st.subheader("📰 Nyheter")
    st.write(news_text)

    st.subheader("🔍 AI-analys")

    prompt = f"""
Du är en AI-expert på aktieanalys. Företaget heter "{company}".
Baserat på dessa nyheter och ekonomisk data, analysera företagets aktie och framtidspotential.

Nyhetsdata:
{news_text}

Gör följande:
1. Analysera de viktigaste nyheterna och deras påverkan på företagets framtid.
2. Spekulera kring ekonomiska nyckeltal (t.ex. vinst, omsättning, tillväxt) baserat på nyhetsflödet.
3. Bedöm om aktien är i riskzon eller har stor uppsida just nu.
4. Ge en sammanfattning med riskbedömning och om det är troligt att aktien går upp eller ner.

Skriv på svenska, kortfattat och med klar slutsats.
"""

    with st.spinner("Analyserar med AI..."):
        ai_response = get_ai_analysis(prompt, model="gpt-3.5-turbo")
    
    st.write(ai_response)
