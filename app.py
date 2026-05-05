import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import google.generativeai as genai

# Configuração da página
st.set_page_config(page_title="Classificador Expert", layout="wide")
st.title("🎯 Classificador de Categorias")

# GESTÃO DA API KEY
api_key = st.sidebar.text_input("Gemini API Key:", type="password") or st.secrets.get("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key.strip())

LABELS = "Adult, American Football, Animals, Anime, Auto, Baseball, Basket, Beauty, Betting, Blog, Business, Casino, Celebrities, Chat Groups, Combat, Cosmetics, Cricket, Crypto, Culinary, Dating, Deco/Arch, E-Commerce, Education, Entertainment, Esoteric, Esports, Fashion, File Sharing, Finance, Football, Games, Golf, Health, Hockey, Horses, Humor, Jobs, Judicial, Legal, Lifestyle, Literature, Loans/Credits, Lottery, Marketing, MMA, Motorsports, Music, News, Politics, Quotes, Radio, Religion, Rugby, Sports, streaming, Technology, Tennis, Tourism, Weather, Well-Being"

def get_clean_sections(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
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
                # Foca em URLs de categorias (curtas)
                if 1 <= len(path_parts) <= 2:
                    links.add(full_url)
        return sorted(list(links))
    except Exception as e:
        st.error(f"Erro ao acessar o site: {e}")
        return []

url_input = st.text_input("URL do Site (ex: https://nypost.com):")

if st.button("Classificar com Precisão"):
    if not api_key:
        st.error("Por favor, insira a Gemini API Key na barra lateral!")
    elif url_input:
        with st.spinner("A analisar estrutura do site..."):
            seccoes = get_clean_sections(url_input)
            
            if seccoes:
                st.info(f"Encontrados {len(seccoes)} links relevantes. Consultando IA...")
                
                try:
                    # Tenta primeiro o Flash (mais rápido/barato)
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash-latest')
                        # Teste simples para ver se o modelo responde
                        test_prompt = "Ok"
                        model.generate_content(test_prompt)
                    except:
                        # Se falhar, usa o Pro (mais compatível com versões antigas da biblioteca)
                        model = genai.GenerativeModel('gemini-pro')
                    
                    prompt = f"""
                    Age como um Taxonomista de Conteúdo especializado. 
                    Atribui APENAS UMA label da lista abaixo para cada URL fornecida.
                    
                    LISTA DE LABELS PERMITIDAS:
                    [{LABELS}]
                    
                    REGRAS DE CLASSIFICAÇÃO:
                    - URLs com /jets/, /giants/, /nfl/ -> 'American Football'
                    - URLs com /yankees/, /mets/, /mlb/ -> 'Baseball'
                    - URLs com /knicks/, /nets/, /nba/ -> 'Basket'
                    - URLs com /p6/, /page-six/ ou fofocas -> 'Celebrities'
                    - URLs com /media/ ou publicidade -> 'Marketing'
                    - Se o conteúdo for político, usa 'Politics' prioritariamente.
                    
                    RESPOSTA ESPERADA:
                    URL - LABEL
                    
                    LISTA DE URLs PARA CLASSIFICAR:
                    """ + "\n".join(seccoes[:60]) # Limite de 60 para não estourar o contexto
                    
                    res = model.generate_content(prompt)
                    
                    st.subheader("🎯 Classificação Final:")
                    st.code(res.text, language="text")
                    
                except Exception as e:
                    st.error(f"Erro crítico na IA: {e}")
                    st.info("Dica: Verifique se sua API Key é válida e se você tem saldo/quota no Google AI Studio.")
            else:
                st.warning("Não foi possível extrair links de categorias deste site. Tente outro formato de URL.")
