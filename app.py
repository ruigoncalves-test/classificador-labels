import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import google.generativeai as genai

# ========================================================
# CONFIGURAÇÃO DA PÁGINA
# ========================================================
st.set_page_config(page_title="Auto-Labeler Gemini Pro", page_icon="🏷️", layout="wide")

st.title("🏷️ Classificador Automático de Secções")
st.markdown("""
Esta app extrai os links de um site e utiliza o **Google Gemini** para atribuir 
as labels mais específicas com base nas tuas regras de negócio.
""")

# ========================================================
# GESTÃO DA API KEY (Secrets ou Sidebar)
# ========================================================
api_key = None

if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Insere a tua Gemini API Key:", type="password")
    st.sidebar.info("Dica: Podes guardar esta chave nos 'Secrets' do Streamlit Cloud para não teres de a digitar sempre.")

# ========================================================
# CONFIGURAÇÃO DO MODELO (Versão Estável)
# ========================================================
model = None
if api_key:
    try:
        genai.configure(api_key=api_key)
        # Usamos o caminho completo para evitar o erro 404
        model = genai.GenerativeModel('models/gemini-1.5-flash')
    except Exception as e:
        st.error(f"Erro ao configurar a API do Google: {e}")

# ========================================================
# VARIÁVEIS E LÓGICA DE SCRAPING
# ========================================================
LABELS = "Adult, American Football, Animals, Anime, Auto, Baseball, Basket, Beauty, Betting, Blog, Business, Casino, Celebrities, Chat Groups, Combat, Cosmetics, Cricket, Crypto, Culinary, Dating, Deco/Arch, E-Commerce, Education, Entertainment, Esoteric, Esports, Fashion, File Sharing, Finance, Football, Games, Golf, Health, Hockey, Horses, Humor, Jobs, Judicial, Legal, Lifestyle, Literature, Loans/Credits, Lottery, Marketing, MMA, Motorsports, Music, News, Politics, Quotes, Radio, Religion, Rugby, Sports, streaming, Technology, Tennis, Tourism, Weather, Well-Being"

def get_site_sections(url):
    """Extrai URLs que parecem ser categorias do site."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        domain = urlparse(url).netloc
        links = set()
        
        for a in soup.find_all('a', href=True):
            full_url = urljoin(url, a['href'])
            parsed_url = urlparse(full_url)
            
            # Filtra apenas links do próprio domínio, remove fragmentos e query params
            if parsed_url.netloc == domain and '#' not in full_url:
                clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                # Evita links de artigos muito profundos (normalmente categorias têm poucos /)
                if len(parsed_url.path.strip('/').split('/')) <= 2 and clean_url != url:
                    links.add(clean_url)
        
        return sorted(list(links))
    except Exception as e:
        st.error(f"Erro
