import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Sistema Privado - Coordenação", layout="centered")

# --- SISTEMA DE LOGIN SIMPLES ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔐 Acesso Restrito")
    user_input = st.text_input("Usuário").lower().strip()
    pass_input = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        if user_input in st.secrets["usuarios"] and pass_input == st.secrets["usuarios"][user_input]:
            st.session_state.autenticado = True
            st.session_state.usuario_logado = user_input
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")
    st.stop()

# --- SE CHEGOU AQUI, ESTÁ LOGADO ---
usuario_atual = st.session_state.usuario_logado
st.sidebar.write(f"Logado como: **{usuario_atual.capitalize()}**")
if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- BANCO DE DATOS (COM COLUNA DE USUÁRIO) ---
def criar_banco():
    conn = sqlite3.connect('atendimentos.db')
    c = conn.cursor()
    # Adicionamos a coluna 'usuario_dono' para rastrear de quem é o dado
    c.execute('''CREATE TABLE IF NOT EXISTS atendimentos 
                 (data TEXT, ra TEXT, nome TEXT, curso TEXT, serie TEXT, turno TEXT, descricao TEXT, usuario_dono TEXT)''')
    conn.commit()
    conn.close()

criar_banco()

st.title(f"📝 Meus Atendimentos")

# Formulário de Cadastro
with st.form("form_privado", clear_on_submit=True):
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
    if st.form_submit_button("Salvar Registro"):
        if nome and ra:
            conn = sqlite3.connect('atendimentos.db')
            c = conn.cursor()
            c.execute("INSERT INTO atendimentos VALUES (?,?,?,?,?,?,?,?)", 
                      (data.strftime("%d/%m/%Y"), ra, nome, curso, serie, turno, descricao, usuario_atual))
            conn.commit()
            conn.close()
            st.success("Salvo apenas na sua conta!")
        else:
            st.error("Preencha Nome e RA.")

# --- VISUALIZAÇÃO FILTRADA (SEGURANÇA) ---
st.divider()
st.subheader("📊 Meus Registros Salvos")

conn = sqlite3.connect('atendimentos.db')
# O segredo está aqui: filtramos no banco apenas os dados do usuário atual
query = "SELECT * FROM atendimentos WHERE usuario_dono = ?"
df = pd.read_sql_query(query, conn, params=(usuario_atual,))
conn.close()

if not df.empty:
    st.dataframe(df.drop(columns=['usuario_dono'])) # Removemos a coluna de usuário da visualização para ficar limpo
    
    # Exportação exclusiva dos dados dele
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Baixar Meus Dados (Excel)", data=csv, file_name=f"atendimentos_{usuario_atual}.csv", mime="text/csv")
else:
    st.info("Você ainda não possui atendimentos registrados.")

# --- A PARTIR DESTA LINHA (Substitua o final do seu app.py) ---
st.divider()

# Título dinâmico dependendo de quem logou
if usuario_atual == "admin":
    st.subheader("📊 Painel de Controle (ADMIN) - Todos os Registros")
else:
    st.subheader("📊 Meus Registros Salvos")

conn = sqlite3.connect('atendimentos.db')

# Lógica de busca: Admin vê tudo, Usuário vê só o seu
if usuario_atual == "admin":
    query = "SELECT * FROM atendimentos"
    df = pd.read_sql_query(query, conn)
else:
    query = "SELECT * FROM atendimentos WHERE usuario_dono = ?"
    df = pd.read_sql_query(query, conn, params=(usuario_atual,))

conn.close()

if not df.empty:
    # Mostra a tabela na tela
    st.dataframe(df)
    
    # Prepara o arquivo para baixar
    csv = df.to_csv(index=False).encode('utf-8-sig')
    
    # Nome do botão também muda para o Admin
    label_botao = "📥 Baixar Relatório Geral (Excel)" if usuario_atual == "admin" else "📥 Baixar Meus Dados"
    
    st.download_button(
        label=label_botao,
        data=csv,
        file_name=f"atendimentos_{usuario_atual}.csv",
        mime="text/csv"
    )
else:
    st.info("Nenhum registro encontrado.")
