import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

def registrar_os():
    st.subheader("Registro de Manutenção")
    
    # Conexão com a planilha configurada em Sistema_Frota
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    try:
        # Lê a aba 'frota' (conforme sua instrução de nomenclatura)
        df_frota = conn.read(worksheet="frota")
        
        # Usa a coluna 'FROTA' para popular o selectbox
        lista_frotas = df_frota['FROTA'].tolist()
    except Exception:
        lista_frotas = []

    if not lista_frotas:
        st.warning("Nenhuma frota cadastrada. Verifique a aba 'frota' na sua planilha.")
    else:
        with st.container():
            col1, col2 = st.columns(2)
            # Popula a interface com os dados reais do Google Sheets
            frota_sel = col1.selectbox("Frota", options=lista_frotas)
            horimetro = col2.number_input("Horímetro", step=0.01)
            
            col3, col4 = st.columns(2)
            mecanico = col3.text_input("Mecânico")
            tipo = col4.selectbox("Tipo", options=["OFICINA", "EXTERNA"])
            
            descricao_servico = st.text_area("Descrição do Serviço")
            
            if st.button("SALVAR"):
                # Prepara os dados para salvar na aba de movimentação (ex: 'historico_os')
                nova_os = pd.DataFrame([{
                    "FROTA": frota_sel,
                    "HORIMETRO": horimetro,
                    "MECANICO": mecanico,
                    "TIPO": tipo,
                    "DESCRICAO": descricao_servico
                }])
                
                # Lógica para anexar os dados na planilha
                # conn.create(worksheet="historico_os", data=nova_os)
                st.success(f"O.S. para {frota_sel} registrada com sucesso!")