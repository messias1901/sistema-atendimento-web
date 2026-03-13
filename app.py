import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Coordenação Web", layout="centered")

# Função para conectar ao banco de dados interno
def criar_banco():
    conn = sqlite3.connect('atendimentos.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS atendimentos 
                 (data TEXT, ra TEXT, nome TEXT, curso TEXT, serie TEXT, turno TEXT, descricao TEXT)''')
    conn.commit()
    conn.close()

criar_banco()

st.title("📝 Coordenação - Atendimentos")

# Formulário
with st.form("meu_formulario", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        data = st.date_input("Data", value=datetime.now())
        ra = st.text_input("RA")
        curso = st.selectbox("Curso", ["Direito", "Engenharia", "Administração", "Psicologia"])
    with col2:
        nome = st.text_input("Nome do Aluno")
        serie = st.selectbox("Série", ["1ª", "2ª", "3ª", "4ª", "5ª"])
        turno = st.selectbox("Turno", ["Matutino", "Vespertino", "Noturno"])
    
    descricao = st.text_area("Descrição")
    btn_salvar = st.form_submit_button("Salvar Registro")

if btn_salvar:
    if nome and ra:
        conn = sqlite3.connect('atendimentos.db')
        c = conn.cursor()
        c.execute("INSERT INTO atendimentos VALUES (?,?,?,?,?,?,?)", 
                  (data.strftime("%d/%m/%Y"), ra, nome, curso, serie, turno, descricao))
        conn.commit()
        conn.close()
        st.success("Salvo com sucesso!")
    else:
        st.error("Preencha Nome e RA.")

# --- PARTE DE GERENCIAMENTO (BAIXAR EXCEL) ---
st.divider()
st.subheader("📊 Gerenciar Dados")

conn = sqlite3.connect('atendimentos.db')
df = pd.read_sql_query("SELECT * FROM atendimentos", conn)
conn.close()

if not df.empty:
    st.write("Últimos registros:")
    st.dataframe(df.tail(5))
    
    # Botão para baixar o Excel
    import io
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Atendimentos')
    
    st.download_button(
        label="📥 Baixar Planilha Completa (Excel)",
        data=buffer.getvalue(),
        file_name=f"atendimentos_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
        mime="application/vnd.ms-excel"
    )
else:
    st.info("Nenhum atendimento registrado ainda.")