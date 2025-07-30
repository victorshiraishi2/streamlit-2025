#%%
import streamlit as st
import pandas as pd
import requests
import datetime

@st.cache_data(ttl="1day")
def get_selic():
    """
    Fetches the historical Selic interest rates from the Banco Central do Brasil API and returns them as a pandas DataFrame.

    Returns:
        pd.DataFrame: DataFrame containing Selic rate history with start and end dates.
    """
    url = "https://www.bcb.gov.br/api/servico/sitebcb/historicotaxasjuros"
    response = requests.get(url)
    df = pd.DataFrame(response.json()["conteudo"])

    df["DataInicioVigencia"] = pd.to_datetime(df["DataInicioVigencia"]).dt.date
    df["DataFimVigencia"] = pd.to_datetime(df["DataFimVigencia"]).dt.date
    df["DataFimVigencia"] = df["DataFimVigencia"].fillna(datetime.datetime.today().date())
    return df

def calc_general_stats(df):
    df_data = df.groupby(by='Data')[['Valor']].sum()
    df_data['lag_1'] = df_data['Valor'].shift(1)
    df_data['Diferença'] = df_data['Valor'] - df_data['lag_1']
    df_data['Média 6M diferença mensal'] = df_data['Diferença'].rolling(6).mean()
    df_data['Média 12M diferença mensal'] = df_data['Diferença'].rolling(12).mean()
    df_data['Média 24M diferença mensal'] = df_data['Diferença'].rolling(24).mean()

    df_data['Diferença mensal Rel.'] = df_data["Valor"] / df_data['lag_1'] - 1

    df_data['Evolução 6M Total'] = df_data['Valor'].rolling(6).apply(lambda x: (x[-1] - x[0])) 
    df_data['Evolução 12M Total'] = df_data['Valor'].rolling(12).apply(lambda x: (x[-1] - x[0]))
    df_data['Evolução 24M Total'] = df_data['Valor'].rolling(24).apply(lambda x: (x[-1] - x[0]))

    df_data['Evolução 6M Relativa'] = df_data['Valor'].rolling(6).apply(lambda x: (x[-1] - x[0]) -1) 
    df_data['Evolução 12M Relativa'] = df_data['Valor'].rolling(12).apply(lambda x: (x[-1] - x[0]) -1)
    df_data['Evolução 24M Relativa'] = df_data['Valor'].rolling(24).apply(lambda x: (x[-1] - x[0]) -1)

    df_data = df_data.drop(columns=['lag_1'], axis=1)

    return df_data

def main_metas():
    col1, col2 = st.columns(2)

    data_inicio_meta = col1.date_input("Data de Início da Meta", max_value=df_stats.index.max())
    data_filtrada = df_stats.index[df_stats.index <= data_inicio_meta][-1]


    custos_fixos = col1.number_input('Custos Fixos', min_value=0.0, format="%.2f")

    salario_bruto = col2.number_input('Salário Bruto', min_value=0.0, format="%.2f")
    salario_liquido = col2.number_input('Salário Líquido', min_value=0.0, format="%.2f")

    valor_inicio = df_stats.loc[data_filtrada]["Valor"]
    col1.markdown("**Valor no Início da Meta:** R$ {:.2f}".format(valor_inicio))

    selic_gov = get_selic()
    filter_selic_date = (selic_gov["DataInicioVigencia"] < data_inicio_meta) & (selic_gov["DataFimVigencia"] > data_inicio_meta)
    selic_default = selic_gov[filter_selic_date]['MetaSelic'].iloc[0]

    selic = st.number_input("Selic", min_value=0.0,value=selic_default, format="%.2f")
    selic_ano = selic / 100
    selic_mes = (selic_ano + 1) ** (1/12) - 1

    st.text(f"Selic ano: {100*selic_ano:.2f}%")
    st.text(f"Selic mês: {100*selic_mes:.2f}%")

    rendimento_ano = valor_inicio * selic_ano
    rendimento_mes = valor_inicio * selic_mes

    col1_pot,col2_pot = st.columns(2)
    mensal = salario_liquido - custos_fixos + rendimento_mes
    anual = 12*(salario_liquido - custos_fixos) + rendimento_ano


    with col1_pot.container(border=True):
        st.markdown(f"**Potencial Arrecadação Anual:** R$ {anual:.2f}", help=f"{salario_liquido} - {custos_fixos} + {rendimento_ano:.2f}")

    with col2_pot.container(border=True):
        st.markdown(f"**Potencial Arrecadação Mês:** R$ {mensal:.2f}", help=f"12 * {salario_liquido} - {custos_fixos} + {rendimento_mes:.2f}")

    with st.container(border=True):
        col1_meta, col2_meta = st.columns(2)
        with col1_meta:
            meta_estipulada = st.number_input("Meta Estipulada", min_value=-99999., format="%.2f", value=mensal)

        with col2_meta:
            patrimonio_final = meta_estipulada + valor_inicio
            st.markdown(f"Patrimonio Estimado por meta \n\n R$ {patrimonio_final:.2f}")

    return data_inicio_meta, meta_estipulada, patrimonio_final

st.set_page_config(page_title='Finanças', page_icon=':moneybag:')

st.markdown("""
# Boas Vindas!
            
## Nosso APP  Financeiro!
            
Espero que você curta a experiencia da nossa solução financeira
            
""")
#Widget de upload de arquivo
file_upload = st.file_uploader("Faça o upload dos dados aqui", type=["csv"])

