import streamlit as st
import pandas as pd

st.set_page_config(page_title='Finanças', page_icon=':moneybag:')

st.markdown("""
# Boas Vindas!
            
## Nosso APP  Financeiro!
            
Espero que você curta a experiencia da nossa solução financeira
            
""")
#Widget de upload de arquivo
file_upload = st.file_uploader("Faça o upload dos dados aqui", type=["csv"])

#Verifica se algum arquivo foi enviado
if file_upload:

    # Leitura dos dados
    df = pd.read_csv(file_upload)
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y').dt.date

    #Exibição dos dados
    exp1 = st.expander("Dados Brutos")
    columns_fmt = {'Valor': st.column_config.NumberColumn("Valor", format="R$ %.2f")}
    exp1.dataframe(df, hide_index=True, column_config=columns_fmt)

    #Visualização dos dados por instituição
    exp2 = st.expander("Dados por Instituição")
    df_instituicao = df.pivot_table(index='Data', columns='Instituição', values='Valor')
  
    tab_data, tab_history, tb_share = exp2.tabs(["Dados", "Histórico", "Compartilhar"])

    with tab_data:
        st.dataframe(df_instituicao)

    with tab_history:
        st.line_chart(df_instituicao)

    with tb_share:

        date = st.selectbox("Filtro Data", options=df_instituicao.index)
        st.bar_chart(df_instituicao.loc[date])
