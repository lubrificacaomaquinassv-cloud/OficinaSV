import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

st.set_page_config(page_title="Oficina SV - SIGCF", layout="wide")

# ── Logo + Título
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    st.image("https://i.postimg.cc/Y9X7ddnb/LOGO-BP.jpg", width=110)
with col_titulo:
    st.title("🚜 Gestão de Oficina - SV")
    st.caption("SIGCF — Sistema Integrado de Gestão de Custos de Frota")

st.divider()

# ── Conexão Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Carregar dados
@st.cache_data(ttl=60)
def carregar_frota():
    res = supabase.table("dim_frota").select("id_frota, modelo").eq("ativo", True).order("modelo").execute()
    return res.data or []

@st.cache_data(ttl=10)
def carregar_os():
    res = supabase.table("ordem_servico").select("numero_os, id_frota, mecanico, status, created_at").order("created_at", desc=True).limit(50).execute()
    return res.data or []

@st.cache_data(ttl=300)
def carregar_mecanicos():
    res = supabase.table("dim_colaborador").select("id_colaborador, nome").eq("ativo", True).order("nome").execute()
    return res.data or []

frota_data    = carregar_frota()
os_data       = carregar_os()
mecanicos_data = carregar_mecanicos()

lista_frotas    = [f"{f['id_frota']} - {f['modelo']}" for f in frota_data] or ["Cadastre a frota"]
lista_mecanicos = [m['nome'] for m in mecanicos_data] or ["Cadastre o mecânico"]

# Próximo número OS
proximo_numero = 1
if os_data:
    numeros = [int(o['numero_os'].replace('OS-','')) for o in os_data if o.get('numero_os','').startswith('OS-')]
    if numeros:
        proximo_numero = max(numeros) + 1

# ── Sidebar
with st.sidebar:
    st.image("https://i.postimg.cc/Y9X7ddnb/LOGO-BP.jpg", width=140)
    st.divider()
    st.header("🕒 Últimas OS")
    if os_data:
        df_os = pd.DataFrame(os_data)[['numero_os','id_frota','mecanico','status']].head(5)
        st.table(df_os)
    else:
        st.info("Nenhuma OS registrada.")

# ── Formulário
with st.form("form_oficina", clear_on_submit=True):
    col_os, _ = st.columns([1, 3])
    with col_os:
        st.metric("O.S. ATUAL", f"OS-{proximo_numero:04d}")

    c1, c2 = st.columns(2)

    with c1:
        frota_sel  = st.selectbox("Selecione o Equipamento", options=lista_frotas)
        mecanico   = st.selectbox("Mecânico", options=lista_mecanicos)
        sistema    = st.selectbox("Sistema Afetado", [
            "Motor","Hidráulico","Elétrico","Pneus",
            "Transmissão","Suspensão","Implemento","Outros"
        ])

    with c2:
        horimetro  = st.number_input("Horímetro ou KM Atual", min_value=0.0, step=0.1, format="%.1f")
        tipo_manut = st.selectbox("Tipo de Manutenção", [
            "CORRETIVA","PREVENTIVA","INTERNA","PREDITIVA"
        ])
        hora_entrada = st.time_input("Hora Entrada", value=None)
        hora_saida   = st.time_input("Hora Saída", value=None)
        status_os  = st.radio("Status", ["FINALIZADO","PENDENTE"], horizontal=True)

    descricao  = st.text_area("Descrição do serviço e peças aplicadas", max_chars=300)
    observacao = st.text_area("Observação", max_chars=200)

    enviar = st.form_submit_button("✅ SALVAR NO SISTEMA")

    if enviar:
        if not descricao.strip():
            st.warning("⚠️ Descrição é obrigatória.")
        else:
            # Calcular tempo trabalhado
            tempo_min = None
            if hora_entrada and hora_saida:
                from datetime import timedelta
                dt_entrada = datetime.combine(datetime.today(), hora_entrada)
                dt_saida   = datetime.combine(datetime.today(), hora_saida)
                if dt_saida > dt_entrada:
                    tempo_min = int((dt_saida - dt_entrada).total_seconds() / 60)

            id_frota = frota_sel.split(" - ")[0].strip()

            novo = {
                "numero_os":    f"OS-{proximo_numero:04d}",
                "id_frota":     id_frota,
                "mecanico":     mecanico,
                "horimetro":    str(horimetro),
                "sistema":      sistema,
                "tipo_manutencao": tipo_manut,
                "hora_entrada": str(hora_entrada) if hora_entrada else None,
                "hora_saida":   str(hora_saida) if hora_saida else None,
                "tempo_min":    tempo_min,
                "status":       status_os,
                "descricao":    descricao,
                "observacao":   observacao,
                "created_at":   datetime.now().isoformat()
            }

            try:
                supabase.table("ordem_servico").insert(novo).execute()
                st.success(f"✅ O.S. OS-{proximo_numero:04d} registrada! Tempo: {tempo_min} min" if tempo_min else f"✅ O.S. OS-{proximo_numero:04d} registrada!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao salvar: {e}")

st.divider()
st.caption("SIGCF | Oficina SV | Controladoria Bataguassu-MS")
