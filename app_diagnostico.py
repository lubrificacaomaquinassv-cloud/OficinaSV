"""Diagnóstico passo a passo — descobre onde o app trava no Streamlit Cloud."""
import streamlit as st

st.set_page_config(page_title="Diagnóstico Oficina SV", layout="wide", page_icon="🔍")
st.title("🔍 Diagnóstico — Oficina SV")
st.caption("Cada etapa abaixo mostra até onde o app consegue chegar.")

if st.button("Rodar diagnóstico completo"):
    st.session_state["_diag_run"] = True

if not st.session_state.get("_diag_run"):
    st.info("Clique no botão acima para testar imports, secrets e Supabase.")
    st.stop()

st.success("✅ 1. Streamlit carregou")

try:
    import re
    from datetime import datetime
    from zoneinfo import ZoneInfo

    st.success("✅ 2. Imports stdlib OK")
except Exception as e:
    st.error(f"❌ 2. Imports stdlib FALHOU: {e}")
    st.stop()

try:
    from sigcf_auth import conectar_supabase, exigir_acesso, logo_html

    st.success("✅ 3. sigcf_auth import OK")
except Exception as e:
    st.error(f"❌ 3. sigcf_auth FALHOU: {e}")
    st.stop()

try:
    html = logo_html(80)
    st.success(f"✅ 4. logo_html OK ({len(html)} chars)")
    st.markdown(html, unsafe_allow_html=True)
except Exception as e:
    st.error(f"❌ 4. logo_html FALHOU: {e}")

try:
    url = str(st.secrets.get("SUPABASE_URL", "") or "")
    key = str(st.secrets.get("SUPABASE_KEY", "") or "")
    pin = str(st.secrets.get("APP_PIN", "") or "")
    st.success(
        f"✅ 5. Secrets — URL={'sim' if url else 'NÃO'}, "
        f"KEY={'sim' if key else 'NÃO'}, PIN={'configurado' if pin else 'vazio'}"
    )
    if not url or not key:
        st.warning("SUPABASE_URL ou SUPABASE_KEY ausente — app original para aqui.")
        st.stop()
except Exception as e:
    st.error(f"❌ 5. Secrets FALHOU: {e}")
    st.stop()

try:
    sb = conectar_supabase()
    st.success("✅ 6. Supabase conectado")
except Exception as e:
    st.error(f"❌ 6. Supabase FALHOU: {e}")
    st.stop()

for i, (nome, fn) in enumerate(
    [
        ("dim_frota", lambda: sb.table("dim_frota").select("id_frota").eq("ativo", True).limit(3).execute()),
        ("ordem_servico", lambda: sb.table("ordem_servico").select("numero_os").limit(3).execute()),
        ("dim_colaborador", lambda: sb.table("dim_colaborador").select("nome").eq("ativo", True).limit(3).execute()),
    ],
    start=7,
):
    try:
        res = fn()
        n = len(res.data or [])
        st.success(f"✅ {i}. Query {nome} OK — {n} registro(s)")
    except Exception as e:
        st.error(f"❌ {i}. Query {nome} FALHOU: {e}")

st.divider()
st.success("Diagnóstico concluído. Se chegou aqui, o app original deveria funcionar.")
st.caption("Próximo passo: restaurar app_original.py → app.py com boot no topo do script.")
