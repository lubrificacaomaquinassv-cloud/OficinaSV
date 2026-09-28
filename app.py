# Oficina SV — relançamento limpo (mesmo Supabase, numeração OS preservada no banco)
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

st.set_page_config(
    page_title="Oficina SV - SIGCF",
    layout="wide",
    page_icon="🔧",
    initial_sidebar_state="collapsed",
)

from sigcf_auth import conectar_supabase, exigir_acesso, logo_html

TZ_BR = ZoneInfo("America/Sao_Paulo")

CSS = """
[data-testid="stAppViewContainer"]{background:#0a1409;}
[data-testid="stSidebar"]{background:#111c10;border-right:1px solid #1e2e1c;}
[data-testid="stHeader"]{background:#0a1409;}
h1,h2,h3,h4,p,span,label{color:#e8edd0;}
.stCaption,[data-testid="stCaptionContainer"] p{color:#8aab80!important;}
.logo-frame{background:linear-gradient(145deg,#0a1628,#0d2040);border:2px solid #c9a227;
 border-radius:12px;padding:5px;display:inline-block;}
.logo-frame img{display:block;border-radius:8px;}
div[data-testid="stForm"]{background:#0d180c;border:1px solid #1e2e1c;border-radius:12px;padding:24px;}
div[data-testid="stSelectbox"] label,div[data-testid="stNumberInput"] label,
div[data-testid="stTextArea"] label,div[data-testid="stTextInput"] label,
div[data-testid="stRadio"] label{color:#8aab80!important;font-size:12px!important;}
.stTextInput input,.stNumberInput input,.stTextArea textarea{
 background:#dce6d2!important;color:#1a2818!important;border:1px solid #4a6644!important;border-radius:8px!important;}
div[data-baseweb="select"] > div{background:#dce6d2!important;border:1px solid #4a6644!important;color:#1a2818!important;}
.stButton button,[data-testid="stFormSubmitButton"] button{
 background:#4a9e3f!important;color:#fff!important;border:1px solid #6fcf60!important;font-weight:700;}
.sec{font-size:12px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#8aab80;
 border-left:4px solid #4a9e3f;padding-left:10px;margin:4px 0 10px;}
.os-table{width:100%;border-collapse:collapse;font-size:12px;}
.os-table th{color:#8aab80;text-transform:uppercase;font-size:10px;padding:6px 8px;border-bottom:1px solid #1e2e1c;}
.os-table td{color:#e8edd0;padding:6px 8px;border-bottom:1px solid #16241480;}
.st-fin{color:#6fcf60;font-weight:700;}
.st-pend{color:#d4a017;font-weight:700;}
"""


