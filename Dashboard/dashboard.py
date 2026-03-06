import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuração da página
st.set_page_config(page_title="Data Explorer Pro", page_icon="📊", layout="wide")

st.title("📊 Dashboard Dinâmico de Dados")
st.markdown(
    "Analise seus dados de forma interativa. Ideal para datasets estruturados, ensaios de robótica ou logs de sensores.")

# 1. Gerenciamento de Arquivos
DATA_FOLDER = "data"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(('.csv', '.xlsx'))]

if not files:
    st.warning(f"Nenhum arquivo encontrado na pasta '{DATA_FOLDER}'. Adicione um CSV ou Excel para começar.")
else:
    # Sidebar - Seleção de Arquivo
    st.sidebar.header("📂 Seleção de Dados")
    selected_file = st.sidebar.selectbox("Selecione o arquivo", files)
    file_path = os.path.join(DATA_FOLDER, selected_file)


    # Carregamento de dados com cache e tratamento de erros
    @st.cache_data
    def load_data(path):
        try:
            if path.endswith('.csv'):
                return pd.read_csv(path)
            return pd.read_excel(path)
        except Exception as e:
            return str(e)


    df_raw = load_data(file_path)

    if isinstance(df_raw, str):
        st.error(f"Erro ao ler o arquivo: {df_raw}")
    else:
        df = df_raw.copy()
        columns = df.columns.tolist()

        # 2. Multi Filtros Laterais Dinâmicos
        st.sidebar.header("🔍 Filtros de Dados")

        filter_cols = st.sidebar.multiselect("Filtrar por quais colunas?", columns)

        # Aplica cada filtro escolhido em cascata
        for col in filter_cols:
            st.sidebar.markdown(f"**Filtro: {col}**")
            if pd.api.types.is_numeric_dtype(df[col]):
                min_val = float(df[col].min())
                max_val = float(df[col].max())

                if min_val == max_val:
                    st.sidebar.info(f"Valor único: {min_val}")
                else:
                    selected_range = st.sidebar.slider(
                        f"Intervalo",
                        min_value=min_val,
                        max_value=max_val,
                        value=(min_val, max_val),
                        key=f"slider_{col}"
                    )
                    df = df[(df[col] >= selected_range[0]) & (df[col] <= selected_range[1])]
            else:
                unique_vals = df[col].dropna().unique()
                selected_vals = st.sidebar.multiselect(
                    f"Valores",
                    options=unique_vals,
                    default=unique_vals,
                    key=f"multi_{col}"
                )
                df = df[df[col].isin(selected_vals)]

            st.sidebar.divider()

            # Botão de Exportação na Sidebar
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.sidebar.download_button(
            label="📥 Baixar Dados Filtrados (CSV)",
            data=csv_data,
            file_name=f"filtrado_{selected_file}",
            mime="text/csv"
        )

        # 3. Layout Principal - Configuração e Visualização
        col1, col2 = st.columns([1, 3])

        with col1:
            st.subheader("⚙️ Configuração do Gráfico")
            chart_type = st.radio("Tipo de Gráfico", ["Linha", "Barras", "Dispersão", "Histograma"])

            x_axis = st.selectbox("Eixo X", columns)

            if chart_type != "Histograma":
                # Usando multiselect para permitir várias colunas no eixo Y
                default_y = [columns[1]] if len(columns) > 1 else [columns[0]]
                y_axis = st.multiselect("Eixo Y", columns, default=default_y)
            else:
                y_axis = None

            custom_title = st.text_input("Título Customizado", f"Análise de {chart_type}")
            show_table = st.checkbox("Mostrar Tabela de Dados", value=True)

        with col2:
            st.subheader("Visualização")

            # Verificação de segurança: não tenta plotar se não houver eixo Y selecionado (exceto histograma)
            if chart_type != "Histograma" and not y_axis:
                st.warning("⚠️ Por favor, selecione pelo menos uma coluna para o Eixo Y.")
            else:
                # Geração dinâmica dos gráficos Plotly com múltiplas variáveis em Y
                if chart_type == "Linha":
                    fig = px.line(df, x=x_axis, y=y_axis, title=custom_title, template="plotly_dark")
                elif chart_type == "Barras":
                    # barmode='group' coloca as barras lado a lado. Se preferir empilhadas, remova esse parâmetro.
                    fig = px.bar(df, x=x_axis, y=y_axis, title=custom_title, template="plotly_dark", barmode='group')
                elif chart_type == "Dispersão":
                    fig = px.scatter(df, x=x_axis, y=y_axis, title=custom_title, template="plotly_dark")
                else:
                    fig = px.histogram(df, x=x_axis, title=custom_title, template="plotly_dark")

                st.plotly_chart(fig, use_container_width=True)

        # 4. Preview de Dados
        if show_table:
            st.divider()
            st.write("### 🗂️ Prévia dos Dados (Filtrados)")
            st.dataframe(df.head(15), use_container_width=True)