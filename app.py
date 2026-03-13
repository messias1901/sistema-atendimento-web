import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema de Gestão - Coordenação", layout="wide")

# --- 2. BANCO DE DADOS (COM TABELA DE UTILIZADORES) ---
def inicializar_banco():
    conn = sqlite3.connect('atendimentos.db')
    c = conn.cursor()
    # Tabela de Atendimentos
    c.execute('''CREATE TABLE IF NOT EXISTS atendimentos 
                 (data TEXT, ra TEXT, nome TEXT, curso TEXT, serie TEXT, turno TEXT, descricao TEXT, usuario_dono TEXT)''')
    
    # Tabela de Utilizadores (Login)
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (username TEXT PRIMARY KEY, password TEXT, perfil TEXT)''')
    
    # Criar utilizador admin padrão se não existir
    c.execute("INSERT OR IGNORE INTO usuarios (username, password, perfil) VALUES ('admin', 'admin123', 'admin')")
    
    conn.commit()
    conn.close()

inicializar_banco()

# --- 3. SISTEMA DE LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔐 Acesso à Coordenação")
    user_input = st.text_input("Utilizador").lower().strip()
    pass_input = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        conn = sqlite3.connect('atendimentos.db')
        c = conn.cursor()
        c.execute("SELECT password, perfil FROM usuarios WHERE username = ?", (user_input,))
        res = c.fetchone()
        conn.close()
        
        if res and res[0] == pass_input:
            st.session_state.autenticado = True
            st.session_state.usuario_logado = user_input
            st.session_state.perfil_logado = res[1]
            st.rerun()
        else:
            st.error("Utilizador ou senha incorretos.")
    st.stop()

# --- 4. MENU LATERAL ---
usuario_atual = st.session_state.usuario_logado
perfil_atual = st.session_state.perfil_logado

st.sidebar.title(f"Olá, {usuario_atual.capitalize()}!")
menu = ["Registos", "Meus Dados"]
if perfil_atual == "admin":
    menu.append("Gerir Utilizadores")

escolha = st.sidebar.selectbox("Navegação", menu)

if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- 5. FUNCIONALIDADE: GERIR UTILIZADORES (APENAS ADMIN) ---
if escolha == "Gerir Utilizadores":
    st.title("👥 Gestão de Utilizadores")
    
    tab1, tab2 = st.tabs(["Novo Utilizador", "Utilizadores Atuais"])
    
    with tab1:
        with st.form("novo_user"):
            new_user = st.text_input("Nome de Utilizador (ex: ana.paula)").lower().strip()
            new_pass = st.text_input("Senha Inicial", type="password")
            new_perfil = st.selectbox("Perfil", ["coordenador", "admin"])
            if st.form_submit_button("Criar Utilizador"):
                if new_user and new_pass:
                    try:
                        conn = sqlite3.connect('atendimentos.db')
                        c = conn.cursor()
                        c.execute("INSERT INTO usuarios VALUES (?,?,?)", (new_user, new_pass, new_perfil))
                        conn.commit()
                        conn.close()
                        st.success(f"Utilizador {new_user} criado!")
                    except:
                        st.error("Este utilizador já existe.")
                else:
                    st.warning("Preencha todos os campos.")

    with tab2:
        conn = sqlite3.connect('atendimentos.db')
        df_users = pd.read_sql_query("SELECT username, perfil FROM usuarios", conn)
        conn.close()
        st.dataframe(df_users, use_container_width=True)

# --- 6. FUNCIONALIDADE: REGISTOS (FORMULÁRIO) ---
elif escolha == "Registos":
    st.title("📝 Novo Atendimento")
    with st.form("atendimento_form", clear_on_submit=True):
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
        if st.form_submit_button("Salvar"):
            if nome and ra:
                conn = sqlite3.connect('atendimentos.db')
                c = conn.cursor()
                c.execute("INSERT INTO atendimentos VALUES (?,?,?,?,?,?,?,?)", 
                          (data.strftime("%d/%m/%Y"), ra, nome, curso, serie, turno, descricao, usuario_atual))
                conn.commit()
                conn.close()
                st.success("Registado!")
            else:
                st.error("Preencha Nome e RA.")

# --- 7. FUNCIONALIDADE: VISUALIZAÇÃO ---
elif escolha == "Meus Dados":
    st.title("📊 Registos Guardados")
    conn = sqlite3.connect('atendimentos.db')
    if perfil_atual == "admin":
        df = pd.read_sql_query("SELECT * FROM atendimentos", conn)
    else:
        df = pd.read_sql_query("SELECT * FROM atendimentos WHERE usuario_dono = ?", conn, params=(usuario_atual,))
    conn.close()

    if not df.empty:
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Baixar Excel (CSV)", csv, "relatorio.csv", "text/csv")
    else:
        st.info("Sem registos encontrados.")
