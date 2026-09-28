# Oficina SV — tema SIGCF v5 (padrão Apontamento de Campo / Posto SV)
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
from sigcf_theme import inject_theme, render_footer, render_header

TZ_BR = ZoneInfo("America/Sao_Paulo")

OFICINA_EXTRA_CSS = """
div[data-testid="stRadio"] label{color:var(--sigcf-label)!important;}
div[data-testid="stRadio"] div[role="radiogroup"] p{
 color:var(--sigcf-text)!important;font-size:13px!important;text-transform:none!important;}
.sigcf-os-hint{
 color:var(--sigcf-label)!important;font-size:11px!important;letter-spacing:0.12em;
 text-transform:uppercase;margin:0 0 16px;font-weight:600;}
.os-table{width:100%;border-collapse:collapse;font-size:12px;font-family:var(--sigcf-font);}
.os-table th{
 color:#ffd966;text-transform:uppercase;font-size:10px;letter-spacing:1px;
 padding:7px 10px;background:#1a2818;border-bottom:2px solid var(--sigcf-border);}
.os-table td{color:var(--sigcf-text);padding:6px 10px;border-bottom:1px solid var(--sigcf-border);}
.st-fin{color:var(--sigcf-green);font-weight:700;}
.st-pend{color:var(--sigcf-gold);font-weight:700;}
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
inject_theme(OFICINA_EXTRA_CSS)
render_header(
    logo_html,
    "Gestão de Oficina — SV",
    "SIGCF — Sistema Integrado de Gestão de Custos de Frota",
)

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

st.markdown('<div class="sec">Registrar ordem de serviço</div>', unsafe_allow_html=True)
st.markdown(
    f'<p class="sigcf-os-hint">Próxima O.S.: OS-{proximo_numero:04d} · sequência lida do Supabase</p>',
    unsafe_allow_html=True,
)

with st.form("form_oficina", clear_on_submit=True):
    col_os, _ = st.columns([1, 3])
    with col_os:
        st.metric("O.S. ATUAL", f"OS-{proximo_numero:04d}")

    st.markdown("**Identificação da O.S.**")
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

    st.markdown("**Serviço e observações**")
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

st.markdown('<span class="sigcf-op-sep"></span>', unsafe_allow_html=True)
st.markdown('<div class="sec">Últimas O.S. lançadas</div>', unsafe_allow_html=True)

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
        '<div class="sigcf-table-wrap" style="overflow-x:auto;">'
        "<table class='os-table'>"
        "<tr><th>OS</th><th>Frota</th><th>Sistema</th><th>Mecânico</th>"
        "<th>Operador</th><th>Status</th><th>Data/Hora</th></tr>"
        f"{linhas}</table></div>",
        unsafe_allow_html=True,
    )
    st.caption("Exibindo as 10 O.S. mais recentes · horário de Brasília")
else:
    st.info("Nenhuma O.S. registrada.")

render_footer("SIGCF · Oficina SV · Controladoria Bataguassu-MS")
