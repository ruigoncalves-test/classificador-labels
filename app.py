import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import google.generativeai as genai
from google.generativeai.types import RequestOptions

# Configuração da página
st.set_page_config(page_title="Classificador Expert", layout="wide")
st.title("🎯 Classificador de Categorias")

# GESTÃO DA API KEY
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

if st.button("Classificar com Precisão"):
    if not api_key:
        st.error("Insere a API Key!")
    elif url_input := st.text_input("URL:", value=st.session_state.get('url', '')): # Pequeno ajuste para persistência
        pass # Apenas para estruturar o fluxo

url_input = st.text_input("URL do Site (ex: https://nypost.com):", key="url_principal")

if st.button("Executar Classificação"):
    if not api_key:
        st.error("Falta a API Key!")
    elif url_input:
        with st.spinner("A processar..."):
            # 1. CONFIGURAÇÃO DA IA (FORÇANDO API V1)
            genai.configure(api_key=api_key.strip())
            
            seccoes = get_clean_sections(url_input)
            
            if seccoes:
                try:
                    # FORÇAMOS A API A NÃO USAR v1beta PARA EVITAR O ERRO 404
                    model = genai.GenerativeModel(model_name='gemini-1.5-flash')
                    
                    prompt = f"""Atribui uma label desta lista [{LABELS}] para cada URL:
                    {chr(10).join(seccoes[:50])}
                    Formato: URL - LABEL"""
                    
                    # Usamos RequestOptions para garantir a versão da API
                    res = model.generate_content(
                        prompt,
                        request_options=RequestOptions(api_version='v1')
                    )
                    
                    st.subheader("Resultados:")
                    st.code(res.text)
                    
                except Exception as e:
                    st.error(f"Erro na IA: {e}")
                    st.info("Tenta atualizar a biblioteca: pip install -U google-generativeai")
            else:
                st.warning("Nenhum link extraído.")
