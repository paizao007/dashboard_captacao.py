# dashboard_captacao_v3.py

import streamlit as st
import pandas as pd
from io import BytesIO
from apify_client import ApifyClient

# Configuração da página
st.set_page_config(page_title="Captação Imobiliária Salvador", page_icon="🏠", layout="wide")

# --- SEGURANÇA ---
# O Token DEVE ser configurado nos 'Secrets' do Streamlit Cloud para este script funcionar.
try:
    APIFY_API_TOKEN = st.secrets["APIFY_API_TOKEN"]
except Exception:
    st.error("❌ Erro de Configuração: O Token da Apify não foi encontrado nos Secrets do Streamlit.")
    st.info("Por favor, adicione 'APIFY_API_TOKEN' nas configurações avançadas do Streamlit Cloud.")
    st.stop()

ACTOR_ID = "israeloriente/olx-brasil-imoveis-scraper"

st.title("🏠 Painel de Captação - Salvador")
st.sidebar.header("⚙️ Filtros")

# Filtros
localizacao = st.sidebar.selectbox("📍 Bairro", ["Stella Maris", "Praia do Flamengo", "Itapuã", "Pituaçu", "Imbuí"])
tipo_transacao = st.sidebar.radio("💰 Transação", ["Venda", "Aluguel"])
preco_min = st.sidebar.number_input("Preço Mínimo", value=350000)
quartos_min = st.sidebar.slider("Quartos Mínimos", 1, 5, 2)
apenas_particular = st.sidebar.checkbox("✅ Apenas Proprietários", value=True)

if st.button("🔍 Iniciar Captação", use_container_width=True):
    with st.spinner("Buscando leads na OLX..."):
        try:
            client = ApifyClient(APIFY_API_TOKEN)
            loc_slug = localizacao.lower().replace(" ", "-")
            search_url = f"https://olx.com.br/imoveis/{tipo_transacao.lower()}/bahia/salvador/{loc_slug}"
            
            run_input = {
                "startUrls": [{"url": search_url}],
                "maxItems": 50,
                "is_professional": not apenas_particular,
                "minPrice": preco_min,
                "minRooms": quartos_min
            }
            
            run = client.actor(ACTOR_ID).call(run_input=run_input)
            
            if run and run.get('status') == 'SUCCEEDED':
                dataset = client.dataset(run["defaultDatasetId"])
                leads = list(dataset.iterate_items())
                
                if leads:
                    df = pd.DataFrame(leads)
                    st.success(f"✅ {len(df)} leads encontrados!")
                    st.dataframe(df[["title", "price", "rooms", "area", "contact", "url"]].rename(columns={
                        "title": "Título", "price": "Preço", "rooms": "Quartos", "area": "Área", "contact": "Contato"
                    }))
                    
                    # Download Excel
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                    st.download_button("📊 Baixar Excel", output.getvalue(), f"leads_{loc_slug}.xlsx", use_container_width=True)
                else:
                    st.warning("Nenhum imóvel encontrado.")
            else:
                st.error("Falha na execução do scraper.")
        except Exception as e:
            st.error(f"Erro: {e}")

st.markdown("---")
st.caption("Desenvolvido por Manus AI | Captação Inteligente")
