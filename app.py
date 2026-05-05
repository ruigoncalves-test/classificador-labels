import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import google.generativeai as genai

st.set_page_config(page_title="Classificador Expert", layout="wide")
st.title("🎯 Classificador de Categorias")

# GESTÃO DA API KEY
api_key = st.sidebar.text_input("Gemini API Key:", type="password") or st.secrets.get("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key.strip())

LABELS = "Adult, American Football, Animals, Anime, Auto, Baseball, Basket, Beauty, Betting, Blog, Business, Casino, Celebrities, Chat Groups, Combat, Cosmetics, Cricket, Crypto, Culinary, Dating, Deco/Arch, E-Commerce, Education, Entertainment, Esoteric, Esports, Fashion, File Sharing, Finance, Football, Games, Golf, Health, Hockey, Horses, Humor, Jobs, Judicial, Legal, Lifestyle, Literature, Loans/Credits, Lottery, Marketing, MMA, Motorsports, Music, News, Politics, Quotes, Radio, Religion, Rugby, Sports, streaming, Technology, Tennis, Tourism, Weather, Well-Being"

def get_clean_sections(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status() # Garante que o request foi bem sucedido
        soup = BeautifulSoup(r.text, 'html.parser')
        domain = urlparse(url).netloc
        
        ignore_list = ['/author/', '/contact', '/settings', '/subscribe', '/privacy', '/terms', '/login', '/about', '/newsletter']
        
        links = set()
        for a in soup.find_all('a', href=True):
            full_url = urljoin(url, a['href']).split('?')[0].split('#')[0].rstrip('/')
            parsed = urlparse(full_url)
            
            if parsed.netloc == domain and not any(x in full_url for x in ignore_list):
                path_parts = [p for p in parsed.path.split('/') if p]
                if 1 <= len(path_parts) <= 2:
                    links.add(full_url)
        return sorted(list(links))
    except Exception as e:
        st.error(f"Erro ao acessar a URL: {e}")
        return []

url_input = st.text_input("URL do Site (ex: https://nypost.com):")

if st.button("Classificar com Precisão"):
    if not api_key:
        st.error("Insere a API Key!")
    elif url_input:
        with st.spinner("A analisar site..."):
            seccoes = get_clean_sections(url_input)
            
            if seccoes:
                st.info(f"Filtrados {len(seccoes)} links. A chamar IA...")
                
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    prompt = f"""
                    Age como um Taxonomista de Conteúdo. 
                    Atribui a label mais específica da lista: [{LABELS}]
                    
                    REGRAS:
                    - /jets/, /giants/, /nfl/ -> 'American Football'
                    - /yankees/, /mets/, /mlb/ -> 'Baseball'
                    - /knicks/, /nets/, /nba/ -> 'Basket'
                    - /p6/, /page-six/ -> 'Celebrities'
                    - /media/ -> 'Marketing'
                    - Se for política, usa 'Politics' (mesmo que esteja em News).
                    
                    Formato: URL - LABEL
                    
                    LISTA:
                    """ + "\n".join(seccoes[:60])
                    
                    res = model.generate_content(prompt)
                    st.subheader("Resultados:")
                    st.markdown(res.text)
                except Exception as e:
                    st.error(f"Erro na IA: {e}")
            else:
                st.error("Nenhum link útil encontrado ou erro de conexão.")
