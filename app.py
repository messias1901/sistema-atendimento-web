import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema de Gestão - Coordenação", layout="wide")

# --- 2. BANCO DE DADOS (CRIAÇÃO AUTOMÁTICA) ---
def inicializar_banco():
    conn = sqlite3.connect('atendimentos.db')
    c = conn.cursor()
    # Tabela de Atendimentos
    c.execute('''CREATE TABLE IF NOT EXISTS atendimentos 
                 (data TEXT, ra TEXT, nome TEXT, curso TEXT, serie TEXT, turno TEXT, descricao TEXT, usuario_dono TEXT)''')
    
    # Tabela de Utilizadores (Login)
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (username TEXT PRIMARY KEY, password TEXT, perfil TEXT)''')
    
    # Criar utilizador admin padrão se não existir (Login: admin / Senha: admin123)
    c.execute("INSERT OR IGNORE INTO usuarios (username, password, perfil) VALUES ('admin', 'admin123', 'admin')")
    
    conn.commit()
    conn.close()

inicializar_banco()

# --- 3. INICIALIZAÇÃO DO ESTADO DA SESSÃO (Evita o AttributeError) ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

if "perfil_logado" not in st.session_state:
    st.session_state.perfil_logado = None

# --- 4. TELA DE LOGIN ---
if not st.session_state.autenticado:
    st.title("🔐 Acesso à Coordenação")
    
    col_login, _ = st.columns([1, 2])
    with col_login:
        user_input = st.text_input("Usuário").lower().strip()
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
                st.error("Usuário ou senha incorretos.")
    st.stop()

# --- 5. VARIÁVEIS DE CONTROLE APÓS LOGIN ---
usuario_atual = st.session_state.usuario_logado
perfil_atual = st.session_state.perfil_logado

# --- 6. MENU LATERAL ---
st.sidebar.title(f"Olá, {usuario_atual.capitalize()}!")
st.sidebar.write(f"Perfil: **{perfil_atual.upper()}**")

opcoes_menu = ["Registrar Atendimento", "Visualizar Registros"]
if perfil_atual == "admin":
    opcoes_menu.append("Gerenciar Usuários")

escolha = st.sidebar.selectbox("Navegação", opcoes_menu)

if st.sidebar.button("Sair / Logout"):
    st.session_state.autenticado = False
    st.session_state.usuario_logado = None
    st.session_state.perfil_logado = None
    st.rerun()

# --- 7. FUNCIONALIDADE: GERENCIAR USUÁRIOS (ADMIN APENAS) ---
if escolha == "Gerenciar Usuários" and perfil_atual == "admin":
    st.title("👥 Gestão de Usuários")
    
    tab_novo, tab_lista = st.tabs(["Novo Usuário", "Usuários Ativos"])
    
    with tab_novo:
        with st.form("form_novo_usuario"):
            new_u = st.text_input("Nome de Usuário").lower().strip()
            new_p = st.text_input("Senha", type="password")
            new_perf = st.selectbox("Nível de Acesso", ["coordenador", "admin"])
            if st.form_submit_button("Cadastrar Usuário"):
