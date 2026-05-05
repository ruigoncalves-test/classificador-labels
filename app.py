import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import google.generativeai as genai

# Configurações iniciais
st.set_page_config(page_title="Auto-Labeler Gemini", page_icon="🏷️")
st.title("🏷️ Classificador Automático (Gemini Edition)")

# Tenta ler a chave dos Secrets ou da Sidebar
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Insere a tua Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

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
            if urlparse(full_url).netloc == domain and '#' not in full_url:
                if len(urlparse(full_url).path.split('/')) <= 3:
                    links.add(full_url)
        return sorted(list(links))
    except Exception as e:
        st.error(f"Erro ao ler o site: {e}")
        return []

url_input = st.text_input("URL do site:", placeholder="https://nypost.com")

if st.button("Analisar e Classificar"):
    if not api_key:
        st.error("Falta a API Key!")
    elif url_input:
        with st.spinner("A processar com Gemini..."):
            seccoes = get_site_sections(url_input)
            if seccoes:
                prompt = f"""
                Analisa estes URLs e atribui a label mais específica desta lista: {LABELS}
                Regras: Política > News. Baseball > Sports. Pirataria > Copyright.
                Responde no formato: URL - Label
                URLs:
                """ + "\n".join(seccoes[:40])
                
                try:
                    response = model.generate_content(prompt)
                    st.subheader("Resultados:")
                    st.text(response.text)
                except Exception as e:
                    st.error(f"Erro no Gemini: {e}")
