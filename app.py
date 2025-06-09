import streamlit as st
import openai
from GoogleNews import GoogleNews

openai.api_key = st.secrets["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"]

st.title("🔍 Smart Nyhetsanalys för Företag")
company = st.text_input("🔎 Sök företag (ex: Astor Scandinavian Group)")

def fetch_news(company):
    googlenews = GoogleNews(lang='sv')
    googlenews.search(company)
    return googlenews.results()[:3]  # De 3 senaste

def analyze_news(news, company):
    text = f"{news['title']}. {news['desc']}"
    prompt = f"""
    Här är en nyhet om {company}:

    {text}

    🔍 Vad kan detta innebära för {company}?

    Svara med:
    - Sammanfattning av nyheten
    - Sannolik påverkan på aktien (liten/medel/stor)
    - Risk för nedgång (1–10)
    - Sannolikhet för uppgång (1–10)
    - Kort förklaring till båda
    """

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

if st.button("Analysera nyheter") and company:
    news_list = fetch_news(company)

    if not news_list:
        st.write("❌ Hittade inga nyheter.")
    else:
        for news in news_list:
            st.write(f"📰 {news['title']} ({news['date']})")
            st.write(f"[Länk till nyhet]({news['link']})")
            st.write("🔍 GPT-analys:")
            try:
                analysis = analyze_news(news, company)
                st.write(analysis)
            except Exception as e:
                st.error(f"Fel vid analys: {e}")
