import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import google.generativeai as genai

st.set_page_config(page_title="Classificador Estável", layout="wide")
st.title("🏷️ Classificador de Categorias")

# GESTÃO DA API KEY
api_key = st.secrets.get("GEMINI_API_KEY") or st.sidebar.text_input("Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key.strip())

# LISTA DE LABELS
LABELS = "Adult, American Football, Animals, Anime, Auto, Baseball, Basket, Beauty, Betting, Blog, Business, Casino, Celebrities, Chat Groups, Combat, Cosmetics, Cricket, Crypto, Culinary, Dating, Deco/Arch, E-Commerce, Education, Entertainment, Esoteric, Esports, Fashion, File Sharing, Finance, Football, Games, Golf, Health, Hockey, Horses, Humor, Jobs, Judicial, Legal, Lifestyle, Literature, Loans/Credits, Lottery, Marketing, MMA, Motorsports, Music, News, Politics, Quotes, Radio, Religion, Rugby, Sports, streaming, Technology, Tennis, Tourism, Weather, Well-Being"

def get_sections(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        domain = urlparse(url).netloc
        links = {urljoin(url, a['href']).split('#')[0].rstrip('/') for a in soup.find_all('a', href=True) 
                 if urlparse(urljoin(url, a['href'])).netloc == domain}
        return sorted([l for l in links if len(urlparse(l).path.split('/')) <= 3 and l != url])
    except: return []

url_input = st.text_input("URL do Site:")

if st.button("Classificar"):
    if not api_key: 
        st.error("Falta a API Key!")
    elif url_input:
        with st.spinner("A analisar site..."):
            seccoes = get_sections(url_input)
            
            if seccoes:
                try:
                    # Tenta encontrar um modelo disponível na tua conta
                    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    
                    # Seleciona o 1.5-flash se existir, senão o gemini-pro, senão o primeiro da lista
                    selected_model = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else \
                                     'models/gemini-pro' if 'models/gemini-pro' in available_models else \
                                     available_models[0]
                    
                    model = genai.GenerativeModel(selected_model)
                    st.info(f"A usar modelo: {selected_model}")
                    
                    prompt = f"Atribui uma label da lista [{LABELS}] a cada URL (Formato: URL - Label):\n" + "\n".join(seccoes[:40])
                    res = model.generate_content(prompt)
                    st.text_area("Resultados:", value=res.text, height=400)
                    
                except Exception as e:
                    st.error(f"Erro na IA: {e}")
            else:
                st.error("Nenhum link encontrado.")
