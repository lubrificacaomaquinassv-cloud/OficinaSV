import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import traceback
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

st.set_page_config(page_title="Oficina SV - Controladoria", layout="wide")

# ── Logo + Título ──────────────────────────────────────────────
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    st.image("https://i.postimg.cc/Y9X7ddnb/LOGO-BP.jpg", width=110)
with col_titulo:
    st.title("🚜 Gestão de Oficina - SV")
    st.caption("Controladoria Bataguassu-MS")

st.divider()

# ── Função upload Google Drive ─────────────────────────────────
def upload_drive(arquivo, nome_arquivo):
    try:
        info = st.secrets["connections"]["gsheets"]
        creds = Credentials.from_service_account_info(
            {
                "type":                        info["type"],
                "project_id":                  info["project_id"],
                "private_key_id":              info["private_key_id"],
                "private_key":                 info["private_key"],
                "client_email":                info["client_email"],
                "client_id":                   info["client_id"],
                "auth_uri":                    info["auth_uri"],
                "token_uri":                   info["token_uri"],
                "auth_provider_x509_cert_url": info["auth_provider_x509_cert_url"],
                "client_x509_cert_url":        info["client_x509_cert_url"],
            },
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        service  = build("drive", "v3", credentials=creds)
        metadata = {"name": nome_arquivo}
        media    = MediaIoBaseUpload(io.BytesIO(arquivo.read()), mimetype=arquivo.type)
        file     = service.files().create(body=metadata, media_body=media, fields="id").execute()
        file_id  = file.get("id")
        service.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"}
        ).execute()
        return f"https://drive.google.com/file/d/{file_id}/view"
    except Exception as e:
        return f"ERRO_UPLOAD: {str(e)}"

# ── Conexão ────────────────────────────────────────────────────
try:
    conn     = st.connection("gsheets", type=GSheetsConnection)
    df_frota = conn.read(worksheet="FROTA", ttl=120)
    df_mov   = conn.read(worksheet="MOVIMENTACAO", ttl=5)

    if not df_frota.empty:
        lista_frotas = (
            df_frota['FROTA'].astype(str) + " - " + df_frota['DESCRICAO'].astype(str)
        ).dropna().unique().tolist()
    else:
        lista_frotas = ["Cadastre a frota na planilha"]

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
    st.header("🕒 Últimas OS")
    if not df_mov.empty:
        cols_disp = [c for c in ['OS_NUM','FROTA','MECANICO','STATUS'] if c in df_mov.columns]
        st.table(df_mov[cols_disp].tail(5).iloc[::-1])
    else:
        st.info("Nenhum lançamento registrado.")

# ── Abas ───────────────────────────────────────────────────────
aba1, aba2 = st.tabs(["📋 Nova OS", "🔧 OS Pendentes"])

# ══════════════════════════════════════════════════════════════
# ABA 1 — NOVA OS
# ══════════════════════════════════════════════════════════════
with aba1:
    with st.form("form_oficina", clear_on_submit=True):
        col_t, col_os = st.columns([3, 1])
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

        descricao  = st.text_area("Descrição detalhada do serviço e peças aplicadas", max_chars=300, placeholder="Máx. 300 caracteres")
        observacao = st.text_area("Observação", max_chars=200, placeholder="Máx. 200 caracteres")
        foto       = st.file_uploader("📎 Anexar Foto / Documento", type=["jpg", "jpeg", "png", "pdf"])

        enviar = st.form_submit_button("✅ SALVAR NO SISTEMA")

        if enviar:
            if not mecanico.strip() or not descricao.strip():
                st.warning("⚠️ Nome do mecânico e Descrição são obrigatórios.")
            elif not conexao_ok:
                st.error("❌ Sem conexão com a planilha.")
            else:
                hora_entrada = datetime.now().strftime("%H:%M")
                hora_saida   = datetime.now().strftime("%H:%M") if status_os == "FINALIZADO" else ""

                foto_url = ""
                if foto:
                    with st.spinner("Enviando arquivo para o Drive..."):
                        nome_arquivo = f"OS{proximo_numero:04d}_{foto.name}"
                        foto_url     = upload_drive(foto, nome_arquivo)

                novo_registro = pd.DataFrame([{
                    "OS_NUM":       proximo_numero,
                    "DATA":         datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "FROTA":        frota_sel,
                    "MECANICO":     mecanico.upper(),
                    "HORIMETRO":    horimetro,
                    "SISTEMA":      sistema,
                    "TIPO":         tipo_manut,
                    "STATUS":       status_os,
                    "DESCRICAO":    descricao,
                    "OBSERVACAO":   observacao,
                    "HORA_ENTRADA": hora_entrada,
                    "HORA_SAIDA":   hora_saida,
                    "FOTO_URL":     foto_url
                }])

                try:
                    df_atualizado = pd.concat([df_mov, novo_registro], ignore_index=True)
                    conn.update(worksheet="MOVIMENTACAO", data=df_atualizado)
                    st.success(f"✅ O.S. #{proximo_numero:04d} registrada com sucesso!")
                    st.rerun()
                except Exception as error:
                    st.error(f"❌ Erro ao salvar: {repr(error)}")
                    st.code(traceback.format_exc())

