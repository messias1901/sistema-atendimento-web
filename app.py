import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema de Atendimento - Coordenação", layout="wide")

# --- 2. BANCO DE DADOS (COM AUTO-REPARO) ---
def inicializar_banco():
    conn = sqlite3.connect('atendimentos.db')
    c = conn.cursor()
    # Cria a tabela base se não existir
    c.execute('''CREATE TABLE IF NOT EXISTS atendimentos 
                 (data TEXT, ra TEXT, nome TEXT, curso TEXT, serie TEXT, turno TEXT, descricao TEXT)''')
    
    # Tenta adicionar a coluna usuario_dono caso ela não exista (Migração de banco antigo)
    try:
        c.execute("ALTER TABLE atendimentos ADD COLUMN usuario_dono TEXT")
    except sqlite3.OperationalError:
        # Se cair aqui, é porque a coluna já existe. Tudo certo!
        pass
        
    conn.commit()
    conn.close()

inicializar_banco()

# --- 3. SISTEMA DE LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔐 Acesso à Coordenação")
    
    with st.container():
        user_input = st.text_input("Usuário").lower().strip()
        pass_input = st.text_input("Senha", type="password")
        
        if st.button("Entrar"):
            # Verifica se o usuário existe nos Secrets e se a senha bate
            if user_input in st.secrets["usuarios"] and pass_input == st.secrets["usuarios"][user_input]:
                st.session_state.autenticado = True
                st.session_state.usuario_logado = user_input
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
    st.stop()

# --- 4. INTERFACE PRINCIPAL ---
usuario_atual = st.session_state.usuario_logado

st.sidebar.title(f"Bem-vindo(a)!")
st.sidebar.info(f"Usuário: **{usuario_atual.upper()}**")
if st.sidebar.button("Sair / Logout"):
    st.session_state.autenticado = False
    st.rerun()

st.title("📝 Registro de Atendimentos")

# --- 5. FORMULÁRIO DE CADASTRO ---
with st.form("atendimento_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        data = st.date_input("Data do Atendimento", value=datetime.now())
        ra = st.text_input("RA do Aluno")
        curso = st.selectbox("Curso", ["Direito", "Engenharia", "Administração", "Psicologia", "Pedagogia", "Sistemas"])
    
    with col2:
        nome = st.text_input("Nome Completo do Aluno")
        serie = st.selectbox("Série/Ano", ["1ª", "2ª", "3ª", "4ª", "5ª", "6ª"])
        turno = st.selectbox("Turno", ["Matutino", "Vespertino", "Noturno"])
        
    descricao = st.text_area("Descrição do Atendimento")
    
    if st.form_submit_button("✅ Salvar Atendimento"):
        if nome and ra:
            try:
                conn = sqlite3.connect('atendimentos.db')
                c = conn.cursor()
                c.execute("""INSERT INTO atendimentos (data, ra, nome, curso, serie, turno, descricao, usuario_dono) 
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                          (data.strftime("%d/%m/%Y"), ra, nome, curso, serie, turno, descricao, usuario_atual))
                conn.commit()
                conn.close()
                st.success(f"Atendimento de {nome} salvo com sucesso!")
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
        else:
            st.warning("Por favor, preencha os campos obrigatórios (Nome e RA).")

# --- 6. VISUALIZAÇÃO E RELATÓRIO ---
st.divider()

if usuario_atual == "admin":
    st.subheader("📊 Relatório Geral (Todos os Coordenadores)")
    query = "SELECT * FROM atendimentos"
    params = ()
else:
    st.subheader(f"📊 Meus Registros ({usuario_atual.capitalize()})")
    query = "SELECT * FROM atendimentos WHERE usuario_dono = ?"
    params = (usuario_atual,)

try:
    conn = sqlite3.connect('atendimentos.db')
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    if not df.empty:
        # Se for admin, mostra a coluna de quem atendeu. Se for user comum, esconde.
        if usuario_atual != "admin":
            df_display = df.drop(columns=['usuario_dono'])
        else:
            df_display = df
            
        st.dataframe(df_display, use_container_width=True)
        
        # Botão de Download (CSV compatível com Excel)
        csv = df_display.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Baixar Planilha (Excel/CSV)",
            data=csv,
            file_name=f"atendimentos_{usuario_atual}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("Nenhum registro encontrado.")
except Exception as e:
    st.error("Erro ao carregar dados. Tente reiniciar o app ou salvar um novo dado.")
