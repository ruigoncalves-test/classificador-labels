import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import google.generativeai as genai

st.set_page_config(page_title="Classificador Expert", layout="wide")
st.title("🎯 Classificador de Categorias")

# GESTÃO DA API KEY
api_key = st.secrets.get("GEMINI_API_KEY") or st.sidebar.text_input("Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key.strip())

LABELS = "Adult, American Football, Animals, Anime, Auto, Baseball, Basket, Beauty, Betting, Blog, Business, Casino, Celebrities, Chat Groups, Combat, Cosmetics, Cricket, Crypto, Culinary, Dating, Deco/Arch, E-Commerce, Education, Entertainment, Esoteric, Esports, Fashion, File Sharing, Finance, Football, Games, Golf, Health, Hockey, Horses, Humor, Jobs, Judicial, Legal, Lifestyle, Literature, Loans/Credits, Lottery, Marketing, MMA, Motorsports, Music, News, Politics, Quotes, Radio, Religion, Rugby, Sports, streaming, Technology, Tennis, Tourism, Weather, Well-Being"

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
    except: return []

url_input = st.text_input("URL do Site:")

if st.button("Classificar"):
    if not api_key:
        st.error("Insere a API Key!")
    elif url_input:
        with st.spinner("A analisar..."):
            seccoes = get_clean_sections(url_input)
            if seccoes:
                try:
                    # O TRUQUE: Listar modelos e escolher o que estiver disponível
                    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    # Tenta 1.5-flash, depois 1.0-pro, senão o primeiro que houver
                    best_model = next((m for m in models if "1.5-flash" in m), 
                                     next((m for m in models if "pro" in m), models[0]))
                    
                    st.info(f"Modelo detectado: {best_model}")
                    model = genai.GenerativeModel(best_model)
                    
                    prompt = f"Labels: {LABELS}\nRegras: Sê específico (ex: Jets -> American Football). Ignora links de sistema. Classifica:\n" + "\n".join(seccoes[:50])
                    res = model.generate_content(prompt)
                    st.markdown(res.text)
                except Exception as e:
                    st.error(f"Erro na IA: {e}")
            else: st.error("Nenhum link útil encontrado.")
