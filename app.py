import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import google.generativeai as genai

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Auto-Labeler Gemini Pro", page_icon="🏷️", layout="wide")

st.title("🏷️ Classificador Automático de Secções")

# GESTÃO DA API KEY
api_key = None
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Insere a tua Gemini API Key:", type="password")

# CONFIGURAÇÃO DO MODELO
model = None
if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-1.5-flash')
    except Exception as e:
        st.error(f"Erro na configuração: {e}")

LABELS = "Adult, American Football, Animals, Anime, Auto, Baseball, Basket, Beauty, Betting, Blog, Business, Casino, Celebrities, Chat Groups, Combat, Cosmetics, Cricket, Crypto, Culinary, Dating, Deco/Arch, E-Commerce, Education, Entertainment, Esoteric, Esports, Fashion, File Sharing, Finance, Football, Games, Golf, Health, Hockey, Horses, Humor, Jobs, Judicial, Legal, Lifestyle, Literature, Loans/Credits, Lottery, Marketing, MMA, Motorsports, Music, News, Politics, Quotes, Radio, Religion, Rugby, Sports, streaming, Technology, Tennis, Tourism, Weather, Well-Being"

def get_site_sections(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        domain = urlparse(url).netloc
        links = set()
        for a in soup.find_all('a', href=True):
            full_url = urljoin(url, a['href'])
            parsed = urlparse(full_url)
            if parsed.netloc == domain and '#' not in full_url:
                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                if len(parsed.path.strip('/').split('/')) <= 2 and clean_url != url:
                    links.add(clean_url)
        return sorted(list(links))
    except Exception as e:
        st.error(f"Erro no scraping: {e}")
        return []

url_input = st.text_input("URL do site (ex: https://nypost.com):")

if st.button("Analisar e Classificar"):
    if not api_key:
        st.warning("Introduz a API Key.")
    elif not url_input:
        st.warning("Introduz o URL.")
    else:
        with st.spinner("A extrair secções..."):
            seccoes = get_site_sections(url_input)
        
        if seccoes:
            with st.spinner("A classificar com IA..."):
                prompt = f"Atribui apenas uma label da lista [{LABELS}] a cada URL, sendo específico (ex: Baseball em vez de Sports). Formato: URL - Label. URLs:\n" + "\n".join(seccoes[:50])
                try:
                    response = model.generate_content(prompt)
                    st.subheader("Resultados:")
                    st.text_area("Resultado:", value=response.text, height=400)
                except Exception as e:
                    st.error(f"Erro na IA: {e}")
        else:
            st.error("Nenhum link encontrado.")