# ══════════════════════════════════════════════════════════════
# ABA 2 — OS PENDENTES
# ══════════════════════════════════════════════════════════════
with aba2:
    st.subheader("🔧 Ordens de Serviço Pendentes")

    if not conexao_ok or df_mov.empty:
        st.info("Nenhuma OS registrada ou sem conexão.")
    else:
        pendentes = df_mov[df_mov['STATUS'] == 'PENDENTE (EM ABERTO)'].copy()

        if pendentes.empty:
            st.success("✅ Nenhuma OS pendente no momento!")
        else:
            st.info(f"**{len(pendentes)}** OS(s) em aberto")

            cols_show = [c for c in ['OS_NUM','DATA','FROTA','MECANICO','SISTEMA','TIPO','DESCRICAO'] if c in pendentes.columns]
            st.dataframe(pendentes[cols_show], use_container_width=True)

            st.divider()
            st.subheader("Finalizar OS")

            opcoes_os = pendentes['OS_NUM'].astype(str).tolist()
            os_sel    = st.selectbox("Selecione a OS para finalizar", options=opcoes_os)

            linha_os  = pendentes[pendentes['OS_NUM'].astype(str) == os_sel]

            if not linha_os.empty:
                st.write(f"**Equipamento:** {linha_os['FROTA'].values[0]}")
                st.write(f"**Mecânico:** {linha_os['MECANICO'].values[0]}")
                st.write(f"**Descrição:** {linha_os['DESCRICAO'].values[0]}")

            with st.form("form_finalizar"):
                obs_final  = st.text_area("Observação de encerramento", max_chars=200, placeholder="Opcional")
                foto_final = st.file_uploader("📎 Foto / Documento de encerramento", type=["jpg","jpeg","png","pdf"])
                finalizar  = st.form_submit_button("✅ FINALIZAR OS")

                if finalizar:
                    hora_saida = datetime.now().strftime("%H:%M")
                    foto_url   = ""

                    if foto_final:
                        with st.spinner("Enviando arquivo para o Drive..."):
                            nome_arquivo = f"OS{os_sel}_ENCERRAMENTO_{foto_final.name}"
                            foto_url     = upload_drive(foto_final, nome_arquivo)

                    try:
                        df_att = conn.read(worksheet="MOVIMENTACAO", ttl=0)
                        idx    = df_att[df_att['OS_NUM'].astype(str) == os_sel].index

                        if len(idx) > 0:
                            i = idx[0]
                            df_att.at[i, 'STATUS']     = 'FINALIZADO'
                            df_att.at[i, 'HORA_SAIDA'] = hora_saida
                            if obs_final.strip():
                                df_att.at[i, 'OBSERVACAO'] = obs_final
                            if foto_url:
                                df_att.at[i, 'FOTO_URL'] = foto_url

                            conn.update(worksheet="MOVIMENTACAO", data=df_att)
                            st.success(f"✅ O.S. #{os_sel} finalizada com sucesso!")
                            st.rerun()
                    except Exception as error:
                        st.error(f"❌ Erro ao finalizar: {repr(error)}")
                        st.code(traceback.format_exc())

st.divider()
st.caption("Sistema Oficina SV | Controladoria Bataguassu-MS | Dados salvos diretamente no Google Sheets.")
