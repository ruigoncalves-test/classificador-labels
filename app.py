import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import google.generativeai as genai

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Classificador Híbrido Pro", layout="wide")
st.title("🛡️ Classificador Inteligente (Lógica + IA)")

# GESTÃO DA API KEY
api_key = st.secrets.get("GEMINI_API_KEY") or st.sidebar.text_input("Gemini API Key:", type="password")
if api_key:
    genai.configure(api_key=api_key.strip())

# DICIONÁRIO DE REGRAS (Lógica local sem custos)
MAPA_LOGICO = {
    "American Football": ["nfl", "jets", "giants", "super-bowl", "college-football"],
    "Baseball": ["mlb", "yankees", "mets", "world-series"],
    "Basket": ["nba", "knicks", "nets", "basketball"],
    "Hockey": ["nhl", "rangers", "islanders", "devils"],
    "Soccer": ["soccer", "premier-league", "champions-league", "world-cup"],
    "Politics": ["politics", "elections", "white-house", "congress", "senate"],
    "Celebrities": ["p6", "page-six", "celebrity", "hollywood", "gossip"],
    "Technology": ["tech", "gadgets", "ai", "iphone", "android"],
    "Business": ["business", "economy", "money", "stocks", "finance"],
    "Health": ["health", "fitness", "wellness", "medical"],
    "Movies": ["movies", "film", "cinema"],
    "Fashion": ["fashion", "beauty", "style"],
    "Betting": ["betting", "odds", "sportsbook"],
    "Esoteric": ["horoscopes", "astrology", "zodiac"],
    "Tourism": ["travel", "tourism", "vacation"]
}

def classificar_por_logica(url):
    url_lower = url.lower()
    for label, keywords in MAPA_LOGICO.items():
        if any(key in url_lower for key in keywords):
            return label
    return None

def get_clean_sections(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        domain = urlparse(url).netloc
        ignore_list = ['/author/', '/contact', '/settings', '/subscribe', '/privacy', '/terms', '/login', '/about']
        
        links = set()
        for a in soup.find_all('a', href=True):
            full_url = urljoin(url, a['href']).split('?')[0].split('#')[0].rstrip('/')
            parsed = urlparse(full_url)
            if parsed.netloc == domain and not any(x in full_url for x in ignore_list):
                path_parts = [p for p in parsed.path.split('/') if p]
                if 1 <= len(path_parts) <= 2:
                    links.add(full_url)
        return sorted(list(links))
    except:
        return []

url_input = st.text_input("URL do Site para classificar:")

if st.button("Executar Classificação"):
    if url_input:
        with st.spinner("A analisar URLs..."):
            seccoes = get_clean_sections(url_input)
            
            if seccoes:
                resultados_finais = []
                urls_para_ia = []

                # PASSO 1: Lógica Local
                for url in seccoes:
                    label = classificar_por_logica(url)
                    if label:
                        resultados_finais.append(f"{url} - **{label}** (Lógica)")
                    else:
                        urls_para_ia.append(url)

                # PASSO 2: IA para o resto
                if urls_para_ia:
                    if api_key:
                        try:
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            prompt = "Classifica estes URLs com as labels mais específicas:\n" + "\n".join(urls_para_ia[:30])
                            res = model.generate_content(prompt)
                            resultados_finais.append("\n---\n### Classificado por IA:\n" + res.text)
                        except Exception as e:
                            st.warning(f"Erro na IA (Quota?): {e}")
                            for u in urls_para_ia:
                                resultados_finais.append(f"{u} - **News** (Fallback)")
                    else:
                        for u in urls_para_ia:
                            resultados_finais.append(f"{u} - **News** (Sem API)")

                # MOSTRAR RESULTADOS
                st.subheader("Resultados:")
                for r in resultados_finais:
                    st.write(r)
            else:
                st.error("Nenhum link encontrado.")
