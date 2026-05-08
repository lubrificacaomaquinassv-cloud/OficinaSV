import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import traceback

# Configuração da página
st.set_page_config(page_title="Oficina SV - Controladoria", layout="wide")

# ── Estilização CSS para Barra Lateral mais estreita e visual profissional ──
st.markdown("""
    <style>
        /* Ajustar largura da barra lateral */
        [data-testid="stSidebar"] {
            min-width: 280px;
            max-width: 280px;
        }
        /* Reduzir padding do topo para ganhar espaço */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 1rem;
        }
        /* Estilo para a tabela lateral ficar mais compacta */
        .stTable {
            font-size: 12px !important;
        }
        /* Ajustar métricas */
        [data-testid="stMetricValue"] {
            font-size: 24px;
        }
    </style>
""", unsafe_allow_html=True)

# ── Logo + Título ──────────────────────────────────────────────
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    st.image("https://i.postimg.cc/Y9X7ddnb/LOGO-BP.jpg", width=100)
with col_titulo:
    st.title("🚜 Gestão de Ordem de Serviços Interno - SV")
    st.caption("Controladoria Bataguassu-MS")

st.divider()

# ── Conexão e Carregamento de Dados ────────────────────────────
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_frota = conn.read(worksheet="FROTA", ttl=120)
    df_mov   = conn.read(worksheet="MOVIMENTACAO", ttl=5)
    
    # Garantir colunas novas
    for col in ["HORA_ENTRADA", "HORA_SAIDA", "FOTO_URL"]:
        if col not in df_mov.columns:
            df_mov[col] = ""

    if not df_frota.empty:
        lista_frotas = (
            df_frota['FROTA'].astype(str) + " - " + df_frota['DESCRICAO'].astype(str)
        ).dropna().unique().tolist()
    else:
        lista_frotas = ["Cadastre a frota na planilha"]

    conexao_ok = True

except Exception as e:
    st.error(f"Erro de Conexão. Detalhe: {repr(e)}")
    st.code(traceback.format_exc())
    lista_frotas = ["Erro ao carregar"]
    df_mov = pd.DataFrame()
    conexao_ok = False

# ── Lógica de Edição / Fechamento de OS ────────────────────────
os_para_editar = None
if conexao_ok and not df_mov.empty:
    df_pendentes = df_mov[df_mov['STATUS'].str.contains("PENDENTE", na=False, case=False)]
    
    with st.sidebar:
        st.image("https://i.postimg.cc/Y9X7ddnb/LOGO-BP.jpg", width=120)
        st.divider()
        st.subheader("🛠️ Finalizar OS")
        
        if not df_pendentes.empty:
            opcoes_pendentes = ["--- Selecione ---"] + (
                df_pendentes['OS_NUM'].astype(str) + " - " + df_pendentes['FROTA'].astype(str).str[:15] + "..."
            ).tolist()
            
            selecao = st.selectbox("OS Pendentes:", opcoes_pendentes)
            
            if selecao != "--- Selecione ---":
                os_num_sel = int(selecao.split(" - ")[0])
                os_para_editar = df_mov[df_mov['OS_NUM'] == os_num_sel].iloc[0]
                st.warning(f"Editando OS #{os_num_sel:04d}")
                if st.button("✖ Cancelar Edição"):
                    st.rerun()
        else:
            st.info("Sem OS pendentes.")

# Definir número da OS
if os_para_editar is not None:
    proximo_numero = int(os_para_editar['OS_NUM'])
    modo_edicao = True
else:
    if not df_mov.empty and 'OS_NUM' in df_mov.columns:
        proximo_numero = int(pd.to_numeric(df_mov['OS_NUM'], errors='coerce').max()) + 1
    else:
        proximo_numero = 1
    modo_edicao = False

