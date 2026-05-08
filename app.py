import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import traceback

# Configuração da página
st.set_page_config(page_title="Oficina SV - Controladoria", layout="wide")

# ── Estilização CSS ──
st.markdown("""
    <style>
        [data-testid="stSidebar"] { min-width: 280px; max-width: 280px; }
        .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
        .stTable { font-size: 12px !important; }
        [data-testid="stMetricValue"] { font-size: 24px; }
        
        /* Garantir que o título não quebre linha de forma feia */
        h1 {
            font-size: 2.0rem !important;
            white-space: nowrap;
        }
    </style>
""", unsafe_allow_html=True)

# ── Cabeçalho Nativo e Estável (Sem cortes) ───────────────────
# Usando colunas nativas com uma proporção que dá bastante espaço para ambos
col_logo, col_titulo = st.columns([1.2, 5.8])

with col_logo:
    # Usando o componente nativo que é o mais seguro contra cortes
    st.image("https://i.postimg.cc/Y9X7ddnb/LOGO-BP.jpg", width=130)

with col_titulo:
    # Título e legenda alinhados nativamente
    st.markdown("<div style='padding-top: 10px;'>", unsafe_allow_html=True)
    st.title("Gestão de Ordem de Serviço Interna - SV")
    st.caption("Controladoria Bataguassu-MS")
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# ── Conexão e Carregamento de Dados ────────────────────────────
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_frota = conn.read(worksheet="FROTA", ttl=120)
    df_mov   = conn.read(worksheet="MOVIMENTACAO", ttl=5)
    
    for col in ["HORA_ENTRADA", "HORA_SAIDA", "FOTO_URL"]:
        if col not in df_mov.columns:
            df_mov[col] = ""
    
    if not df_mov.empty:
        df_mov['OS_NUM'] = pd.to_numeric(df_mov['OS_NUM'], errors='coerce')

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
    df_pendentes = df_mov[df_mov['STATUS'].str.contains("PENDENTE", na=False, case=False)].copy()
    
    with st.sidebar:
        st.image("https://i.postimg.cc/Y9X7ddnb/LOGO-BP.jpg", width=120)
        st.divider()
        st.subheader("🛠️ Finalizar OS")
        
        if not df_pendentes.empty:
            opcoes_pendentes = ["--- Selecione ---"]
            for _, row in df_pendentes.iterrows():
                num_limpo = int(float(row['OS_NUM']))
                frota_resumo = str(row['FROTA'])[:15]
                opcoes_pendentes.append(f"{num_limpo} - {frota_resumo}...")
            
            selecao = st.selectbox("OS Pendentes:", opcoes_pendentes)
            
            if selecao != "--- Selecione ---":
                try:
                    os_num_sel = int(float(selecao.split(" - ")[0]))
                    os_para_editar = df_mov[df_mov['OS_NUM'] == os_num_sel].iloc[0]
                    st.warning(f"Editando OS #{os_num_sel:04d}")
                    if st.button("✖ Cancelar Edição"):
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro ao carregar OS: {e}")
        else:
            st.info("Sem OS pendentes.")

# Definir número da OS
if os_para_editar is not None:
    proximo_numero = int(float(os_para_editar['OS_NUM']))
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
                
                df_final['OS_NUM'] = df_final['OS_NUM'].astype(int)
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
        cols_disp = ['OS_NUM','FROTA','STATUS']
        df_view = df_mov[cols_disp].tail(8).iloc[::-1].copy()
        df_view['OS_NUM'] = df_view['OS_NUM'].apply(lambda x: int(float(x)) if pd.notnull(x) else x)
        df_view['FROTA'] = df_view['FROTA'].str[:10] + "..."
        st.table(df_view)
    else:
        st.info("Sem registros.")

st.divider()
st.caption("Sistema Oficina SV | Controladoria Bataguassu-MS")
