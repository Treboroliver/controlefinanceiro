import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Cashflow Web", page_icon="💰", layout="wide")

# ==========================================
# 1. FUNÇÕES DE BASE DE DADOS E POP-UPS
# ==========================================
def init_db():
    conn = sqlite3.connect('cashflow.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)''')
    
    # Tabela principal atualizada com forma de pagamento
    c.execute('''CREATE TABLE IF NOT EXISTS transacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, estabelecimento TEXT, 
                    descricao TEXT, tipo_pgto TEXT, valor_total REAL, qtd_parc INTEGER, 
                    valor_parcela REAL, forma_pgto TEXT, cartao TEXT, categoria TEXT, devedor TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS receitas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, origem TEXT, 
                    conta TEXT, recebimento TEXT, valor REAL)''')

    c.execute('''CREATE TABLE IF NOT EXISTS contas_fixas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, dia INTEGER, valor REAL, descricao TEXT,
                    estabelecimento TEXT, forma_pgto TEXT, cartao TEXT, categoria TEXT, devedor TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS cartoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, 
                    dia_fechamento INTEGER, dia_vencimento INTEGER, bandeira TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS categorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cor TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS devedores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS estabelecimentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, razao_social TEXT, tipo TEXT)''')
                    
    try:
        c.execute('''ALTER TABLE transacoes ADD COLUMN id_conta_fixa TEXT''')
    except:
        pass
    try:
        c.execute('''ALTER TABLE contas_fixas ADD COLUMN status TEXT DEFAULT 'Ativa' ''')
        c.execute('''ALTER TABLE contas_fixas ADD COLUMN id_referencia TEXT''')
    except:
        pass
    
    c.execute("SELECT * FROM users WHERE username='robert'")
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES ('robert', 'admin123')")
    conn.commit()
    conn.close()

def atualizar_bd_tabela(nome_tabela, df_editado):
    conn = sqlite3.connect('cashflow.db')
    c = conn.cursor()
    cols_db = [col for col in df_editado.columns if col not in ['✔', 'PREVISÃO', 'Excluir']]
    
    ids_ativos = df_editado[df_editado['id'].notna()]['id'].tolist()
    if ids_ativos:
        placeholders = ','.join('?' for _ in ids_ativos)
        c.execute(f"DELETE FROM {nome_tabela} WHERE id NOT IN ({placeholders})", ids_ativos)
    else:
        c.execute(f"DELETE FROM {nome_tabela}")
        
    colunas_update = [col for col in cols_db if col != 'id']
    set_clause = ', '.join([f"{col}=?" for col in colunas_update])
    cols_insert = ', '.join(colunas_update)
    vals_insert = ', '.join(['?' for _ in colunas_update])
    
    for _, row in df_editado.iterrows():
        valores = [None if pd.isna(row[col]) else row[col] for col in colunas_update]
        if pd.notna(row['id']):
            c.execute(f"UPDATE {nome_tabela} SET {set_clause} WHERE id=?", valores + [row['id']])
        else:
            c.execute(f"INSERT INTO {nome_tabela} ({cols_insert}) VALUES ({vals_insert})", valores)
    conn.commit()
    conn.close()

def excluir_registos(nome_tabela, df_editado):
    ids_para_excluir = df_editado[df_editado['Excluir'] == True]['id'].tolist()
    if ids_para_excluir:
        conn = sqlite3.connect('cashflow.db')
        c = conn.cursor()
        placeholders = ','.join('?' for _ in ids_para_excluir)
        c.execute(f"DELETE FROM {nome_tabela} WHERE id IN ({placeholders})", ids_para_excluir)
        conn.commit()
        conn.close()
        return True
    return False

def carregar_lista(tabela, coluna):
    conn = sqlite3.connect('cashflow.db')
    try:
        df = pd.read_sql_query(f"SELECT {coluna} FROM {tabela} ORDER BY {coluna} ASC", conn)
        lista = [""] + df[coluna].tolist()
    except:
        lista = [""]
    conn.close()
    return lista

# --- JANELAS POP-UP (MODAIS) ---
@st.dialog("Cadastrar Estabelecimento")
def modal_estabelecimento():
    nome = st.text_input("Nome do Estabelecimento:")
    tipo = st.radio("Tipo:", ["Físico", "Online"], horizontal=True)
    if st.button("Salvar", type="primary"):
        if nome:
            conn = sqlite3.connect('cashflow.db')
            conn.execute('INSERT INTO estabelecimentos (nome, razao_social, tipo) VALUES (?, ?, ?)', (nome.upper(), "", tipo))
            conn.commit()
            conn.close()
            st.rerun()

@st.dialog("Cadastrar Cartão")
def modal_cartao():
    nome = st.text_input("Nome do Cartão:")
    bandeira = st.radio("Bandeira:", ["MasterCard", "Visa"], horizontal=True)
    if st.button("Salvar", type="primary"):
        if nome:
            conn = sqlite3.connect('cashflow.db')
            conn.execute('INSERT INTO cartoes (nome, dia_fechamento, dia_vencimento, bandeira) VALUES (?, ?, ?, ?)', (nome.upper(), 1, 10, bandeira))
            conn.commit()
            conn.close()
            st.rerun()

@st.dialog("Cadastrar Categoria")
def modal_categoria():
    nome = st.text_input("Nome da Categoria:")
    cor = st.color_picker("Cor:", value="#00C49F")
    if st.button("Salvar", type="primary"):
        if nome:
            conn = sqlite3.connect('cashflow.db')
            conn.execute('INSERT INTO categorias (nome, cor) VALUES (?, ?)', (nome.upper(), cor))
            conn.commit()
            conn.close()
            st.rerun()

@st.dialog("Cadastrar Devedor")
def modal_devedor():
    nome = st.text_input("Nome do Devedor:")
    if st.button("Salvar", type="primary"):
        if nome:
            conn = sqlite3.connect('cashflow.db')
            conn.execute('INSERT INTO devedores (nome) VALUES (?)', (nome.upper(),))
            conn.commit()
            conn.close()
            st.rerun()

