import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import traceback

st.set_page_config(page_title="Oficina SV - Controladoria", layout="wide")

# ── Logo + Título ──────────────────────────────────────────────
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    st.image("https://i.postimg.cc/Y9X7ddnb/LOGO-BP.jpg", width=110)
with col_titulo:
    st.title("🚜 Gestão de Oficina - SV")
    st.caption("Controladoria Bataguassu-MS")

st.divider()

# ── Conexão ────────────────────────────────────────────────────
try:
    conn = st.connection("gsheets", type=GSheetsConnection)

    df_frota = conn.read(worksheet="frota", usecols=[0, 1, 2, 3], ttl=120)
    df_mov   = conn.read(worksheet="movimentacao", ttl=5)

    lista_frotas = df_frota['FROTA'].dropna().unique().tolist() if not df_frota.empty else ["Cadastre a frota na planilha"]

    if not df_mov.empty and 'OS_NUM' in df_mov.columns:
        proximo_numero = int(pd.to_numeric(df_mov['OS_NUM'], errors='coerce').max()) + 1
    else:
        proximo_numero = 1

    conexao_ok = True

except Exception as e:
    st.error(f"Erro de Conexão. Detalhe: {repr(e)}")
    st.code(traceback.format_exc())
    lista_frotas   = ["Erro ao carregar"]
    proximo_numero = 0
    df_mov         = pd.DataFrame()
    conexao_ok     = False

# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://i.postimg.cc/Y9X7ddnb/LOGO-BP.jpg", width=140)
    st.divider()
    st.header("🕒 Últimos Serviços")
    if not df_mov.empty:
        cols_disp = [c for c in ['OS_NUM','FROTA','MECANICO','STATUS'] if c in df_mov.columns]
        st.table(df_mov[cols_disp].tail(5).iloc[::-1])
    else:
        st.info("Nenhum lançamento registrado na aba 'movimentacao'.")

# ── Formulário ─────────────────────────────────────────────────
with st.form("form_oficina", clear_on_submit=True):
    col_titulo, col_os = st.columns([3, 1])
    with col_os:
        st.metric("O.S. ATUAL", f"#{proximo_numero:04d}")

    c1, c2 = st.columns(2)

    with c1:
        frota_sel = st.selectbox("Selecione o Equipamento", options=lista_frotas)
        mecanico  = st.text_input("Nome do Mecânico")
        sistema   = st.selectbox("Sistema Afetado", [
            "Motor", "Hidráulico", "Elétrico", "Pneus",
            "Transmissão", "Suspensão", "Implemento", "Outros"
        ])

    with c2:
        horimetro  = st.number_input("Horímetro ou KM Atual", min_value=0.0, step=0.1, format="%.1f")
        tipo_manut = st.selectbox("Tipo de Manutenção", ["CORRETIVA", "PREVENTIVA", "INTERNA", "PREDITIVA"])
        status_os  = st.radio("Status do Equipamento", ["FINALIZADO", "PENDENTE (EM ABERTO)"], horizontal=True)

    descricao = st.text_area("Descrição detalhada do serviço e peças aplicadas", max_chars=300)

    enviar = st.form_submit_button("✅ SALVAR NO SISTEMA")

    if enviar:
        if not mecanico.strip() or not descricao.strip():
            st.warning("⚠️ Nome do mecânico e Descrição são obrigatórios.")
        elif not conexao_ok:
            st.error("❌ Sem conexão com a planilha. Verifique os Secrets.")
        else:
            novo_registro = pd.DataFrame([{
                "OS_NUM":    proximo_numero,
                "DATA":      datetime.now().strftime("%d/%m/%Y %H:%M"),
                "FROTA":     frota_sel,
                "MECANICO":  mecanico.upper(),
                "HORIMETRO": horimetro,
                "SISTEMA":   sistema,
                "TIPO":      tipo_manut,
                "STATUS":    status_os,
                "DESCRICAO": descricao
            }])

            try:
                df_atualizado = pd.concat([df_mov, novo_registro], ignore_index=True)
                conn.update(worksheet="movimentacao", data=df_atualizado)
                st.success(f"✅ O.S. #{proximo_numero:04d} registrada com sucesso!")
                st.rerun()
            except Exception as error:
                st.error(f"❌ Erro ao salvar: {repr(error)}")
                st.code(traceback.format_exc())

st.divider()
st.caption("Sistema Oficina SV | Controladoria Bataguassu-MS | Dados salvos diretamente no Google Sheets.")