import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuração da página para aproveitar o espaço do monitor
st.set_page_config(page_title="Oficina SV - Controladoria", layout="wide")

# Título Principal
st.title("🚜 Gestão de Oficina - SV")

# Estabelece conexão com o Google Sheets (usando as Secrets do Streamlit Cloud)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Lê as abas da planilha
    df_frota = conn.read(worksheet="frota")
    df_mov = conn.read(worksheet="movimentacao")
    
    # Garante que as listas não venham vazias para o formulário
    lista_frotas = df_frota['FROTA'].unique().tolist() if not df_frota.empty else ["Cadastre a frota na planilha"]
    
    # Lógica do número sequencial de O.S.
    if not df_mov.empty and 'OS_NUM' in df_mov.columns:
        proximo_numero = int(df_mov['OS_NUM'].max()) + 1
    else:
        proximo_numero = 1
        
except Exception as e:
    st.error(f"Erro de Conexão: Verifique se o link da planilha nos 'Secrets' está correto. Detalhe: {e}")
    lista_frotas = ["Erro ao carregar"]
    proximo_numero = 0
    df_mov = pd.DataFrame()

# --- BARRA LATERAL (Histórico e Status) ---
with st.sidebar:
    st.header("🕒 Últimos Serviços")
    # Container vazio para evitar o erro 'removeChild' no navegador
    sidebar_container = st.container()
    
    if not df_mov.empty:
        # Pega as últimas 5 movimentações e inverte a ordem (mais recente no topo)
        # Selecionamos apenas colunas essenciais para não poluir a barra lateral
        historico = df_mov.tail(5)[['FROTA', 'MECANICO', 'STATUS']].iloc[::-1]
        sidebar_container.table(historico)
    else:
        sidebar_container.info("Nenhum lançamento registrado na aba 'movimentacao'.")

# --- FORMULÁRIO PRINCIPAL ---
with st.form("form_oficina", clear_on_submit=True):
    # Cabeçalho do Formulário com o número da OS em destaque
    col_titulo, col_os = st.columns([3, 1])
    with col_os:
        st.metric("O.S. ATUAL", f"#{proximo_numero:04d}")

    # Organização em colunas para facilitar o preenchimento no PC
    c1, c2 = st.columns(2)
    
    with c1:
        frota_sel = st.selectbox("Selecione o Equipamento", options=lista_frotas)
        mecanico = st.text_input("Nome do Mecânico")
        sistema = st.selectbox("Sistema Afetado", ["Motor", "Hidráulico", "Elétrico", "Pneus", "Transmissão", "Suspensão", "Implemento", "Outros"])
        
    with c2:
        horimetro = st.number_input("Horímetro ou KM Atual", min_value=0.0, step=0.1, format="%.1f")
        tipo_manut = st.selectbox("Tipo de Manutenção", ["CORRETIVA", "PREVENTIVA", "INTERNA", "PREDITIVA"])
        status_os = st.radio("Status do Equipamento", ["FINALIZADO", "PENDENTE (EM ABERTO)"], horizontal=True)

    descricao = st.text_area("Descrição detalhada do serviço e peças aplicadas")

    # Botão de Envio
    enviar = st.form_submit_button("✅ SALVAR NO SISTEMA")

    if enviar:
        if not mecanico or not descricao or proximo_numero == 0:
            st.warning("Atenção: Nome do mecânico e Descrição são obrigatórios.")
        else:
            # Organiza os dados para salvar
            novo_registro = pd.DataFrame([{
                "OS_NUM": proximo_numero,
                "DATA": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "FROTA": frota_sel,
                "MECANICO": mecanico.upper(),
                "HORIMETRO": horimetro,
                "SISTEMA": sistema,
                "TIPO": tipo_manut,
                "STATUS": status_os,
                "DESCRICAO": descricao
            }])
            
            try:
                # Envia os dados para a aba 'movimentacao' no Google Sheets
                conn.create(worksheet="movimentacao", data=novo_registro)
                st.success(f"Sucesso! O.S. #{proximo_numero:04d} registrada e salva na nuvem.")
                # Aguarda um momento e recarrega a página para atualizar o histórico lateral
                st.rerun()
            except Exception as error:
                st.error(f"Erro ao salvar na planilha: {error}")

# Rodapé informativo
st.caption("Sistema Oficina SV | Controladoria Bataguassu-MS | Dados salvos diretamente no Google Sheets.")