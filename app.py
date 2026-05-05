import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import google.generativeai as genai

st.set_page_config(page_title="Classificador de Alta Precisão", layout="wide")
st.title("🎯 Classificador de Categorias (Modo Expert)")

# GESTÃO DA API KEY
api_key = st.secrets.get("GEMINI_API_KEY") or st.sidebar.text_input("Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key.strip())

LABELS = "Adult, American Football, Animals, Anime, Auto, Baseball, Basket, Beauty, Betting, Blog, Business, Casino, Celebrities, Chat Groups, Combat, Cosmetics, Cricket, Crypto, Culinary, Dating, Deco/Arch, E-Commerce, Education, Entertainment, Esoteric, Esports, Fashion, File Sharing, Finance, Football, Games, Golf, Health, Hockey, Horses, Humor, Jobs, Judicial, Legal, Lifestyle, Literature, Loans/Credits, Lottery, Marketing, MMA, Motorsports, Music, News, Politics, Quotes, Radio, Religion, Rugby, Sports, streaming, Technology, Tennis, Tourism, Weather, Well-Being"

def get_clean_sections(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        domain = urlparse(url).netloc
        
        # Palavras a ignorar para limpar o lixo
        ignore_list = [
            '/author/', '/contact', '/settings', '/subscribe', '/login', '/account', 
            '/help', '/privacy', '/terms', '/newsletter', '/sitemap', '/advertise',
            '/about', '/search', '/tips', '/covers', '/archives', '/apps'
        ]
        
        links = set()
        for a in soup.find_all('a', href=True):
            full_url = urljoin(url, a['href']).split('?')[0].split('#')[0].rstrip('/')
            parsed = urlparse(full_url)
            
            # Filtros de relevância
            if parsed.netloc == domain:
                # Se não estiver na lista de ignorados e tiver uma estrutura de categoria
                if not any(x in full_url for x in ignore_list):
                    path_parts = [p for p in parsed.path.split('/') if p]
                    # Foca em categorias (1 nível) ou subcategorias (2 níveis)
                    if 1 <= len(path_parts) <= 2:
                        links.add(full_url)
        
        return sorted(list(links))
    except:
        return []

url_input = st.text_input("URL do Site:", placeholder="https://nypost.com")

if st.button("Classificar com Precisão"):
    if not api_key:
        st.error("Insere a API Key!")
    elif url_input:
        with st.spinner("A filtrar secções relevantes..."):
            seccoes = get_clean_sections(url_input)
            
            if seccoes:
                st.info(f"Filtrados {len(seccoes)} links relevantes. A classificar...")
                
                # Forçamos o modelo a ser um "Taxonomista de Conteúdo"
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""
                Age como um especialista em SEO e Taxonomia de Media. 
                O teu objetivo é atribuir a label mais específica possível a partir desta lista:
                [{LABELS}]

                REGRAS DE CLASSIFICAÇÃO:
                1. Analisa o nome da pasta no URL. Ex: '/nfl/' é 'American Football', não 'Sports'.
                2. Se o URL for de notícias gerais mas focar em política (ex: /politics/), usa 'Politics'.
                3. Ignora URLs que sejam administrativos ou institucionais (mesmo que tenham passado pelo filtro).
                4. Se o URL for um nome de equipa (ex: /jets/, /yankees/), identifica a modalidade correspondente.
                5. 'P6' ou 'Page Six' é sempre 'Celebrities'.
                6. 'Media' neste contexto é 'Marketing'.

                Responde APENAS no formato:
                URL - LABEL (Breve explicação se necessário)

                LISTA DE URLS:
                """ + "\n".join(seccoes[:60])
                
                try:
                    res = model.generate_content(prompt)
                    st.subheader("Resultados:")
                    st.markdown(res.text)
                except Exception as e:
                    st.error(f"Erro na IA: {e}")
            else:
                st.error("Não foram encontrados links de categorias limpos.")