# ── Formulário Principal ───────────────────────────────────────
with st.form("form_oficina", clear_on_submit=not modo_edicao):
    col_t, col_os = st.columns([3, 1])
    with col_os:
        label_os = "EDITANDO O.S." if modo_edicao else "O.S. ATUAL"
        st.metric(label_os, f"#{proximo_numero:04d}")

    c1, c2 = st.columns(2)

    with c1:
        idx_frota = 0
        if modo_edicao:
            try: idx_frota = lista_frotas.index(os_para_editar['FROTA'])
            except: idx_frota = 0
        
        frota_sel = st.selectbox("Equipamento", options=lista_frotas, index=idx_frota)
        mecanico  = st.text_input("Mecânico", value=os_para_editar['MECANICO'] if modo_edicao else "")
        
        sistemas = ["Motor", "Hidráulico", "Elétrico", "Pneus", "Transmissão", "Suspensão", "Implemento", "Outros"]
        idx_sistema = 0
        if modo_edicao:
            try: idx_sistema = sistemas.index(os_para_editar['SISTEMA'])
            except: idx_sistema = 0
        sistema = st.selectbox("Sistema Afetado", sistemas, index=idx_sistema)
        
        # Horas lado a lado para economizar espaço
        ch1, ch2 = st.columns(2)
        with ch1:
            h_entrada = st.text_input("Hora Entrada", value=os_para_editar['HORA_ENTRADA'] if modo_edicao else "", placeholder="08:00")
        with ch2:
            h_saida   = st.text_input("Hora Saída", value=os_para_editar['HORA_SAIDA'] if modo_edicao else "", placeholder="17:30")

    with c2:
        horimetro  = st.number_input("Horímetro / KM", min_value=0.0, step=0.1, format="%.1f", 
                                     value=float(os_para_editar['HORIMETRO']) if modo_edicao else 0.0)
        
        tipos = ["CORRETIVA", "PREVENTIVA", "INTERNA", "PREDITIVA"]
        idx_tipo = 0
        if modo_edicao:
            try: idx_tipo = tipos.index(os_para_editar['TIPO'])
            except: idx_tipo = 0
        tipo_manut = st.selectbox("Tipo Manutenção", tipos, index=idx_tipo)
        
        status_opcoes = ["FINALIZADO", "PENDENTE (EM ABERTO)"]
        idx_status = 0
        if modo_edicao:
            try: idx_status = status_opcoes.index(os_para_editar['STATUS'])
            except: idx_status = 0
        status_os = st.radio("Status Equipamento", status_opcoes, index=idx_status, horizontal=True)
        
        foto_url = st.text_input("URL da Foto", value=os_para_editar['FOTO_URL'] if modo_edicao else "", placeholder="Link da imagem")

    descricao = st.text_area("Descrição do Serviço e Peças", max_chars=300, value=os_para_editar['DESCRICAO'] if modo_edicao else "")
    observacao = st.text_area("Observação", max_chars=200, value=os_para_editar['OBSERVACAO'] if modo_edicao else "")

    texto_botao = "💾 ATUALIZAR O.S." if modo_edicao else "✅ SALVAR NO SISTEMA"
    enviar = st.form_submit_button(texto_botao, use_container_width=True)

    if enviar:
        if not mecanico.strip() or not descricao.strip():
            st.warning("⚠️ Preencha o Mecânico e a Descrição.")
        elif not conexao_ok:
            st.error("❌ Sem conexão com a planilha.")
        else:
            dados_os = {
                "OS_NUM":      proximo_numero,
                "DATA":        os_para_editar['DATA'] if modo_edicao else datetime.now().strftime("%d/%m/%Y %H:%M"),
                "FROTA":       frota_sel,
                "MECANICO":    mecanico.upper(),
                "HORIMETRO":   horimetro,
                "SISTEMA":     sistema,
                "TIPO":        tipo_manut,
                "STATUS":      status_os,
                "DESCRICAO":   descricao,
                "OBSERVACAO":  observacao,
                "HORA_ENTRADA": h_entrada,
                "HORA_SAIDA":   h_saida,
                "FOTO_URL":     foto_url
            }

            try:
                if modo_edicao:
                    idx_linha = df_mov.index[df_mov['OS_NUM'] == proximo_numero].tolist()[0]
                    for key, val in dados_os.items():
                        df_mov.at[idx_linha, key] = val
                    df_final = df_mov
                else:
                    novo_registro = pd.DataFrame([dados_os])
                    df_final = pd.concat([df_mov, novo_registro], ignore_index=True)
                
                conn.update(worksheet="MOVIMENTACAO", data=df_final)
                st.success(f"✅ O.S. #{proximo_numero:04d} salva!")
                st.rerun()
            except Exception as error:
                st.error(f"❌ Erro: {repr(error)}")

# ── Sidebar: Histórico Compacto ───────────────────────────────
with st.sidebar:
    st.divider()
    st.subheader("🕒 Últimas OS")
    if not df_mov.empty:
        # Mostrar apenas colunas essenciais para não poluir
        cols_disp = ['OS_NUM','FROTA','STATUS']
        # Formatar para exibição compacta
        df_view = df_mov[cols_disp].tail(8).iloc[::-1].copy()
        df_view['FROTA'] = df_view['FROTA'].str[:10] + "..."
        st.table(df_view)
    else:
        st.info("Sem registros.")

st.divider()
st.caption("Sistema Oficina SV | Controladoria Bataguassu-MS")
