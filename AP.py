# app.py
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Configuração inicial do Streamlit
st.set_page_config(page_title="Sistema de Gestão de Granja", layout="wide")

# Conexão com o banco de dados
def criar_conexao():
    conn = sqlite3.connect('granja.db')
    return conn

def criar_tabelas():
    conn = criar_conexao()
    cursor = conn.cursor()
    
    # Tabela de Lotes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            data_entrada DATE,
            quantidade_inicial INTEGER,
            linhagem TEXT,
            status TEXT DEFAULT 'ativo'
        )
    ''')
    
    # Tabela de Mortalidade
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mortalidade (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lote_id INTEGER,
            data DATE,
            quantidade INTEGER,
            causa TEXT,
            FOREIGN KEY (lote_id) REFERENCES lotes (id)
        )
    ''')
    
    # Tabela de Pesagens
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pesagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lote_id INTEGER,
            data DATE,
            peso_medio FLOAT,
            uniformidade FLOAT,
            FOREIGN KEY (lote_id) REFERENCES lotes (id)
        )
    ''')
    
    # Tabela de Consumo
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS consumo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lote_id INTEGER,
            data DATE,
            tipo_racao TEXT,
            quantidade FLOAT,
            FOREIGN KEY (lote_id) REFERENCES lotes (id)
        )
    ''')
    
    # Tabela de Funcionários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS funcionarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            funcao TEXT,
            data_admissao DATE
        )
    ''')
    
    # Tabela de Controle Ambiental
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ambiente (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lote_id INTEGER,
            data DATETIME,
            temperatura FLOAT,
            umidade FLOAT,
            FOREIGN KEY (lote_id) REFERENCES lotes (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Funções de Gestão de Lotes
def cadastrar_lote(codigo, data_entrada, quantidade_inicial, linhagem):
    conn = criar_conexao()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO lotes (codigo, data_entrada, quantidade_inicial, linhagem)
            VALUES (?, ?, ?, ?)
        ''', (codigo, data_entrada, quantidade_inicial, linhagem))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def listar_lotes():
    conn = criar_conexao()
    df = pd.read_sql_query("SELECT * FROM lotes", conn)
    conn.close()
    return df

# Funções de Registro de Mortalidade
def registrar_mortalidade(lote_id, data, quantidade, causa):
    conn = criar_conexao()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO mortalidade (lote_id, data, quantidade, causa)
        VALUES (?, ?, ?, ?)
    ''', (lote_id, data, quantidade, causa))
    conn.commit()
    conn.close()

def obter_mortalidade_por_lote(lote_id):
    conn = criar_conexao()
    df = pd.read_sql_query('''
        SELECT data, SUM(quantidade) as total_mortes, causa
        FROM mortalidade
        WHERE lote_id = ?
        GROUP BY data, causa
    ''', conn, params=[lote_id])
    conn.close()
    return df

# Funções de Controle de Pesagens
def registrar_pesagem(lote_id, data, peso_medio, uniformidade):
    conn = criar_conexao()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO pesagens (lote_id, data, peso_medio, uniformidade)
        VALUES (?, ?, ?, ?)
    ''', (lote_id, data, peso_medio, uniformidade))
    conn.commit()
    conn.close()

def obter_pesagens_por_lote(lote_id):
    conn = criar_conexao()
    df = pd.read_sql_query('''
        SELECT data, peso_medio, uniformidade
        FROM pesagens
        WHERE lote_id = ?
        ORDER BY data
    ''', conn, params=[lote_id])
    conn.close()
    return df

