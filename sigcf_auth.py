"""PIN opcional SIGCF — logo Santa Virginia."""
from pathlib import Path

LOGO_URL = "https://i.postimg.cc/Y9X7ddnb/LOGO-BP.jpg"
LOGO_FILE = Path(__file__).resolve().parent / "assets" / "logo_santa_verginia.png"
SESSION_KEY = "sigcf_auth"

LOGO_FRAME_CSS = (
    ".logo-frame{background:linear-gradient(145deg,#0a1628,#0d2040);border:2px solid #c9a227;"
    "border-radius:12px;padding:5px;display:inline-block;}"
    ".logo-frame img{display:block;border-radius:8px;}"
)


def logo_html(width: int = 118) -> str:
    # URL externa no Cloud — evita base64 pesado no boot
    src = LOGO_URL
    return f'<div class="logo-frame"><img src="{src}" width="{width}" alt="Santa Virginia"></div>'


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
            "Secrets do Supabase nao encontrados. No Streamlit Cloud: "
            "Settings → Secrets → SUPABASE_URL e SUPABASE_KEY, depois Reboot app."
        )
        st.stop()
    return create_client(url, key)


def exigir_acesso(titulo: str, subtitulo: str = "Acesso restrito — SIGCF Santa Virginia"):
    import streamlit as st

    pin_cfg = _secret("APP_PIN", "").strip()
    if not pin_cfg or st.session_state.get(SESSION_KEY):
        return

    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"]{{background:#0a1409;}}
        h1,h2,p,label{{color:#e8edd0;}}
        {LOGO_FRAME_CSS}
        </style>
        """,
        unsafe_allow_html=True,
    )
    col_logo, col_titulo = st.columns([1, 4])
    with col_logo:
        st.markdown(logo_html(), unsafe_allow_html=True)
    with col_titulo:
        st.title(titulo)
        st.caption(subtitulo)

    pin = st.text_input("PIN de acesso", type="password", key="sigcf_login_pin")
    if st.button("Entrar", type="primary", key="sigcf_login_btn"):
        if pin == pin_cfg:
            st.session_state[SESSION_KEY] = True
            st.rerun()
        else:
            st.error("PIN incorreto.")
    st.stop()
