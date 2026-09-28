"""PIN opcional SIGCF — logo Santa Virginia premium."""
import base64
from pathlib import Path

LOGO_URL = "https://i.postimg.cc/Y9X7ddnb/LOGO-BP.jpg"
LOGO_FILE = Path(__file__).resolve().parent / "assets" / "logo_santa_verginia.png"
SESSION_KEY = "sigcf_auth"


def logo_html(width: int = 118) -> str:
    if LOGO_FILE.is_file():
        b64 = base64.b64encode(LOGO_FILE.read_bytes()).decode()
        src = f"data:image/png;base64,{b64}"
    else:
        src = LOGO_URL
    return f'<div class="logo-frame"><img src="{src}" width="{width}" alt="Santa Virgínia"></div>'


def _secret(key: str, default: str = "") -> str:
    import streamlit as st

    try:
        return str(st.secrets.get(key, default) or default)
    except Exception:
        return default


def conectar_supabase():
    import streamlit as st
    from supabase import create_client

    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        st.error(
            "Secrets do Supabase não encontrados. No Streamlit Cloud: "
            "Settings → Secrets → SUPABASE_URL e SUPABASE_KEY, depois Reboot app."
        )
        st.stop()
    return create_client(url, key)


def exigir_acesso(titulo: str, subtitulo: str = "Acesso restrito — SIGCF Santa Virgínia"):
    import streamlit as st

    pin_cfg = _secret("APP_PIN", "").strip()
    if not pin_cfg or st.session_state.get(SESSION_KEY):
        return

    from sigcf_theme import inject_theme, render_header

    inject_theme()
    render_header(logo_html, titulo, subtitulo)

    pin = st.text_input("PIN de acesso", type="password", key="sigcf_login_pin")
    if st.button("Entrar", type="primary", key="sigcf_login_btn"):
        if pin == pin_cfg:
            st.session_state[SESSION_KEY] = True
            st.rerun()
        else:
            st.error("PIN incorreto.")
    st.stop()