@st.dialog("Calculadora")
def modal_calculadora():
    st.write("Calculadora Simples")
    expressao = st.text_input("Expressão Matemática (ex: 100 + 50 * 2):")
    if st.button("Calcular", type="primary", use_container_width=True):
        try:
            resultado = eval(expressao, {"__builtins__": None}, {})
            st.success(f"Resultado: {resultado}")
        except Exception:
            st.error("Expressão inválida.")

# ==========================================
# 2. SISTEMA DE LOGIN
# ==========================================
def check_login(username, password):
    conn = sqlite3.connect('cashflow.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    return user is not None

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.markdown("<h1 style='text-align: center;'>CASHFLOW Login</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            user_input = st.text_input("Utilizador")
            pass_input = st.text_input("Palavra-passe", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                init_db()
                if check_login(user_input.strip(), pass_input.strip()):
                    st.session_state['logged_in'] = True
                    st.rerun()
                else:
                    st.error("Credenciais incorretas.")
    st.stop()

# ==========================================
# 3. MENU DE NAVEGAÇÃO LATERAL
# ==========================================
with st.sidebar:
    st.title("CASHFLOW")
    menu_selecionado = st.radio("Navegação", [
        "Dashboard", 
        "Registrar Nova Despesa", 
        "Gestão de Receitas", 
        "Contas Fixas / Assinaturas",
        "Cadastro de Cartões",
        "Gestão de Categorias",
        "Gestão de Estabelecimentos",
        "Gestão de Devedores"
    ])
    st.divider()
    if st.button("Sair", use_container_width=True):
        st.session_state['logged_in'] = False
        st.rerun()

txt_ajuda_edicao = "💡 **Dica:** Duplo clique para editar. Marque 'Excluir' e clique no botão vermelho para apagar."

# ==========================================
# 4. CONTROLADOR DE ECRÃS
# ==========================================

if menu_selecionado == "Dashboard":
    import datetime
    
    agora = datetime.datetime.now()
    ano_atual = agora.year
    mes_atual = agora.month
    
    meses_nomes = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    anos_lista = [""] + [str(y) for y in range(2020, ano_atual + 10)]
    
    if 'filtro_ano' not in st.session_state:
        st.session_state['filtro_ano'] = ""
    if 'filtro_mes' not in st.session_state:
        st.session_state['filtro_mes'] = ""
        
    def set_este_mes():
        st.session_state['filtro_ano'] = str(ano_atual)
        st.session_state['filtro_mes'] = meses_nomes[mes_atual]
        
    def set_proximo_mes():
        m = mes_atual + 1
        a = ano_atual
        if m > 12:
            m = 1
            a += 1
        st.session_state['filtro_ano'] = str(a)
        st.session_state['filtro_mes'] = meses_nomes[m]
        
    def set_todos():
        st.session_state['filtro_ano'] = ""
        st.session_state['filtro_mes'] = ""

    st.markdown("### Filtros")
    col_f1, col_f2, col_f3, col_f4, col_f5, col_f6 = st.columns([1.5, 1.5, 2, 1.5, 1.5, 1.5])
    with col_f1: st.markdown("<p style='margin-top:10px; font-weight:bold;'>Filtro Base:</p>", unsafe_allow_html=True)
    with col_f2: st.selectbox("Ano", anos_lista, key='filtro_ano', label_visibility="collapsed")
    with col_f3: st.selectbox("Mês", meses_nomes, key='filtro_mes', label_visibility="collapsed")
    with col_f4: st.button("Este Mês", type="primary", use_container_width=True, on_click=set_este_mes)
    with col_f5: st.button("Próximo Mês", use_container_width=True, on_click=set_proximo_mes)
    with col_f6: st.button("Todos", use_container_width=True, on_click=set_todos)
    st.divider()

    with st.expander("Filtros Avançados", expanded=False):
        col_adv1, col_adv2, col_adv3, col_adv4 = st.columns(4)
        with col_adv1: f_cartoes = st.multiselect("Cartões", carregar_lista("cartoes", "nome"))
        with col_adv2: f_estab = st.multiselect("Estabelecimentos", carregar_lista("estabelecimentos", "nome"))
        with col_adv3: f_cat = st.multiselect("Categorias", carregar_lista("categorias", "nome"))
        with col_adv4: f_dev = st.multiselect("Devedores", carregar_lista("devedores", "nome"))

    st.divider()

    condicoes = []
    params_sql = []
    condicoes_rec = []
    params_sql_rec = []
    
    ano_sel = st.session_state['filtro_ano']
    mes_sel = st.session_state['filtro_mes']
    
    if ano_sel and mes_sel:
        mes_num = meses_nomes.index(mes_sel)
        condicoes.append("data LIKE ?")
        params_sql.append(f"%/{mes_num:02d}/{ano_sel}")
        condicoes_rec.append("data LIKE ?")
        params_sql_rec.append(f"%/{mes_num:02d}/{ano_sel}")
    elif ano_sel:
        condicoes.append("data LIKE ?")
        params_sql.append(f"%/%/{ano_sel}")
        condicoes_rec.append("data LIKE ?")
        params_sql_rec.append(f"%/%/{ano_sel}")
    elif mes_sel:
        mes_num = meses_nomes.index(mes_sel)
        condicoes.append("data LIKE ?")
        params_sql.append(f"%/{mes_num:02d}/%")
        condicoes_rec.append("data LIKE ?")
        params_sql_rec.append(f"%/{mes_num:02d}/%")

    if f_cartoes:
        places = ','.join('?' for _ in f_cartoes)
        condicoes.append(f"cartao IN ({places})")
        params_sql.extend(f_cartoes)
    if f_estab:
        places = ','.join('?' for _ in f_estab)
        condicoes.append(f"estabelecimento IN ({places})")
        params_sql.extend(f_estab)
    if f_cat:
        places = ','.join('?' for _ in f_cat)
        condicoes.append(f"categoria IN ({places})")
        params_sql.extend(f_cat)
    if f_dev:
        places = ','.join('?' for _ in f_dev)
        condicoes.append(f"devedor IN ({places})")
        params_sql.extend(f_dev)

    filtro_sql = " WHERE " + " AND ".join(condicoes) if condicoes else ""
    params_sql = tuple(params_sql)
    
    filtro_sql_rec = " WHERE " + " AND ".join(condicoes_rec) if condicoes_rec else ""
    params_sql_rec = tuple(params_sql_rec)

    # Leitura Real da Base de Dados para o Dashboard
    conn = sqlite3.connect('cashflow.db')
    
    saldo_anterior = 0.0
    if ano_sel:
        if mes_sel:
            mes_num = meses_nomes.index(mes_sel)
            limite_ym = f"{ano_sel}{mes_num:02d}"
        else:
            limite_ym = f"{ano_sel}01"
            
        c_rec = pd.read_sql_query(f"SELECT SUM(valor) as total FROM receitas WHERE substr(data,7,4) || substr(data,4,2) < '{limite_ym}'", conn)
        c_desp = pd.read_sql_query(f"SELECT SUM(valor_parcela) as total FROM transacoes WHERE substr(data,7,4) || substr(data,4,2) < '{limite_ym}'", conn)
        prev_rec = c_rec['total'][0] if pd.notna(c_rec['total'][0]) else 0.0
        prev_desp = c_desp['total'][0] if pd.notna(c_desp['total'][0]) else 0.0
        saldo_anterior = prev_rec - prev_desp

    df_rec = pd.read_sql_query(f"SELECT SUM(valor) as total FROM receitas{filtro_sql_rec}", conn, params=params_sql_rec)
    df_desp = pd.read_sql_query(f"SELECT SUM(valor_parcela) as total FROM transacoes{filtro_sql}", conn, params=params_sql)
    
    total_rec = df_rec['total'][0] if pd.notna(df_rec['total'][0]) else 0.0
    total_desp = df_desp['total'][0] if pd.notna(df_desp['total'][0]) else 0.0
    
    help_rec = None
    help_desp = None
    if saldo_anterior > 0:
        total_rec += saldo_anterior
        help_rec = f"Inclui Saldo Positivo Acumulado (Meses Anteriores): R$ {saldo_anterior:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    elif saldo_anterior < 0:
        total_desp += abs(saldo_anterior)
        help_desp = f"Inclui Dívida Acumulada (Meses Anteriores): R$ {abs(saldo_anterior):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
    saldo = total_rec - total_desp
    
    df_cartao = pd.read_sql_query(f"SELECT cartao as Cartão, SUM(valor_parcela) as Valor FROM transacoes{filtro_sql} GROUP BY cartao", conn, params=params_sql)
    df_estab = pd.read_sql_query(f"SELECT estabelecimento as Estabelecimento, SUM(valor_parcela) as Valor FROM transacoes{filtro_sql} GROUP BY estabelecimento", conn, params=params_sql)
    df_cat = pd.read_sql_query(f"SELECT categoria as Categoria, SUM(valor_parcela) as Valor FROM transacoes{filtro_sql} GROUP BY categoria", conn, params=params_sql)
    df_dev = pd.read_sql_query(f"SELECT devedor as Pessoa, SUM(valor_parcela) as Valor FROM transacoes{filtro_sql} GROUP BY devedor", conn, params=params_sql)
    
    df_rec_m = pd.read_sql_query(f"SELECT substr(data,4,2) as Mes, SUM(valor) as Valor, 'Receita' as Tipo FROM receitas{filtro_sql_rec} GROUP BY Mes", conn, params=params_sql_rec)
    df_desp_m = pd.read_sql_query(f"SELECT substr(data,4,2) as Mes, SUM(valor_parcela) as Valor, 'Despesa' as Tipo FROM transacoes{filtro_sql} GROUP BY Mes", conn, params=params_sql)
    df_mensal = pd.concat([df_rec_m, df_desp_m]) if not df_rec_m.empty or not df_desp_m.empty else pd.DataFrame()
    
    df_rec_a = pd.read_sql_query(f"SELECT substr(data,7,4) as Ano, SUM(valor) as Valor, 'Receita' as Tipo FROM receitas{filtro_sql_rec} GROUP BY Ano", conn, params=params_sql_rec)
    df_desp_a = pd.read_sql_query(f"SELECT substr(data,7,4) as Ano, SUM(valor_parcela) as Valor, 'Despesa' as Tipo FROM transacoes{filtro_sql} GROUP BY Ano", conn, params=params_sql)
    df_anual = pd.concat([df_rec_a, df_desp_a]) if not df_rec_a.empty or not df_desp_a.empty else pd.DataFrame()
    
    conn.close()

    st.markdown("<br>", unsafe_allow_html=True)
    
    col_top_left, col_top_right = st.columns([4, 6])
    
    with col_top_left:
        col_m1, col_m2 = st.columns(2)
        with col_m1: st.metric(label="RECEITAS (+)", value=f"R$ {total_rec:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), help=help_rec)
        with col_m2: st.metric(label="DESPESAS (-)", value=f"R$ {total_desp:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), help=help_desp)
        
        cor_saldo = "#FF4B4B" if saldo < 0 else "#00C49F"
        saldo_formatado = f"R$ {saldo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        fig_rosca = go.Figure(data=[go.Pie(labels=['Receitas', 'Despesas', 'Saldo'], values=[total_rec, total_desp, abs(saldo)], hole=0.7, marker_colors=['#00C49F', '#FFC857', '#FF4B4B'], textinfo='none')])
        fig_rosca.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5), margin=dict(t=30, b=0, l=0, r=0), height=250, annotations=[dict(text=f"SALDO LÍQUIDO<br><span style='font-size:24px; color:{cor_saldo}; font-weight:bold;'>{saldo_formatado}</span>", x=0.5, y=0.5, font_size=14, showarrow=False)])
        st.plotly_chart(fig_rosca, use_container_width=True)
        
    with col_top_right:
        if not df_anual.empty:
            fig_anual = px.bar(df_anual.sort_values('Ano'), x='Ano', y='Valor', color='Tipo', barmode='group', title="RECEITAS VS DESPESAS POR ANO", text_auto='.2f', color_discrete_map={'Receita': '#00C49F', 'Despesa': '#FF4B4B'})
            fig_anual.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', title_x=0.5, margin=dict(l=10, r=10, t=40, b=10), shapes=[dict(type="rect", xref="paper", yref="paper", x0=0, y0=0, x1=1, y1=1, line=dict(color="lightgray", width=1))])
            fig_anual.update_yaxes(visible=False)
            fig_anual.update_xaxes(title=None)
            fig_anual.update_traces(textposition='auto')
            st.plotly_chart(fig_anual, use_container_width=True)

    st.divider()
    
    if not df_mensal.empty:
        df_mensal['Mes_Nome'] = df_mensal['Mes'].apply(lambda m: ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"][int(m)-1] if pd.notna(m) and m.isdigit() else m)
        fig_mensal = px.bar(df_mensal.sort_values('Mes'), x='Mes_Nome', y='Valor', color='Tipo', barmode='group', title="RECEITAS VS DESPESAS POR MÊS", text_auto='.2f', color_discrete_map={'Receita': '#00C49F', 'Despesa': '#FF4B4B'})
        fig_mensal.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', title_x=0.5, margin=dict(l=10, r=10, t=40, b=10), shapes=[dict(type="rect", xref="paper", yref="paper", x0=0, y0=0, x1=1, y1=1, line=dict(color="lightgray", width=1))])
        fig_mensal.update_yaxes(visible=False)
        fig_mensal.update_xaxes(title=None)
        fig_mensal.update_traces(textposition='auto')
        st.plotly_chart(fig_mensal, use_container_width=True)
    
    st.divider()

    def apply_chart_style(fig):
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_visible=False,
            title_x=0.5, margin=dict(l=10, r=40, t=40, b=10),
            shapes=[dict(type="rect", xref="paper", yref="paper", x0=0, y0=0, x1=1, y1=1, line=dict(color="lightgray", width=1))]
        )
        fig.update_yaxes(title=None)
        fig.update_traces(textposition='auto')
        return fig

    col_g1, col_g2, col_g3, col_g4 = st.columns(4)
    with col_g1:
        if not df_cartao.empty:
            fig_cartao = px.bar(df_cartao.sort_values('Valor', ascending=True), x='Valor', y='Cartão', orientation='h', title="CARTÕES", text_auto='.2f', color_discrete_sequence=['#42D6D6'])
            st.plotly_chart(apply_chart_style(fig_cartao), use_container_width=True)
    with col_g2:
        if not df_estab.empty:
            fig_estab = px.bar(df_estab.sort_values('Valor', ascending=True), x='Valor', y='Estabelecimento', orientation='h', title="ESTABELECIMENTOS", text_auto='.2f', color_discrete_sequence=['#42D6D6'])
            st.plotly_chart(apply_chart_style(fig_estab), use_container_width=True)
    with col_g3:
        if not df_cat.empty:
            fig_cat = px.bar(df_cat.sort_values('Valor', ascending=True), x='Valor', y='Categoria', orientation='h', title="CATEGORIAS", text_auto='.2f', color_discrete_sequence=['#42D6D6'])
            st.plotly_chart(apply_chart_style(fig_cat), use_container_width=True)
    with col_g4:
        if not df_dev.empty:
            fig_dev = px.bar(df_dev.sort_values('Valor', ascending=True), x='Valor', y='Pessoa', orientation='h', title="PESSOAS (DEVEDORES)", text_auto='.2f', color_discrete_sequence=['#42D6D6'])
            st.plotly_chart(apply_chart_style(fig_dev), use_container_width=True)

    st.divider()
    st.markdown("### Resumo de Débitos do Período")
    conn = sqlite3.connect('cashflow.db')
    df_resumo = pd.read_sql_query(f"SELECT cartao as Cartão, data as 'Data Vencimento', estabelecimento as Estabelecimento, descricao as Descrição, valor_parcela as Valor, devedor as Pessoa FROM transacoes{filtro_sql} ORDER BY substr(data,7,4) ASC, substr(data,4,2) ASC, substr(data,1,2) ASC", conn, params=params_sql)
    conn.close()
    
    if not df_resumo.empty:
        df_resumo['Valor'] = df_resumo['Valor'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        st.dataframe(df_resumo, hide_index=True, use_container_width=True)
    else:
        st.info("Nenhum débito encontrado para os filtros selecionados.")



# ====================================================
# CADASTRO PRINCIPAL (LANÇAMENTOS) COM POP-UPS E CÁLCULO
# ====================================================
elif menu_selecionado == "Registrar Nova Despesa":
    col_title1, col_title2 = st.columns([8, 2])
    with col_title1: st.header("Registrar Nova Despesa")
    with col_title2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🖩 Calculadora", use_container_width=True):
            modal_calculadora()
            
    lista_cartoes = carregar_lista("cartoes", "nome")
    lista_estab = carregar_lista("estabelecimentos", "nome")
    lista_cat = carregar_lista("categorias", "nome")
    lista_dev = carregar_lista("devedores", "nome")

    data_trans = st.date_input("Data:", format="DD/MM/YYYY")
    
    colE1, colE2 = st.columns([10, 1])
    with colE1: estabelecimento = st.selectbox("Estabelecimento:", lista_estab)
    with colE2: 
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕", key="btn_estab", help="Novo Estabelecimento"): modal_estabelecimento()

    descricao = st.text_input("Descrição:")
    
    st.markdown("**Tipo de Pagamento:**")
    tipo_pgto = st.radio("", ["À Vista", "Parcelado"], horizontal=True, label_visibility="collapsed")
    
    modo_preenchimento = "Digitar Total (Divide a Parc.)"
    if tipo_pgto == "Parcelado":
        st.markdown("**Modo de Preenchimento:**")
        modo_preenchimento = st.radio(
            "", 
            ["Digitar Total (Divide a Parc.)", "Digitar Parcela (Multiplica o Total)"], 
            horizontal=True, 
            label_visibility="collapsed"
        )
    
    colV1, colV2, colV3 = st.columns(3)
    
    if modo_preenchimento == "Digitar Total (Divide a Parc.)":
        with colV1: valor_total = st.number_input("Valor Total (R$):", min_value=0.0, format="%.2f", step=10.0)
        with colV2:
            qtd_parc = st.number_input("Qtd Parc:", min_value=1, step=1, disabled=(tipo_pgto == "À Vista"))
            if tipo_pgto == "À Vista": qtd_parc = 1
        with colV3:
            valor_parcela = valor_total / qtd_parc if qtd_parc > 0 else 0.0
            st.number_input("Valor Parcela (R$):", value=valor_parcela, disabled=True, format="%.2f")
    else:
        with colV2: qtd_parc = st.number_input("Qtd Parc:", min_value=1, step=1)
        with colV3: valor_parcela = st.number_input("Valor Parcela (R$):", min_value=0.0, format="%.2f", step=10.0)
        with colV1:
            valor_total = valor_parcela * qtd_parc
            st.number_input("Valor Total (R$):", value=valor_total, disabled=True, format="%.2f")

    forma_pgto = st.selectbox("Forma de Pagamento:", ["", "CARTÃO DE CRÉDITO", "PIX", "DINHEIRO", "BOLETO"])
    
    colC1, colC2 = st.columns([10, 1])
    with colC1: cartao = st.selectbox("Cartão:", lista_cartoes)
    with colC2: 
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕", key="btn_cartao", help="Novo Cartão"): modal_cartao()

    colCat1, colCat2 = st.columns([10, 1])
    with colCat1: categoria = st.selectbox("Categoria:", lista_cat)
    with colCat2: 
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕", key="btn_cat", help="Nova Categoria"): modal_categoria()

    colD1, colD2 = st.columns([10, 1])
    with colD1: devedor = st.selectbox("Devedor:", lista_dev)
    with colD2: 
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕", key="btn_dev", help="Novo Devedor"): modal_devedor()

    st.markdown("<br>", unsafe_allow_html=True)
    col_btn_cancel, col_btn_save = st.columns(2)
    
    with col_btn_cancel:
        if st.button("Cancelar", type="secondary", use_container_width=True):
            st.rerun()
            
    with col_btn_save:
        if st.button("Salvar Lançamento", type="primary", use_container_width=True):
            if estabelecimento and valor_total > 0:
                conn = sqlite3.connect('cashflow.db')
                c = conn.cursor()
                
                if tipo_pgto == "À Vista":
                    qtd_parc = 1

                import datetime
                import calendar
                
                dia_fechamento = None
                dia_vencimento = None
                mes_venc_base = data_trans.month
                ano_venc_base = data_trans.year
                is_cartao = False

                if forma_pgto == "CARTÃO DE CRÉDITO" and cartao:
                    c.execute("SELECT dia_fechamento, dia_vencimento FROM cartoes WHERE nome = ?", (cartao,))
                    res_cartao = c.fetchone()
                    if res_cartao:
                        dia_fechamento, dia_vencimento = res_cartao
                        is_cartao = True
                        
                        mes_compra = data_trans.month
                        ano_compra = data_trans.year
                        if dia_fechamento < dia_vencimento:
                            if data_trans.day < dia_fechamento:
                                mes_venc_base = mes_compra
                                ano_venc_base = ano_compra
                            else:
                                mes_venc_base = mes_compra + 1
                                ano_venc_base = ano_compra
                                if mes_venc_base > 12:
                                    mes_venc_base = 1
                                    ano_venc_base += 1
                        else:
                            if data_trans.day < dia_fechamento:
                                mes_venc_base = mes_compra + 1
                                ano_venc_base = ano_compra
                                if mes_venc_base > 12:
                                    mes_venc_base = 1
                                    ano_venc_base += 1
                            else:
                                mes_venc_base = mes_compra + 2
                                ano_venc_base = ano_compra
                                if mes_venc_base > 12:
                                    mes_venc_base -= 12
                                    ano_venc_base += 1
                
                for i in range(1, qtd_parc + 1):
                    desc_parc = descricao
                    if qtd_parc > 1:
                        desc_parc = f"{descricao} ({i}/{qtd_parc})" if descricao.strip() else f"Parcela {i}/{qtd_parc}"
                    
                    mes_venc_i = mes_venc_base + (i - 1)
                    ano_venc_i = ano_venc_base + (mes_venc_i - 1) // 12
                    mes_venc_i = (mes_venc_i - 1) % 12 + 1
                    
                    if is_cartao:
                        ultimo_dia_i = calendar.monthrange(ano_venc_i, mes_venc_i)[1]
                        dia_venc_real_i = min(dia_vencimento, ultimo_dia_i)
                        data_parc = datetime.date(ano_venc_i, mes_venc_i, dia_venc_real_i)
                    else:
                        ultimo_dia_i = calendar.monthrange(ano_venc_i, mes_venc_i)[1]
                        dia_venc_real_i = min(data_trans.day, ultimo_dia_i)
                        data_parc = datetime.date(ano_venc_i, mes_venc_i, dia_venc_real_i)

                    c.execute('''INSERT INTO transacoes 
                                 (data, estabelecimento, descricao, tipo_pgto, valor_total, qtd_parc, valor_parcela, forma_pgto, cartao, categoria, devedor) 
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                              (data_parc.strftime('%d/%m/%Y'), estabelecimento, desc_parc, tipo_pgto, valor_total, qtd_parc, valor_parcela, forma_pgto, cartao, categoria, devedor))
                
                conn.commit()
                conn.close()
                st.success("Lançamento registado com sucesso!")
                st.rerun()
            else:
                st.error("Estabelecimento e Valor Total são obrigatórios.")

    st.divider()
    st.subheader("Histórico de Lançamentos")
    st.markdown(txt_ajuda_edicao)
    
    conn = sqlite3.connect('cashflow.db')
    df_trans = pd.read_sql_query("SELECT * FROM transacoes ORDER BY id DESC", conn)
    conn.close()
    
    df_trans.insert(0, "Excluir", False)
    col_config_trans = {
        "id": None,
        "Excluir": st.column_config.CheckboxColumn("Excluir"),
        "valor_total": st.column_config.NumberColumn("Valor Total", format="R$ %.2f"),
        "valor_parcela": st.column_config.NumberColumn("Valor Parcela", format="R$ %.2f")
    }
    edited_trans = st.data_editor(df_trans, num_rows="dynamic", hide_index=True, use_container_width=True, column_config=col_config_trans)
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("💾 Salvar Edições de Texto", type="primary", use_container_width=True, key="save_trans"):
            atualizar_bd_tabela("transacoes", edited_trans)
            st.rerun()
    with col_btn2:
        if st.button("🗑️ Excluir Selecionados", type="secondary", use_container_width=True, key="del_trans"):
            if excluir_registos("transacoes", edited_trans): st.rerun()

# ==========================================
# OUTROS ECRÃS (RECEITAS, CONTAS FIXAS, ETC)
# ==========================================
elif menu_selecionado == "Gestão de Receitas":
    st.header("Gestão de Receitas (Entradas)")
    with st.form("form_receita", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data_rec = st.date_input("Data do Recebimento", format="DD/MM/YYYY")
            conta = st.radio("Tipo de Conta:", ["Salário", "Extra"], horizontal=True)
        with col2:
            valor = st.number_input("Valor (R$):", min_value=0.0, format="%.2f", step=10.0)
            recebimento = st.radio("Tipo de Recebimento:", ["Em Conta", "PIX", "Dinheiro"], horizontal=True)
        origem = st.text_input("Recebido de (Origem):")
        if st.form_submit_button("Salvar Receita", type="primary"):
            if origem and valor > 0:
                conn = sqlite3.connect('cashflow.db')
                conn.execute('INSERT INTO receitas (data, origem, conta, recebimento, valor) VALUES (?, ?, ?, ?, ?)', (data_rec.strftime('%d/%m/%Y'), origem, conta, recebimento, valor))
                conn.commit()
                conn.close()
                st.rerun()

    st.divider()
    st.markdown(txt_ajuda_edicao)
    conn = sqlite3.connect('cashflow.db')
    df_receitas = pd.read_sql_query("SELECT * FROM receitas ORDER BY id DESC", conn)
    conn.close()
    
    df_receitas.insert(0, "Excluir", False)
    col_config_rec = {
        "id": None,
        "Excluir": st.column_config.CheckboxColumn("Excluir"),
        "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f")
    }
    edited_receitas = st.data_editor(df_receitas, num_rows="dynamic", hide_index=True, use_container_width=True, column_config=col_config_rec)
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("💾 Salvar Edições", type="primary", use_container_width=True):
            atualizar_bd_tabela("receitas", edited_receitas)
            st.rerun()
    with col_btn2:
        if st.button("🗑️ Excluir", use_container_width=True):
            if excluir_registos("receitas", edited_receitas): st.rerun()

elif menu_selecionado == "Contas Fixas / Assinaturas":
    st.header("Cadastrar Conta Fixa / Assinatura")
    
    lista_cartoes = carregar_lista("cartoes", "nome")
    lista_estab = carregar_lista("estabelecimentos", "nome")
    lista_cat = carregar_lista("categorias", "nome")
    lista_dev = carregar_lista("devedores", "nome")

    col1, col2 = st.columns(2)
    with col1: dia = st.number_input("Dia do Vencimento (1 a 31):", min_value=1, max_value=31, step=1)
    with col2: valor = st.number_input("Valor (0 se for variável):", min_value=0.0, format="%.2f", step=10.0)
    
    descricao = st.text_input("Descrição da Conta:")
    
    colE1, colE2 = st.columns([10, 1])
    with colE1: estabelecimento = st.selectbox("Estabelecimento:", lista_estab, key="cf_estab")
    with colE2: 
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕", key="cf_btn_estab", help="Novo Estabelecimento"): modal_estabelecimento()

    forma_pgto = st.selectbox("Forma de Pgto:", ["", "Boleto", "Cartão de Crédito", "PIX"], key="cf_forma")
    
    colC1, colC2 = st.columns([10, 1])
    with colC1: cartao = st.selectbox("Cartão:", lista_cartoes, key="cf_cartao")
    with colC2: 
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕", key="cf_btn_cartao", help="Novo Cartão"): modal_cartao()
        
    colCat1, colCat2 = st.columns([10, 1])
    with colCat1: categoria = st.selectbox("Categoria:", lista_cat, key="cf_cat")
    with colCat2: 
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕", key="cf_btn_cat", help="Nova Categoria"): modal_categoria()

    colD1, colD2 = st.columns([10, 1])
    with colD1: devedor = st.selectbox("Devedor:", lista_dev, key="cf_dev")
    with colD2: 
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕", key="cf_btn_dev", help="Novo Devedor"): modal_devedor()
        
    if st.button("Salvar Modelo", type="primary"):
        if descricao:
            import uuid
            import datetime
            import calendar
            
            id_ref = str(uuid.uuid4())
            
            conn = sqlite3.connect('cashflow.db')
            c = conn.cursor()
            c.execute('''INSERT INTO contas_fixas (dia, valor, descricao, estabelecimento, forma_pgto, cartao, categoria, devedor, status, id_referencia) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Ativa', ?)''', 
                      (dia, valor, descricao, estabelecimento, forma_pgto, cartao, categoria, devedor, id_ref))
            
            agora = datetime.datetime.now()
            mes_venc_base = agora.month
            ano_venc_base = agora.year
            is_cartao = False
            dia_fechamento = None
            dia_vencimento = None
            
            if forma_pgto == "CARTÃO DE CRÉDITO" and cartao:
                c.execute("SELECT dia_fechamento, dia_vencimento FROM cartoes WHERE nome = ?", (cartao,))
                res_cartao = c.fetchone()
                if res_cartao:
                    dia_fechamento, dia_vencimento = res_cartao
                    is_cartao = True
                    if dia_fechamento < dia_vencimento:
                        if agora.day >= dia_fechamento:
                            mes_venc_base += 1
                            if mes_venc_base > 12:
                                mes_venc_base = 1; ano_venc_base += 1
                    else:
                        if agora.day < dia_fechamento:
                            mes_venc_base += 1
                            if mes_venc_base > 12:
                                mes_venc_base = 1; ano_venc_base += 1
                        else:
                            mes_venc_base += 2
                            if mes_venc_base > 12:
                                mes_venc_base -= 12; ano_venc_base += 1
                                
            for i in range(12):
                mes_venc_i = mes_venc_base + i
                ano_venc_i = ano_venc_base + (mes_venc_i - 1) // 12
                mes_venc_i = (mes_venc_i - 1) % 12 + 1
                
                if is_cartao:
                    ultimo_dia_i = calendar.monthrange(ano_venc_i, mes_venc_i)[1]
                    dia_venc_real = min(dia_vencimento, ultimo_dia_i)
                    data_parc = datetime.date(ano_venc_i, mes_venc_i, dia_venc_real)
                else:
                    ultimo_dia_i = calendar.monthrange(ano_venc_i, mes_venc_i)[1]
                    dia_venc_real = min(dia, ultimo_dia_i)
                    data_parc = datetime.date(ano_venc_i, mes_venc_i, dia_venc_real)
                    
                desc_parc = f"{descricao} (Assinatura)"
                c.execute('''INSERT INTO transacoes 
                             (data, estabelecimento, descricao, tipo_pgto, valor_total, qtd_parc, valor_parcela, forma_pgto, cartao, categoria, devedor, id_conta_fixa) 
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                          (data_parc.strftime('%d/%m/%Y'), estabelecimento, desc_parc, "À Vista", valor, 1, valor, forma_pgto, cartao, categoria, devedor, id_ref))
            
            conn.commit()
            conn.close()
            st.success("Conta Fixa salva e gerada para os próximos 12 meses!")
            st.rerun()

    st.divider()
    st.markdown(txt_ajuda_edicao)
    conn = sqlite3.connect('cashflow.db')
    df_cf = pd.read_sql_query("SELECT * FROM contas_fixas ORDER BY dia ASC", conn)
    conn.close()
    
    df_cf.insert(0, "Excluir", False)
    col_config = {
        "id": None, 
        "id_referencia": None,
        "Excluir": st.column_config.CheckboxColumn("Excluir"),
        "status": st.column_config.SelectboxColumn("Status", options=["Ativa", "Cancelada"]),
        "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f")
    }
    edited_cf = st.data_editor(df_cf, num_rows="dynamic", hide_index=True, use_container_width=True, column_config=col_config)
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("💾 Salvar Edições", type="primary", use_container_width=True):
            atualizar_bd_tabela("contas_fixas", edited_cf)
            
            import datetime
            hoje = datetime.datetime.now()
            conn = sqlite3.connect('cashflow.db')
            c = conn.cursor()
            
            # Deletar lançamentos futuros de assinaturas canceladas
            c.execute("SELECT id_referencia FROM contas_fixas WHERE status='Cancelada'")
            canceladas = [row[0] for row in c.fetchall() if row[0]]
            if canceladas:
                placeholders = ','.join('?' for _ in canceladas)
                df_trans_canc = pd.read_sql_query(f"SELECT id, data FROM transacoes WHERE id_conta_fixa IN ({placeholders})", conn, params=canceladas)
                ids_to_delete = []
                for _, row in df_trans_canc.iterrows():
                    try:
                        d = datetime.datetime.strptime(row['data'], '%d/%m/%Y')
                        if d > hoje:
                            ids_to_delete.append(row['id'])
                    except:
                        pass
                if ids_to_delete:
                    p = ','.join('?' for _ in ids_to_delete)
                    c.execute(f"DELETE FROM transacoes WHERE id IN ({p})", ids_to_delete)
            
            # Atualizar lançamentos futuros das ativas
            c.execute("SELECT id_referencia, dia, valor, descricao, estabelecimento, forma_pgto, cartao, categoria, devedor FROM contas_fixas WHERE status='Ativa'")
            ativas = c.fetchall()
            for ativa in ativas:
                id_ref, c_dia, c_valor, c_desc, c_estab, c_forma, c_cartao, c_cat, c_dev = ativa
                if id_ref:
                    c.execute("SELECT id, data FROM transacoes WHERE id_conta_fixa=?", (id_ref,))
                    trans_ativas = c.fetchall()
                    for t_id, t_data in trans_ativas:
                        try:
                            d = datetime.datetime.strptime(t_data, '%d/%m/%Y')
                            if d > hoje:
                                desc_parc = f"{c_desc} (Assinatura)"
                                c.execute('''UPDATE transacoes SET valor_total=?, valor_parcela=?, descricao=?, estabelecimento=?, forma_pgto=?, cartao=?, categoria=?, devedor=? WHERE id=?''', 
                                          (c_valor, c_valor, desc_parc, c_estab, c_forma, c_cartao, c_cat, c_dev, t_id))
                        except:
                            pass
                            
            conn.commit()
            conn.close()
            st.rerun()
    with col_btn2:
        if st.button("🗑️ Excluir", use_container_width=True):
            if excluir_registos("contas_fixas", edited_cf): st.rerun()

elif menu_selecionado == "Cadastro de Cartões":
    st.header("Cadastrar Cartão")
    with st.form("form_cartao", clear_on_submit=True):
        nome = st.text_input("Nome do Cartão:")
        col1, col2 = st.columns(2)
        with col1: dia_fechamento = st.number_input("Dia de Fechamento:", min_value=1, max_value=31, step=1)
        with col2: dia_vencimento = st.number_input("Dia do Vencimento:", min_value=1, max_value=31, step=1)
        bandeira = st.radio("Bandeira:", ["MasterCard", "Visa"], horizontal=True)
        if st.form_submit_button("Salvar Cartão", type="primary"):
            if nome:
                conn = sqlite3.connect('cashflow.db')
                conn.execute('INSERT INTO cartoes (nome, dia_fechamento, dia_vencimento, bandeira) VALUES (?, ?, ?, ?)', (nome.upper(), dia_fechamento, dia_vencimento, bandeira))
                conn.commit()
                conn.close()
                st.rerun()

    st.divider()
    st.markdown(txt_ajuda_edicao)
    conn = sqlite3.connect('cashflow.db')
    df_cartoes = pd.read_sql_query("SELECT * FROM cartoes ORDER BY id ASC", conn)
    conn.close()
    df_cartoes.insert(0, "Excluir", False)
    edited_cartoes = st.data_editor(df_cartoes, num_rows="dynamic", hide_index=True, use_container_width=True, column_config={"id": None, "Excluir": st.column_config.CheckboxColumn("Excluir")})
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("💾 Salvar Edições", type="primary", use_container_width=True):
            atualizar_bd_tabela("cartoes", edited_cartoes); st.rerun()
    with col_btn2:
        if st.button("🗑️ Excluir", use_container_width=True):
            if excluir_registos("cartoes", edited_cartoes): st.rerun()

elif menu_selecionado == "Gestão de Categorias":
    st.header("Gestão de Categorias")
    with st.form("form_categoria", clear_on_submit=True):
        nome = st.text_input("Nome da Categoria:")
        cor = st.color_picker("Cor:", value="#00C49F")
        if st.form_submit_button("Salvar Categoria", type="primary"):
            if nome:
                conn = sqlite3.connect('cashflow.db')
                conn.execute('INSERT INTO categorias (nome, cor) VALUES (?, ?)', (nome.upper(), cor))
                conn.commit()
                conn.close()
                st.rerun()

    st.divider()
    st.markdown(txt_ajuda_edicao)
    conn = sqlite3.connect('cashflow.db')
    df_cat = pd.read_sql_query("SELECT * FROM categorias ORDER BY id ASC", conn)
    conn.close()
    df_cat.insert(0, "Excluir", False)
    edited_cat = st.data_editor(df_cat, num_rows="dynamic", hide_index=True, use_container_width=True, column_config={"id": None, "Excluir": st.column_config.CheckboxColumn("Excluir")})
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("💾 Salvar Edições", type="primary", use_container_width=True):
            atualizar_bd_tabela("categorias", edited_cat); st.rerun()
    with col_btn2:
        if st.button("🗑️ Excluir", use_container_width=True):
            if excluir_registos("categorias", edited_cat): st.rerun()

elif menu_selecionado == "Gestão de Estabelecimentos":
    st.header("Gestão de Estabelecimentos")
    with st.form("form_estab", clear_on_submit=True):
        nome = st.text_input("Nome do Estabelecimento:")
        razao_social = st.text_input("Razão Social:")
        tipo = st.radio("Tipo:", ["Físico", "Online"], horizontal=True)
        if st.form_submit_button("Salvar Cadastro", type="primary"):
            if nome:
                conn = sqlite3.connect('cashflow.db')
                conn.execute('INSERT INTO estabelecimentos (nome, razao_social, tipo) VALUES (?, ?, ?)', (nome.upper(), razao_social.upper(), tipo))
                conn.commit()
                conn.close()
                st.rerun()

    st.divider()
    st.markdown(txt_ajuda_edicao)
    conn = sqlite3.connect('cashflow.db')
    df_estab = pd.read_sql_query("SELECT * FROM estabelecimentos ORDER BY id ASC", conn)
    conn.close()
    df_estab.insert(0, "Excluir", False)
    edited_estab = st.data_editor(df_estab, num_rows="dynamic", hide_index=True, use_container_width=True, column_config={"id": None, "Excluir": st.column_config.CheckboxColumn("Excluir")})
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("💾 Salvar Edições", type="primary", use_container_width=True):
            atualizar_bd_tabela("estabelecimentos", edited_estab); st.rerun()
    with col_btn2:
        if st.button("🗑️ Excluir", use_container_width=True):
            if excluir_registos("estabelecimentos", edited_estab): st.rerun()

elif menu_selecionado == "Gestão de Devedores":
    st.header("Gestão de Devedores")
    with st.form("form_devedor", clear_on_submit=True):
        nome = st.text_input("Nome do Devedor:")
        if st.form_submit_button("Salvar Devedor", type="primary"):
            if nome:
                conn = sqlite3.connect('cashflow.db')
                conn.execute('INSERT INTO devedores (nome) VALUES (?)', (nome.upper(),))
                conn.commit()
                conn.close()
                st.rerun()

    st.divider()
    st.markdown(txt_ajuda_edicao)
    conn = sqlite3.connect('cashflow.db')
    df_dev = pd.read_sql_query("SELECT * FROM devedores ORDER BY id ASC", conn)
    conn.close()
    df_dev.insert(0, "Excluir", False)
    edited_dev = st.data_editor(df_dev, num_rows="dynamic", hide_index=True, use_container_width=True, column_config={"id": None, "Excluir": st.column_config.CheckboxColumn("Excluir")})
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("💾 Salvar Edições", type="primary", use_container_width=True):
            atualizar_bd_tabela("devedores", edited_dev); st.rerun()
    with col_btn2:
        if st.button("🗑️ Excluir", use_container_width=True):
            if excluir_registos("devedores", edited_dev): st.rerun()