# Usar arquivo padrão se nenhum for enviado
if file_upload is None:
    try:
        df = pd.read_csv("dados_exemplo.csv")
        st.info("📊 Usando dados de exemplo. Faça upload do seu arquivo para usar seus dados.")
    except FileNotFoundError:
        st.error("Arquivo de exemplo não encontrado. Por favor, faça upload de um arquivo CSV.")
        df = None
else:
    df = pd.read_csv(file_upload)

#Verifica se há dados para processar
if df is not None:
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y').dt.date

    #Exibição dos dados
    exp1 = st.expander("Dados Brutos")
    columns_fmt = {'Valor': st.column_config.NumberColumn("Valor", format="R$ %.2f")}
    exp1.dataframe(df, hide_index=True, column_config=columns_fmt)

    #Visualização dos dados por instituição
    exp2 = st.expander("Dados por Instituição")
    df_instituicao = df.pivot_table(index='Data', columns='Instituição', values='Valor')
    
    #Abas para visualização dos dados
    tab_data, tab_history, tb_share = exp2.tabs(["Dados", "Histórico", "Compartilhar"])

    #Exibir dataframe
    with tab_data:
        st.dataframe(df_instituicao)

    #Exibir histórico de dados
    with tab_history:
        st.line_chart(df_instituicao)

    #Exibir distribuição
    with tb_share:

        #Filtro de data
        date = st.selectbox("Filtro Data", options=df_instituicao.index)

        #Grafico de distribuicao
        st.bar_chart(df_instituicao.loc[date])

    
    exp3 = st.expander("Estatísticas Gerais")

    df_stats = calc_general_stats(df)
    columns_config = {
         
        'Diferença' : st.column_config.NumberColumn("Diferenca", format="R$ %.2f"),
        'Média 6M diferença mensal' : st.column_config.NumberColumn("Média 6M Diferença Mensal", format="R$ %.2f"),
        'Média 12M diferença mensal' : st.column_config.NumberColumn("Média 12M Diferença Mensal", format="R$ %.2f"),
        'Média 24M diferença mensal' : st.column_config.NumberColumn("Média 24M Diferença Mensal", format="R$ %.2f"),
        'Diferença mensal Rel.' : st.column_config.NumberColumn("Diferença Mensal Relativa", format="percent"),

        'Evolução 6M Total' : st.column_config.NumberColumn("Evolução 6M Total", format="R$ %.2f"),
        'Evolução 12M Total' : st.column_config.NumberColumn("Evolução 12M Total", format="R$ %.2f"),
        'Evolução 24M Total' : st.column_config.NumberColumn("Evolução 24M Total", format="R$ %.2f"),

        'Evolução 6M Relativa' : st.column_config.NumberColumn("Evolução 6M Relativa", format="percent"),
        'Evolução 12M Relativa' : st.column_config.NumberColumn("Evolução 12M Relativa", format="percent"),
        'Evolução 24M Relativa' : st.column_config.NumberColumn("Evolução 24M Relativa", format="percent")
    }

    tab_stats, tab_abs, tab_rel = exp3.tabs(tabs=['Dados', "Histórico de Evolução", "Crescimento Relativo"])

    with tab_stats:
        st.dataframe(df_stats, column_config=columns_config)

    with tab_abs:
        abs_cols = [
            'Diferença',
            'Média 6M diferença mensal',
            'Média 12M diferença mensal',
            'Média 24M diferença mensal',
        ]
        st.line_chart(df_stats[abs_cols])
    
    with tab_rel:
        rel_cols = [
            'Diferença mensal Rel.',
            'Evolução 6M Relativa',
            'Evolução 12M Relativa',
            'Evolução 24M Relativa'
        ]
        st.line_chart(data=df_stats[rel_cols])

    with st.expander('Metas'):

        tab_main,tab_data_meta, tab_graph = st.tabs(tabs=["Configuração", "Dados", "Gráficos"])
        
        with tab_main:
            data_inicio_meta, meta_estipulada, patrimonio_final = main_metas()

        with tab_data_meta:
            meses = pd.DataFrame({
                "Data Referência" : [data_inicio_meta + pd.DateOffset(months=i) for i in range(1, 13)],
                "Meta Mensal": [round(meta_estipulada,2) * i for i in range(1, 13)],
                })
            
            meses["Data Referência"] = meses["Data Referência"].dt.strftime('%Y-%m')
            df_patrimonio = df_stats.reset_index()[["Data", "Valor"]]
            df_patrimonio["Data Referência"] = pd.to_datetime(df_patrimonio["Data"]).dt.strftime('%Y-%m')
            meses = meses.merge(df_patrimonio,how= "left", on="Data Referência")

            meses = meses[["Data Referência","Meta Mensal", "Valor"]]
            meses["Atingimento (%)"] = meses["Valor"] / meses["Meta Mensal"]
            meses["Atingimento Ano"] = meses["Valor"] / patrimonio_final
            meses["Atingimento Esperado"] = meses["Meta Mensal"] / patrimonio_final
            meses.set_index("Data Referência")

            columns_config_meses = {
                "Meta Mensal": st.column_config.NumberColumn("Meta Mensal", format="R$ %.2f"),
                "Valor": st.column_config.NumberColumn("Valor Atingido", format="R$ %.2f"),
                "Atingimento (%)": st.column_config.NumberColumn("Atingimento (%)", format="percent"),
                "Atingimento Ano": st.column_config.NumberColumn("Atingimento Ano", format="percent"),
                "Atingimento Esperado": st.column_config.NumberColumn("Atingimento Esperado", format="percent")
            }

            st.dataframe(meses, column_config=columns_config_meses)

        with tab_graph:
            st.line_chart(meses[["Atingimento Ano", "Atingimento Esperado"]])