def parse_hora(txt):
    if not txt or not str(txt).strip():
        return None
    txt = str(txt).strip().replace("h", ":")
    m = re.match(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?$", txt)
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    if h > 23 or mi > 59:
        return None
    return datetime.strptime(f"{h:02d}:{mi:02d}", "%H:%M").time()


def fmt_dt_br(value):
    if not value:
        return "—"
    try:
        raw = str(value).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        return dt.astimezone(TZ_BR).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(value)[:16]


def extrair_num_os(numero_os):
    txt = str(numero_os or "").strip().upper()
    if txt.startswith("OS-"):
        try:
            return int(txt.replace("OS-", ""))
        except ValueError:
            return None
    return None


@st.cache_resource
def get_supabase():
    return conectar_supabase()


@st.cache_data(ttl=60)
def carregar_frota(_sb):
    res = _sb.table("dim_frota").select("id_frota, modelo").eq("ativo", True).order("modelo").execute()
    return res.data or []


@st.cache_data(ttl=60)
def carregar_mecanicos(_sb):
    res = _sb.table("dim_colaborador").select("id_colaborador, nome").eq("ativo", True).order("nome").execute()
    return res.data or []


@st.cache_data(ttl=10)
def carregar_os_recentes(_sb):
    try:
        res = _sb.table("ordem_servico").select(
            "numero_os, id_frota, mecanico, operador, sistema, status, created_at"
        ).order("created_at", desc=True).limit(10).execute()
        return res.data or []
    except Exception:
        res = _sb.table("ordem_servico").select(
            "numero_os, id_frota, mecanico, status, created_at"
        ).order("created_at", desc=True).limit(10).execute()
        return res.data or []


@st.cache_data(ttl=10)
def proximo_numero_os(_sb):
    """Numeração vem do Supabase — recriar o app não apaga OS já lançadas."""
    numeros = []
    try:
        res = (
            _sb.table("ordem_servico")
            .select("numero_os")
            .like("numero_os", "OS-%")
            .order("numero_os", desc=True)
            .limit(1)
            .execute()
        )
        for row in res.data or []:
            n = extrair_num_os(row.get("numero_os"))
            if n is not None:
                numeros.append(n)
    except Exception:
        pass
    if not numeros:
        res = _sb.table("ordem_servico").select("numero_os").limit(1000).execute()
        for row in res.data or []:
            n = extrair_num_os(row.get("numero_os"))
            if n is not None:
                numeros.append(n)
    return max(numeros) + 1 if numeros else 1


exigir_acesso("Gestão de Oficina — SV")
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

col_logo, col_titulo = st.columns([1.1, 5.9])
with col_logo:
    st.markdown(logo_html(118), unsafe_allow_html=True)
with col_titulo:
    st.title("Gestão de Oficina — SV")
    st.caption("SIGCF | Controladoria Bataguassu-MS")

st.divider()

try:
    supabase = get_supabase()
    frota_data = carregar_frota(supabase)
    mecanicos_data = carregar_mecanicos(supabase)
    os_data = carregar_os_recentes(supabase)
    proximo_numero = proximo_numero_os(supabase)
except Exception as e:
    st.error(f"Erro ao carregar dados do Supabase: {e}")
    st.info("Verifique SUPABASE_URL e SUPABASE_KEY em Settings → Secrets no Streamlit Cloud.")
    st.stop()

lista_frotas = [f"{f['id_frota']} - {f['modelo']}" for f in frota_data] or ["Cadastre a frota"]
lista_mecanicos = [m["nome"] for m in mecanicos_data] or ["Cadastre o mecânico"]

st.caption(f"Próxima OS: **OS-{proximo_numero:04d}** (sequência lida do Supabase)")

with st.form("form_oficina", clear_on_submit=True):
    col_os, _ = st.columns([1, 3])
    with col_os:
        st.metric("O.S. ATUAL", f"OS-{proximo_numero:04d}")

    c1, c2 = st.columns(2)

    with c1:
        frota_sel = st.selectbox("Selecione o Equipamento", options=lista_frotas)
        mecanico = st.selectbox("Mecânico", options=lista_mecanicos)
        sistema = st.selectbox(
            "Sistema Afetado",
            ["Motor", "Hidráulico", "Elétrico", "Pneus", "Transmissão", "Suspensão", "Implemento", "Outros"],
        )
        operador_sel = st.text_input(
            "Operador (apontado no equipamento)",
            placeholder="Digite o nome do operador",
        )

    with c2:
        horimetro = st.number_input("Horímetro ou KM Atual", min_value=0.0, step=0.1, format="%.1f")
        tipo_manut = st.selectbox("Tipo de Manutenção", ["CORRETIVA", "PREVENTIVA", "INTERNA", "PREDITIVA"])
        hora_entrada_txt = st.text_input("Hora Entrada", placeholder="Ex: 08:30")
        hora_saida_txt = st.text_input("Hora Saída", placeholder="Ex: 14:30")
        status_os = st.radio("Status", ["FINALIZADO", "PENDENTE"], horizontal=True)

    descricao = st.text_area("Descrição do serviço e peças aplicadas", max_chars=300)
    observacao = st.text_area("Observação", max_chars=200)
    enviar = st.form_submit_button("SALVAR NO SISTEMA")

    if enviar:
        hora_entrada = parse_hora(hora_entrada_txt)
        hora_saida = parse_hora(hora_saida_txt)
        if hora_entrada_txt.strip() and not hora_entrada:
            st.warning("Hora de entrada inválida. Use HH:MM (ex: 08:30).")
        elif hora_saida_txt.strip() and not hora_saida:
            st.warning("Hora de saída inválida. Use HH:MM (ex: 14:30).")
        elif not descricao.strip():
            st.warning("Descrição é obrigatória.")
        else:
            tempo_min = None
            if hora_entrada and hora_saida:
                dt_entrada = datetime.combine(datetime.today(), hora_entrada)
                dt_saida = datetime.combine(datetime.today(), hora_saida)
                if dt_saida > dt_entrada:
                    tempo_min = int((dt_saida - dt_entrada).total_seconds() / 60)

            novo = {
                "numero_os": f"OS-{proximo_numero:04d}",
                "id_frota": frota_sel.split(" - ")[0].strip(),
                "mecanico": mecanico,
                "operador": str(operador_sel or "").strip().upper() or None,
                "horimetro": str(horimetro),
                "sistema": sistema,
                "tipo_manutencao": tipo_manut,
                "hora_entrada": str(hora_entrada) if hora_entrada else None,
                "hora_saida": str(hora_saida) if hora_saida else None,
                "tempo_minutos": tempo_min,
                "status": status_os,
                "descricao": descricao,
                "observacao": observacao,
            }
            try:
                supabase.table("ordem_servico").insert(novo).execute()
                st.success(
                    f"O.S. OS-{proximo_numero:04d} registrada! Tempo: {tempo_min} min"
                    if tempo_min
                    else f"O.S. OS-{proximo_numero:04d} registrada!"
                )
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

st.divider()
st.markdown('<div class="sec">Ultimas OS lancadas</div>', unsafe_allow_html=True)
if os_data:
    linhas = ""
    for o in os_data:
        status = str(o.get("status", "—")).upper()
        cls = "st-fin" if "FINAL" in status else "st-pend"
        linhas += (
            f"<tr><td>{o.get('numero_os', '—')}</td>"
            f"<td>{o.get('id_frota', '—')}</td>"
            f"<td>{o.get('sistema', '—')}</td>"
            f"<td>{o.get('mecanico', '—')}</td>"
            f"<td>{o.get('operador') or '—'}</td>"
            f"<td class='{cls}'>{status}</td>"
            f"<td>{fmt_dt_br(o.get('created_at'))}</td></tr>"
        )
    st.markdown(
        "<table class='os-table'>"
        "<tr><th>OS</th><th>Frota</th><th>Sistema</th><th>Mecanico</th>"
        "<th>Operador</th><th>Status</th><th>Data/Hora</th></tr>"
        f"{linhas}</table>",
        unsafe_allow_html=True,
    )
else:
    st.info("Nenhuma OS registrada.")

st.caption("SIGCF | Oficina SV | Controladoria Bataguassu-MS")
