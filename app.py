
import streamlit as st
import openai
from googlenews import GoogleNews
import datetime

openai.api_key = st.secrets["OPENAI_API_KEY"]

st.title("AI Nyhetsanalys för Företag & Aktier")

company = st.text_input("Ange företagsnamn (t.ex. Astor Scandinavian Group):")

if company:
    with st.spinner("Hämtar nyheter..."):
        googlenews = GoogleNews(lang='sv')
        googlenews.set_time_range(
            (datetime.datetime.now() - datetime.timedelta(days=14)).strftime("%m/%d/%Y"),
            datetime.datetime.now().strftime("%m/%d/%Y")
        )
        googlenews.search(company)
        news_results = googlenews.results(sort=True)

        news_texts = []
        for article in news_results[:8]:
            title = article.get("title", "")
            desc = article.get("desc", "")
            link = article.get("link", "")
            news_texts.append(f"- {title}\n{desc}\n{link}")

        news_prompt = "\n\n".join(news_texts) if news_texts else "Inga nyheter hittades."

    st.subheader("🔍 AI-analys")
    with st.spinner("Analyserar med AI..."):
        prompt = f"""
Du är en AI-expert på aktieanalys. Företaget heter "{company}".
Baserat på dessa nyheter och ekonomisk data, analysera företagets aktie och framtidspotential.

Nyhetsdata:
{news_prompt}

Gör följande:
1. Analysera de viktigaste nyheterna och deras påverkan på företagets framtid.
2. Spekulera kring ekonomiska nyckeltal (t.ex. vinst, omsättning, tillväxt) baserat på nyhetsflödet.
3. Bedöm om aktien är i riskzon eller har stor uppsida just nu.
4. Ge en sammanfattning med riskbedömning och om det är troligt att aktien går upp eller ner.

Skriv på svenska, kortfattat och med klar slutsats.
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        st.write(response.choices[0].message.content)
