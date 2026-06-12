import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

st.set_page_config(page_title="Oficina SV - SIGCF", layout="wide", page_icon="🔧",
                   initial_sidebar_state="collapsed")

LOGO_URL = "https://i.postimg.cc/Y9X7ddnb/LOGO-BP.jpg"

# ── Identidade visual SV (mesmo padrão do Gestor e do Painel da Frota) ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700&display=swap');
[data-testid="stAppViewContainer"]{background:#0a1409;}
[data-testid="stSidebar"]{background:#111c10;border-right:1px solid #1e2e1c;}
[data-testid="stHeader"]{background:#0a1409;}
h1,h2,h3,h4,p,span,label{color:#e8edd0;}
h1{font-family:'Barlow Condensed',sans-serif;letter-spacing:1px;}
.stCaption,[data-testid="stCaptionContainer"] p{color:#8aab80!important;}
div[data-testid="stForm"]{background:#111c10;border:1px solid #1e2e1c;border-radius:12px;padding:24px;}
div[data-testid="stSelectbox"] label,div[data-testid="stNumberInput"] label,
div[data-testid="stTimeInput"] label,div[data-testid="stTextArea"] label,
div[data-testid="stTextInput"] label,div[data-testid="stRadio"] label,
div[data-testid="stRadio"] p{color:#8aab80!important;font-family:'Barlow Condensed',sans-serif;
 text-transform:uppercase;letter-spacing:1px;font-size:12px!important;}
div[data-testid="stRadio"] div[role="radiogroup"] p{color:#e8edd0!important;font-size:14px!important;text-transform:none;}
div[data-baseweb="select"] > div{background:#0d180c!important;border:1px solid #1e2e1c!important;color:#e8edd0!important;}
div[data-baseweb="select"] div{color:#e8edd0!important;}
div[data-baseweb="select"] svg{fill:#8aab80;}
ul[data-testid="stSelectboxVirtualDropdown"],div[data-baseweb="popover"] ul{background:#111c10!important;}
div[data-baseweb="popover"] li{color:#e8edd0!important;}
.stNumberInput input,.stTextInput input,.stTextArea textarea,.stTimeInput input{
 background:#0d180c!important;border:1px solid #1e2e1c!important;color:#e8edd0!important;}
.stNumberInput button{background:#111c10!important;color:#8aab80!important;border:1px solid #1e2e1c!important;}
div[data-testid="metric-container"],div[data-testid="stMetric"]{
 background:#0d180c;border:1px solid #4a9e3f;border-radius:10px;padding:12px 18px;}
div[data-testid="stMetric"] label,div[data-testid="metric-container"] label{color:#8aab80!important;}
div[data-testid="stMetricValue"]{color:#6fcf60!important;font-family:'Barlow Condensed',sans-serif;}
.stButton button,[data-testid="stFormSubmitButton"] button{
 background:#4a9e3f!important;color:#ffffff!important;border:1px solid #6fcf60!important;
 font-family:'Barlow Condensed',sans-serif;font-weight:700;letter-spacing:1.5px;
 text-transform:uppercase;border-radius:8px;padding:10px 28px;}
.stButton button:hover,[data-testid="stFormSubmitButton"] button:hover{background:#3d8534!important;}
.stButton button p,[data-testid="stFormSubmitButton"] button p{color:#ffffff!important;font-weight:700;}
.logo-box{background:#ffffff;border-radius:10px;padding:8px 12px;display:inline-block;}
.sec{font-family:'Barlow Condensed',sans-serif;font-size:12px;font-weight:700;
 letter-spacing:2px;text-transform:uppercase;color:#8aab80;
 border-left:4px solid #4a9e3f;padding-left:10px;margin:4px 0 10px;}
.os-table{width:100%;border-collapse:collapse;font-size:12px;}
.os-table th{color:#8aab80;text-transform:uppercase;font-size:10px;letter-spacing:1px;
 text-align:left;padding:6px 8px;border-bottom:1px solid #1e2e1c;font-family:'Barlow Condensed',sans-serif;}
.os-table td{color:#e8edd0;padding:6px 8px;border-bottom:1px solid #16241480;}
.st-fin{color:#6fcf60;font-weight:700;}
.st-pend{color:#d4a017;font-weight:700;}
</style>
""", unsafe_allow_html=True)

# ── Logo + Título ──
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    st.markdown(f'<div class="logo-box"><img src="{LOGO_URL}" width="100"></div>', unsafe_allow_html=True)
with col_titulo:
    st.title("🔧 Gestão de Oficina — SV")
    st.caption("SIGCF | Controladoria Bataguassu-MS")

st.divider()

# ── Conexão Supabase ──
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Carregar dados ──
@st.cache_data(ttl=60)
def carregar_frota():
    res = supabase.table("dim_frota").select("id_frota, modelo").eq("ativo", True).order("modelo").execute()
    return res.data or []

@st.cache_data(ttl=10)
def carregar_os():
    try:
        res = supabase.table("ordem_servico").select(
            "numero_os, id_frota, mecanico, operador, sistema, status, created_at"
        ).order("created_at", desc=True).limit(50).execute()
        return res.data or []
    except Exception:
        # fallback enquanto a coluna "operador" não existir no banco
        res = supabase.table("ordem_servico").select(
            "numero_os, id_frota, mecanico, status, created_at"
        ).order("created_at", desc=True).limit(50).execute()
        return res.data or []

@st.cache_data(ttl=300)
def carregar_mecanicos():
    res = supabase.table("dim_colaborador").select("id_colaborador, nome").eq("ativo", True).order("nome").execute()
    return res.data or []

@st.cache_data(ttl=300)
def carregar_operadores():
    """Operadores de trator: dim_colaborador com funcao OPERADOR (salário
    centralizado na mesma tabela dos mecânicos)."""
    try:
        res = supabase.table("dim_colaborador").select("nome").eq("ativo", True).eq("funcao", "OPERADOR").order("nome").execute()
        if res.data:
            return [{"operador": r["nome"]} for r in res.data]
    except Exception:
        pass
    try:
        res = supabase.table("dim_operador_frota").select("operador").eq("ativo", True).order("operador").execute()
        return res.data or []
    except Exception:
        return []

frota_data = carregar_frota()
os_data = carregar_os()
mecanicos_data = carregar_mecanicos()
operadores_data = carregar_operadores()

lista_frotas = [f"{f['id_frota']} - {f['modelo']}" for f in frota_data] or ["Cadastre a frota"]
lista_mecanicos = [m['nome'] for m in mecanicos_data] or ["Cadastre o mecânico"]
lista_operadores = sorted({str(o['operador']).strip() for o in operadores_data if o.get('operador')})

SEM_OPERADOR = "— SEM OPERADOR —"

# Próximo número OS
proximo_numero = 1
if os_data:
    numeros = [int(o['numero_os'].replace('OS-', '')) for o in os_data if o.get('numero_os', '').startswith('OS-')]
    if numeros:
        proximo_numero = max(numeros) + 1

# ── Formulário ──
with st.form("form_oficina", clear_on_submit=True):
    col_os, _ = st.columns([1, 3])
    with col_os:
        st.metric("O.S. ATUAL", f"OS-{proximo_numero:04d}")

    c1, c2 = st.columns(2)

    with c1:
        frota_sel = st.selectbox("Selecione o Equipamento", options=lista_frotas)
        mecanico = st.selectbox("Mecânico", options=lista_mecanicos)
        sistema = st.selectbox("Sistema Afetado", [
            "Motor", "Hidráulico", "Elétrico", "Pneus",
            "Transmissão", "Suspensão", "Implemento", "Outros"
        ])
        if lista_operadores:
            operador_sel = st.selectbox(
                "Operador (apontado no equipamento)",
                options=[SEM_OPERADOR] + lista_operadores,
                help="Usado para calcular a hora do operador parado durante a OS",
            )
        else:
            operador_sel = st.text_input(
                "Operador (apontado no equipamento)",
                help="Cadastre os operadores na tabela dim_operador_frota para virar lista",
            )

    with c2:
        horimetro = st.number_input("Horímetro ou KM Atual", min_value=0.0, step=0.1, format="%.1f")
        tipo_manut = st.selectbox("Tipo de Manutenção", [
            "CORRETIVA", "PREVENTIVA", "INTERNA", "PREDITIVA"
        ])
        hora_entrada = st.time_input("Hora Entrada", value=None)
        hora_saida = st.time_input("Hora Saída", value=None)
        status_os = st.radio("Status", ["FINALIZADO", "PENDENTE"], horizontal=True)

    descricao = st.text_area("Descrição do serviço e peças aplicadas", max_chars=300)
    observacao = st.text_area("Observação", max_chars=200)

    enviar = st.form_submit_button("✅ SALVAR NO SISTEMA")

    if enviar:
        if not descricao.strip():
            st.warning("⚠️ Descrição é obrigatória.")
        else:
            # Calcular tempo trabalhado
            tempo_min = None
            if hora_entrada and hora_saida:
                dt_entrada = datetime.combine(datetime.today(), hora_entrada)
                dt_saida = datetime.combine(datetime.today(), hora_saida)
                if dt_saida > dt_entrada:
                    tempo_min = int((dt_saida - dt_entrada).total_seconds() / 60)

            id_frota = frota_sel.split(" - ")[0].strip()

            operador_final = str(operador_sel or "").strip().upper()
            if operador_final == SEM_OPERADOR.upper() or not operador_final:
                operador_final = None

            novo = {
                "numero_os": f"OS-{proximo_numero:04d}",
                "id_frota": id_frota,
                "mecanico": mecanico,
                "operador": operador_final,
                "horimetro": str(horimetro),
                "sistema": sistema,
                "tipo_manutencao": tipo_manut,
                "hora_entrada": str(hora_entrada) if hora_entrada else None,
                "hora_saida": str(hora_saida) if hora_saida else None,
                "tempo_min": tempo_min,
                "status": status_os,
                "descricao": descricao,
                "observacao": observacao,
                "created_at": datetime.now().isoformat()
            }

            try:
                supabase.table("ordem_servico").insert(novo).execute()
                st.success(
                    f"✅ O.S. OS-{proximo_numero:04d} registrada! Tempo: {tempo_min} min"
                    if tempo_min else f"✅ O.S. OS-{proximo_numero:04d} registrada!"
                )
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao salvar: {e}")

st.divider()

# ── Últimas OS (tabela completa abaixo do formulário) ──
st.markdown('<div class="sec">🕒 Últimas OS lançadas</div>', unsafe_allow_html=True)
if os_data:
    linhas = ""
    for o in os_data[:10]:
        status = str(o.get("status", "—")).upper()
        cls = "st-fin" if "FINAL" in status else "st-pend"
        dt_fmt = "—"
        if o.get("created_at"):
            try:
                dt_fmt = datetime.fromisoformat(
                    str(o["created_at"]).replace("Z", "+00:00")
                ).strftime("%d/%m/%Y %H:%M")
            except Exception:
                dt_fmt = str(o["created_at"])[:16]
        linhas += (
            f"<tr><td>{o.get('numero_os', '—')}</td>"
            f"<td>{o.get('id_frota', '—')}</td>"
            f"<td>{o.get('sistema', '—')}</td>"
            f"<td>{o.get('mecanico', '—')}</td>"
            f"<td>{o.get('operador') or '—'}</td>"
            f"<td class='{cls}'>{status}</td>"
            f"<td>{dt_fmt}</td></tr>"
        )
    st.markdown(
        "<table class='os-table'>"
        "<tr><th>OS</th><th>Frota</th><th>Sistema</th><th>Mecânico</th>"
        "<th>Operador</th><th>Status</th><th>Data/Hora</th></tr>"
        f"{linhas}</table>",
        unsafe_allow_html=True,
    )
    st.caption("Exibindo as 10 OS mais recentes")
else:
    st.info("Nenhuma OS registrada.")

st.divider()
st.caption("SIGCF | Oficina SV | Controladoria Bataguassu-MS")