# Funções de Gestão de Consumo
def registrar_consumo(lote_id, data, tipo_racao, quantidade):
    conn = criar_conexao()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO consumo (lote_id, data, tipo_racao, quantidade)
        VALUES (?, ?, ?, ?)
    ''', (lote_id, data, tipo_racao, quantidade))
    conn.commit()
    conn.close()

def obter_consumo_por_lote(lote_id):
    conn = criar_conexao()
    df = pd.read_sql_query('''
        SELECT data, tipo_racao, quantidade
        FROM consumo
        WHERE lote_id = ?
        ORDER BY data
    ''', conn, params=[lote_id])
    conn.close()
    return df

# Funções de Análise e Gráficos
def gerar_grafico_mortalidade(lote_id):
    df = obter_mortalidade_por_lote(lote_id)
    fig = px.line(df, x='data', y='total_mortes', title='Evolução da Mortalidade')
    return fig

def gerar_grafico_peso(lote_id):
    df = obter_pesagens_por_lote(lote_id)
    fig = px.line(df, x='data', y='peso_medio', title='Evolução do Peso Médio')
    return fig

def gerar_grafico_consumo(lote_id):
    df = obter_consumo_por_lote(lote_id)
    fig = px.bar(df, x='data', y='quantidade', color='tipo_racao',
                 title='Consumo de Ração por Tipo')
    return fig

# Interface Streamlit
def main():
    st.title("Sistema de Gestão de Granja")
    
    menu = st.sidebar.selectbox(
        "Menu",
        ["Início", "Gestão de Lotes", "Mortalidade", "Pesagens", "Consumo", "Análises"]
    )
    
    if menu == "Início":
        st.write("Bem-vindo ao Sistema de Gestão de Granja")
        st.write("Selecione uma opção no menu lateral para começar.")
        
        # Dashboard resumido
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Lotes Ativos", 
                     len(listar_lotes()[listar_lotes()['status'] == 'ativo']))
        
    elif menu == "Gestão de Lotes":
        st.subheader("Cadastro de Novo Lote")
        
        codigo = st.text_input("Código do Lote")
        data_entrada = st.date_input("Data de Entrada")
        quantidade_inicial = st.number_input("Quantidade Inicial", min_value=1)
        linhagem = st.selectbox("Linhagem", ["Ross", "Cobb", "Hubbard"])
        
        if st.button("Cadastrar Lote"):
            if cadastrar_lote(codigo, data_entrada, quantidade_inicial, linhagem):
                st.success("Lote cadastrado com sucesso!")
            else:
                st.error("Erro ao cadastrar lote. Código já existe.")
        
        st.subheader("Lotes Cadastrados")
        st.dataframe(listar_lotes())
        
    elif menu == "Mortalidade":
        st.subheader("Registro de Mortalidade")
        
        lotes_df = listar_lotes()
        lote_selecionado = st.selectbox("Selecione o Lote", 
                                       lotes_df['codigo'].tolist())
        lote_id = lotes_df[lotes_df['codigo'] == lote_selecionado]['id'].iloc[0]
        
        data = st.date_input("Data do Registro")
        quantidade = st.number_input("Quantidade", min_value=1)
        causa = st.selectbox("Causa", ["Doença", "Acidentes", "Outras"])
        
        if st.button("Registrar Mortalidade"):
            registrar_mortalidade(lote_id, data, quantidade, causa)
            st.success("Mortalidade registrada com sucesso!")
        
        st.subheader("Histórico de Mortalidade")
        st.plotly_chart(gerar_grafico_mortalidade(lote_id))
        
    elif menu == "Pesagens":
        st.subheader("Registro de Pesagens")
        
        lotes_df = listar_lotes()
        lote_selecionado = st.selectbox("Selecione o Lote", 
                                       lotes_df['codigo'].tolist())
        lote_id = lotes_df[lotes_df['codigo'] == lote_selecionado]['id'].iloc[0]
        
        data = st.date_input("Data da Pesagem")
        peso_medio = st.number_input("Peso Médio (g)", min_value=0.0)
        uniformidade = st.number_input("Uniformidade (%)", min_value=0.0, max_value=100.0)
        
        if st.button("Registrar Pesagem"):
            registrar_pesagem(lote_id, data, peso_medio, uniformidade)
            st.success("Pesagem registrada com sucesso!")
        
        st.subheader("Evolução do Peso")
        st.plotly_chart(gerar_grafico_peso(lote_id))
        
    elif menu == "Consumo":
        st.subheader("Registro de Consumo")
        
        lotes_df = listar_lotes()
        lote_selecionado = st.selectbox("Selecione o Lote", 
                                       lotes_df['codigo'].tolist())
        lote_id = lotes_df[lotes_df['codigo'] == lote_selecionado]['id'].iloc[0]
        
        data = st.date_input("Data do Consumo")
        tipo_racao = st.selectbox("Tipo de Ração", 
                                 ["Pré-inicial", "Inicial", "Crescimento", "Final"])
        quantidade = st.number_input("Quantidade (kg)", min_value=0.0)
        
        if st.button("Registrar Consumo"):
            registrar_consumo(lote_id, data, tipo_racao, quantidade)
            st.success("Consumo registrado com sucesso!")
        
        st.subheader("Histórico de Consumo")
        st.plotly_chart(gerar_grafico_consumo(lote_id))
        
    elif menu == "Análises":
        st.subheader("Análises e Relatórios")
        
        lotes_df = listar_lotes()
        lote_selecionado = st.selectbox("Selecione o Lote", 
                                       lotes_df['codigo'].tolist())
        lote_id = lotes_df[lotes_df['codigo'] == lote_selecionado]['id'].iloc[0]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(gerar_grafico_mortalidade(lote_id))
            st.plotly_chart(gerar_grafico_consumo(lote_id))
            
        with col2:
            st.plotly_chart(gerar_grafico_peso(lote_id))

if __name__ == "__main__":
    criar_tabelas()
    main()