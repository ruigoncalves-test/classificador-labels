import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Classificador Expert", layout="wide")
st.title("🎯 Classificador de Categorias (Versão Estável)")

# 2. GESTÃO DA API KEY (Barra Lateral)
st.sidebar.header("Configurações")
api_key = st.sidebar.text_input("Gemini API Key:", type="password") or st.secrets.get("GEMINI_API_KEY")

LABELS = "Adult, American Football, Animals, Anime, Auto, Baseball, Basket, Beauty, Betting, Blog, Business, Casino, Celebrities, Chat Groups, Combat, Cosmetics, Cricket, Crypto, Culinary, Dating, Deco/Arch, E-Commerce, Education, Entertainment, Esoteric, Esports, Fashion, File Sharing, Finance, Football, Games, Golf, Health, Hockey, Horses, Humor, Jobs, Judicial, Legal, Lifestyle, Literature, Loans/Credits, Lottery, Marketing, MMA, Motorsports, Music, News, Politics, Quotes, Radio, Religion, Rugby, Sports, streaming, Technology, Tennis, Tourism, Weather, Well-Being"

def get_clean_sections(url):
    try:
        # Cabeçalho para evitar bloqueios por bots
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        r = requests.get(url, headers=headers, timeout=15)
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
                # Pega apenas links de 1 ou 2 níveis (ex: site.com/esportes ou site.com/esportes/futebol)
                if 1 <= len(path_parts) <= 2:
                    links.add(full_url)
        return sorted(list(links))
    except Exception as e:
        st.error(f"Erro ao extrair links do site: {e}")
        return []

def call_gemini_rest(key, prompt):
    # FORÇAMOS O ENDPOINT V1 (ESTÁVEL) - Isto elimina o erro 404 de versão
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.1, # Menor criatividade para maior precisão na categoria
        }
    }
    
    headers = {'Content-Type': 'application/json'}
    
    # Fazemos o pedido diretamente ao servidor da Google
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        # Se o Flash falhar, tentamos o Pro como backup no endpoint estável
        url_pro = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={key}"
        response_pro = requests.post(url_pro, headers=headers, json=payload)
        
        if response_pro.status_code == 200:
            return response_pro.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            erro_detalhado = response_pro.json().get('error', {}).get('message', 'Erro desconhecido')
            raise Exception(f"Erro na API Google: {response_pro.status_code} - {erro_detalhado}")

# 3. INTERFACE PRINCIPAL
url_input = st.text_input("Insira a URL (ex: https://nypost.com):")

if st.button("🚀 Iniciar Classificação Expert"):
    if not api_key:
        st.warning("⚠️ Insira a Gemini API Key na barra lateral esquerda.")
    elif not url_input:
        st.warning("⚠️ Insira uma URL válida.")
    else:
        with st.spinner("1/2: A ler estrutura do site..."):
            links_extraidos = get_clean_sections(url_input)
            
        if links_extraidos:
            st.success(f"Encontrados {len(links_extraidos)} links de categorias.")
            
            # Construção do Prompt
            prompt_final = f"""Age como um Taxonomista. Atribui uma label desta lista [{LABELS}] para cada URL.
            Responde APENAS no formato: URL - LABEL.
            
            Lista de URLs:
            {chr(10).join(links_extraidos[:60])}"""
            
            try:
                with st.spinner("2/2: A consultar Inteligência Artificial (Endpoint Estável)..."):
                    resultado = call_gemini_rest(api_key.strip(), prompt_final)
                
                st.subheader("✅ Resultado da Classificação:")
                st.code(resultado, language="text")
                
            except Exception as e:
                st.error(f"❌ Falha na IA: {e}")
        else:
            st.error("Não foram encontrados links de categorias. Tente outro site ou verifique o formato da URL.")
