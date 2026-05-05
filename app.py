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

# CONFIGURAÇÃO DO MODELO COM FALLBACK (CONTINGÊNCIA)
model = None
if api_key:
    try:
        genai.configure(api_key=api_key)
        # Tentamos primeiro o Flash, se der erro 404, usamos o Pro
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            # Teste rápido para ver se o modelo responde
            model.generate_content("test") 
        except:
            model = genai.GenerativeModel('gemini-pro')
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
                # Filtro para pegar apenas categorias principais
                path_parts = [p for p in parsed.path.split('/') if p]
                if len(path_parts) == 1:
                    links.add(clean_url)
        return sorted(list(links))
    except Exception as e:
        st.error(f"Erro no scraping: {e}")
        return []

url_input = st.text_input("URL do site (ex: https://nypost.com):")

if st.button("Analisar e Classificar"):
    if not api_key:
        st.warning("Introduz a API Key na barra lateral ou nos Secrets.")
    elif not url_input:
        st.warning("Introduz o URL do site.")
    else:
        with st.spinner("A extrair secções do site..."):
            seccoes = get_site_sections(url_input)
        
        if seccoes:
            st.info(f"Encontradas {len(seccoes)} secções. A classificar com IA...")
            with st.spinner("A aguardar resposta do Gemini..."):
                prompt = f"Atribui apenas uma label da lista [{LABELS}] a cada URL abaixo. Sê específico (ex: Baseball em vez de Sports). Formato: URL - Label. URLs:\n" + "\n".join(seccoes[:40])
                try:
                    response = model.generate_content(prompt)
                    st.subheader("Resultados:")
                    st.text_area("Copia os resultados:", value=response.text, height=400)
                except Exception as e:
                    st.error(f"Erro na IA: {e}")
        else:
            st.error("Nenhum link de secção encontrado. Tenta outro site ou verifica o URL.")
