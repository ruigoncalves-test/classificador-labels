import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import google.generativeai as genai

# 1. Configuração da página
st.set_page_config(page_title="Classificador Expert", layout="wide")
st.title("🎯 Classificador de Categorias")

# 2. GESTÃO DA API KEY
api_key = st.sidebar.text_input("Gemini API Key:", type="password") or st.secrets.get("GEMINI_API_KEY")

LABELS = "Adult, American Football, Animals, Anime, Auto, Baseball, Basket, Beauty, Betting, Blog, Business, Casino, Celebrities, Chat Groups, Combat, Cosmetics, Cricket, Crypto, Culinary, Dating, Deco/Arch, E-Commerce, Education, Entertainment, Esoteric, Esports, Fashion, File Sharing, Finance, Football, Games, Golf, Health, Hockey, Horses, Humor, Jobs, Judicial, Legal, Lifestyle, Literature, Loans/Credits, Lottery, Marketing, MMA, Motorsports, Music, News, Politics, Quotes, Radio, Religion, Rugby, Sports, streaming, Technology, Tennis, Tourism, Weather, Well-Being"

def get_clean_sections(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
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
        st.error(f"Erro no scraping: {e}")
        return []

# 3. Interface de entrada
url_input = st.text_input("URL do Site (ex: https://nypost.com):")

if st.button("Executar Classificação"):
    if not api_key:
        st.error("Falta a API Key na barra lateral!")
    elif url_input:
        with st.spinner("A processar estrutura e consultando IA..."):
            
            # CONFIGURAÇÃO DIRETA
            genai.configure(api_key=api_key.strip())
            
            seccoes = get_clean_sections(url_input)
            
            if seccoes:
                try:
                    # Usando o nome de modelo que tem maior compatibilidade histórica
                    # Se 'gemini-1.5-flash' falhar, ele tentará o 'gemini-pro' automaticamente
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        # Teste rápido de sanidade
                        model.generate_content("test")
                    except:
                        model = genai.GenerativeModel('gemini-pro')
                    
                    prompt = f"""Age como um Taxonomista. Atribui uma label desta lista [{LABELS}] para cada URL.
                    Responde no formato: URL - LABEL
                    
                    URLs:
                    {chr(10).join(seccoes[:50])}"""
                    
                    # Chamada simples sem argumentos complexos para evitar erros de versão
                    res = model.generate_content(prompt)
                    
                    st.subheader("Resultados:")
                    st.code(res.text)
                    
                except Exception as e:
                    st.error(f"Erro na IA: {e}")
                    st.info("Dica técnica: Verifique se o pacote google-generativeai está instalado corretamente.")
            else:
                st.warning("Nenhum link de categoria encontrado.")
