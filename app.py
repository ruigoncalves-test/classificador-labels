import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from openai import OpenAI

# Configurações iniciais
st.set_page_config(page_title="Auto-Labeler Pro", page_icon="🏷️")
st.title("🏷️ Classificador Automático de Secções")

# Sidebar para configurações
st.sidebar.header("Configurações")
api_key = st.sidebar.text_input("OpenAI API Key", type="password")
model_choice = st.sidebar.selectbox("Modelo", ["gpt-4o", "gpt-4-turbo"])

# A tua lista de labels estrita
LABELS = "Adult, American Football, Animals, Anime, Auto, Baseball, Basket, Beauty, Betting, Blog, Business, Casino, Celebrities, Chat Groups, Combat, Cosmetics, Cricket, Crypto, Culinary, Dating, Deco/Arch, E-Commerce, Education, Entertainment, Esoteric, Esports, Fashion, File Sharing, Finance, Football, Games, Golf, Health, Hockey, Horses, Humor, Jobs, Judicial, Legal, Lifestyle, Literature, Loans/Credits, Lottery, Marketing, MMA, Motorsports, Music, News, Politics, Quotes, Radio, Religion, Rugby, Sports, streaming, Technology, Tennis, Tourism, Weather, Well-Being"

def get_site_sections(url):
    """Extrai links únicos que parecem ser secções do site."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        domain = urlparse(url).netloc
        links = set()
        
        for a in soup.find_all('a', href=True):
            full_url = urljoin(url, a['href'])
            # Filtra apenas links do próprio domínio e ignora fragmentos (#)
            if urlparse(full_url).netloc == domain and '#' not in full_url:
                # Limpeza básica para evitar links de artigos individuais muito longos
                if len(urlparse(full_url).path.split('/')) <= 3:
                    links.add(full_url)
        
        return sorted(list(links))
    except Exception as e:
        st.error(f"Erro ao ler o site: {e}")
        return []

# Interface principal
url_input = st.text_input("Insere o URL principal do site:", placeholder="https://nypost.com")

if st.button("Analisar e Classificar"):
    if not api_key:
        st.warning("Insere a tua API Key na barra lateral.")
    elif url_input:
        with st.spinner("A extrair secções do site..."):
            seccoes = get_site_sections(url_input)
            
        if seccoes:
            st.write(f"Encontradas {len(seccoes)} secções potenciais. A classificar...")
            
            client = OpenAI(api_key=api_key)
            
            # Prompt estruturado para garantir o teu raciocínio
            prompt_sistema = f"""
            Tu és um analista de taxonomia de sites. Receberás uma lista de URLs.
            A tua tarefa é atribuir a label mais específica possível da lista abaixo:
            LABELS: {LABELS}
            
            REGRAS CRÍTICAS:
            1. Prioridade à especificidade: Se o URL é de 'mlb', a label é 'Baseball', não 'Sports'.
            2. Se o foco for notícias políticas, usa 'Politics' mesmo que seja uma subcategoria de 'News'.
            3. 'Copyright' para pirataria/downloads de filmes.
            4. 'MP3' para downloads de música.
            5. Formato de resposta: URL - Label
            """
            
            prompt_usuario = f"Classifica estes URLs: \n" + "\n".join(seccoes[:50]) # Limite de 50 para evitar custos excessivos
            
            try:
                response = client.chat.completions.create(
                    model=model_choice,
                    messages=[
                        {"role": "system", "content": prompt_sistema},
                        {"role": "user", "content": prompt_usuario}
                    ]
                )
                
                st.subheader("Resultado da Classificação:")
                st.code(response.choices[0].message.content)
                
            except Exception as e:
                st.error(f"Erro na IA: {e}")
        else:
            st.error("Não foi possível encontrar links no URL fornecido.")
