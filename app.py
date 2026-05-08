import streamlit as st
import pandas as pd
from datetime import datetime
import traceback

import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Oficina SV - Controladoria", layout="wide")

# ── CONEXÃO GOOGLE SHEETS ─────────────────────────────────────
def conectar_gsheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    client = gspread.authorize(creds)

    # 🔥 COLOQUE O NOME EXATO DA SUA PLANILHA
    return client.open("OFICINA_SV")


# ── CARREGAMENTO DOS DADOS ────────────────────────────────────
try:
    sheet = conectar_gsheet()

    aba_frota = sheet.worksheet("FROTA")
    aba_mov   = sheet.worksheet("MOVIMENTACAO")

    df_frota = pd.DataFrame(aba_frota.get_all_records())
    df_mov   = pd.DataFrame(aba_mov.get_all_records())

    for col in ["OS_NUM", "STATUS"]:
        if col not in df_mov.columns:
            df_mov[col] = None

    if not df_frota.empty:
        lista_frotas = (
            df_frota['FROTA'].astype(str) + " - " + df_frota['DESCRICAO'].astype(str)
        ).dropna().unique().tolist()
    else:
        lista_frotas = ["Cadastre a frota na planilha"]

    if not df_mov.empty:
        os_max = pd.to_numeric(df_mov['OS_NUM'], errors='coerce').max()
        proximo_numero = int(os_max) + 1 if pd.notna(os_max) else 1
    else:
        proximo_numero = 1

    conexao_ok = True

except Exception as e:
    st.error("Erro ao conectar com Google Sheets")
    st.code(str(e))
    df_frota = pd.DataFrame()
    df_mov   = pd.DataFrame()
    lista_frotas = ["Erro"]
    proximo_numero = 0
    conexao_ok = False


# ── LAYOUT ────────────────────────────────────────────────────
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    st.image("https://i.postimg.cc/Y9X7ddnb/LOGO-BP.jpg", width=110)
with col_titulo:
    st.title("🚜 Gestão de Oficina - SV")
    st.caption("Controladoria Bataguassu-MS")

st.divider()

# ── SIDEBAR ───────────────────────────────────────────────────
with st.sidebar:
    st.header("🕒 Últimas OS")
    if not df_mov.empty:
        cols = [c for c in ['OS_NUM','FROTA','MECANICO','STATUS'] if c in df_mov.columns]
        st.table(df_mov[cols].tail(5).iloc[::-1])

# ── ABAS ──────────────────────────────────────────────────────
aba1, aba2 = st.tabs(["📋 Nova OS", "🔧 OS Pendentes"])

# ══════════════════════════════════════════════════════════════
# NOVA OS
# ══════════════════════════════════════════════════════════════
with aba1:

    with st.form("form_os", clear_on_submit=True):

        st.metric("O.S. ATUAL", f"#{proximo_numero:04d}")

        c1, c2 = st.columns(2)

        with c1:
            frota_sel = st.selectbox("Equipamento", lista_frotas)
            mecanico  = st.text_input("Mecânico")
            sistema   = st.selectbox("Sistema", [
                "Motor","Hidráulico","Elétrico","Pneus",
                "Transmissão","Suspensão","Implemento","Outros"
            ])

        with c2:
            horimetro  = st.number_input("Horímetro/KM", 0.0)
            tipo_manut = st.selectbox("Tipo", ["CORRETIVA","PREVENTIVA","INTERNA","PREDITIVA"])
            status_os  = st.radio("Status", ["FINALIZADO","PENDENTE"], horizontal=True)

        descricao  = st.text_area("Descrição", max_chars=300)
        observacao = st.text_area("Observação", max_chars=200)

        enviar = st.form_submit_button("SALVAR")

        if enviar:

            if not mecanico or not descricao:
                st.warning("Preencha Mecânico e Descrição")
            elif not conexao_ok:
                st.error("Sem conexão")
            else:

                hora_entrada = datetime.now().strftime("%H:%M")
                hora_saida   = datetime.now().strftime("%H:%M") if status_os == "FINALIZADO" else ""

                novo = pd.DataFrame([{
                    "OS_NUM": proximo_numero,
                    "DATA": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "FROTA": frota_sel,
                    "MECANICO": mecanico.upper(),
                    "HORIMETRO": horimetro,
                    "SISTEMA": sistema,
                    "TIPO": tipo_manut,
                    "STATUS": status_os,
                    "DESCRICAO": descricao,
                    "OBSERVACAO": observacao,
                    "HORA_ENTRADA": hora_entrada,
                    "HORA_SAIDA": hora_saida
                }])

                df_final = pd.concat([df_mov, novo], ignore_index=True)

                try:
                    aba_mov.update(
                        [df_final.columns.values.tolist()] +
                        df_final.values.tolist()
                    )
                    st.success("OS salva!")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))


# ══════════════════════════════════════════════════════════════
# OS PENDENTES
# ══════════════════════════════════════════════════════════════
with aba2:

    if not df_mov.empty:

        pendentes = df_mov[df_mov['STATUS'].astype(str).str.contains("PENDENTE", na=False)]

        if pendentes.empty:
            st.success("Nenhuma pendente")
        else:
            st.dataframe(pendentes)

            os_sel = st.selectbox("Selecionar OS", pendentes['OS_NUM'].astype(str))

            if st.button("FINALIZAR OS"):

                df_att = df_mov.copy()

                idx = df_att[df_att['OS_NUM'].astype(str) == os_sel].index

                if len(idx) > 0:
                    i = idx[0]
                    df_att.at[i, 'STATUS'] = 'FINALIZADO'
                    df_att.at[i, 'HORA_SAIDA'] = datetime.now().strftime("%H:%M")

                    try:
                        aba_mov.update(
                            [df_att.columns.values.tolist()] +
                            df_att.values.tolist()
                        )
                        st.success("OS finalizada!")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))