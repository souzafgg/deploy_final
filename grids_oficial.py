import pandas as pd
import streamlit as st
import plotly.express as px
import asyncio
import plotly.graph_objects as go
from api import token, main
from read_data import to_excel, convert_csv, ler_arquivo
from st_aggrid import AgGrid, GridUpdateMode, DataReturnMode
from st_aggrid.grid_options_builder import GridOptionsBuilder
from streamlit_option_menu import option_menu

if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'collapsed'

st.set_page_config(page_title="DASHBOARD NLT",
                   page_icon=":bar_chart:",
                   layout="wide",
                   initial_sidebar_state=st.session_state.sidebar_state)
                

# ---------------- login -------------------

file = ler_arquivo(nome_df="mostrar_pai.csv")


update_mode_value = GridUpdateMode.__members__["GRID_CHANGED"]
return_mode_value = DataReturnMode.__members__["FILTERED"]
col_direita, col_esquerda, col_extrema = st.columns(3)
gd = GridOptionsBuilder.from_dataframe(file)
gd.configure_pagination(enabled=True)
gd.configure_default_column(editable=True, groupable=True, resizable=True)
gd_options = gd.build()


st.sidebar.header("Seja Bem vindo")
pagina = option_menu(menu_title=None, 
                options=["Dashboards", "Requisições API", "Contato"],
                default_index=0, 
                orientation="horizontal",
                icons=["bar-chart-line-fill", "clipboard-data", "envelope"],
                styles={
                "container": {"padding": "0!important", "background-color": "#422B6A"},
                "icon": {"color": "orange", "font-size": "25px"},
                "nav-link": {
                    "font-size": "25px",
                    "text-align": "left",
                    "margin": "2px",
                    "--hover-color": "#7E65A9",
                },
                "nav-link-selected": {"background-color": "#87B021"},
            })

st.markdown("---")

# ------- configurando arquivos -------------
tab_porta = pd.pivot_table(file, index="Porta",
                           aggfunc="count")[["DevEUI"]]

geral = pd.DataFrame(index=["Total"], columns=[
    "DevEUI"], data=len(file["DevEUI"]))
ativ = pd.pivot_table(file, aggfunc="count",
                      index=["Atividade"])[["DevEUI"]]
status = pd.pivot_table(file, aggfunc="count",
                        index=["Status"])[["DevEUI"]]
multi_index = pd.pivot_table(file, aggfunc="count",
                             index=["Status", "Atividade"])[["DevEUI"]]

multi_novo = multi_index.reset_index(level=[0, 1])
multi_novo["Misto"] = multi_novo["Status"] + ", " + multi_novo["Atividade"]
final = multi_novo.set_index("Misto")[["DevEUI"]]

tudo = pd.concat([geral, ativ, status])


teste = file.groupby(by=["Atividade"]).count()[["DevEUI"]]
teste1 = file.groupby(by=["Status"]).count()[["DevEUI"]]
teste2 = file.groupby(by=["Porta"]).count()[["DevEUI"]]
mesclado = pd.pivot_table(file, aggfunc="count",
                        index=["Status", "Atividade"])

copia_porta = teste2.reset_index()
copia_atividade = teste.reset_index()
copia_status = teste1.reset_index()
copia_mesclado = mesclado.reset_index().drop(columns=["Porta"])

if pagina == "Requisições API":
    
    if "botao_login" not in st.session_state:
        st.session_state.botao_login = False
    
    if "botao_api" not in st.session_state:
        st.session_state.botao_api = False

    form_login = st.form(key="login")
    email = form_login.text_input("Digite seu email para acessar a API: ")
    senha = form_login.text_input("Digite sua senha: ")
    confirmar = form_login.form_submit_button("Clique aqui para confimar seu login: ")
    if confirmar:
        st.session_state.botao_login = True
    if st.session_state.botao_login:
        tokn, resp = token(email, senha)
        if "200" in str(resp):

            update_mode_value_d = GridUpdateMode.__members__["GRID_CHANGED"]
            return_mode_value_d = DataReturnMode.__members__["FILTERED"]
            gd_dash = GridOptionsBuilder.from_dataframe(file)
            gd_dash.configure_pagination(enabled=True)
            gd_dash.configure_default_column(editable=True, groupable=True, resizable=True)
            sel_mode_d = st.radio("Tipo de seleção", options=["single", "multiple"])
            gd_dash.configure_selection(selection_mode=sel_mode_d, use_checkbox=True)
            gd_dash_options = gd_dash.build()

            tabel_pagina = AgGrid(file, height=500, width=500, gridOptions=gd_dash_options,
                                theme="streamlit", fit_columns_on_grid_load=True, update_mode=GridUpdateMode.SELECTION_CHANGED)

            sel_rows = tabel_pagina["selected_rows"]
            selecionado = pd.DataFrame(sel_rows)
            try:
                selecionado.drop(columns=selecionado.columns[0], inplace=True)
            except:
                pass

            form1 = st.form(key="teste")
            confirmar_analise = form1.form_submit_button("Clique aqui para confirmar")
            if confirmar_analise:
                st.session_state.botao_api = True
            if st.session_state.botao_api:
                planilha = asyncio.run(main(arq_orig=selecionado,
                            token=tokn, login=email, password=senha))
                arquivo_novo_excel = convert_csv(planilha)

                st.download_button(label="Download arquivo xlsx :bar_chart:",
                                data=arquivo_novo_excel, file_name="analise_nlt_nova.csv")
                st.session_state.botao_api = False
            


if pagina == "Dashboards":

    st.header("Métricas gerais da análise")
    cm1, cm2, cm3, cm4, cm5 = st.columns(5)
    with open("metrics.css") as estilo:
        st.markdown(f"<style>{estilo.read()}</style>", unsafe_allow_html=True)
        
    cm1.metric(label="Total", value=geral.loc["Total"])
    cm2.metric(label="Na NLT", value=status.loc["Na NLT"])
    cm3.metric(label="Fora da NLT", value=status.loc["Fora da NLT"])
    cm4.metric(label="Ativos", value=ativ.loc["Ativo"])
    cm5.metric(label="Inativos", value=ativ.loc["Não ativo"])


    teste.loc["Total"] = teste["DevEUI"].sum()
    teste["%"] = round(((teste["DevEUI"] / teste.loc["Total", "DevEUI"]) * 100), 2)

    with st.expander("Vizualizar dashboards das métricas gerais"):
        col_g1, col_g2 = st.columns(2)
        # met_geral = px.pie(tudo, values="DevEUI", names=tudo.index, title="Vizualização geral das métricas", hole=.2,
        # template="plotly_dark", color_discrete_sequence=px.colors.sequential.RdBu)
        pie = go.Figure(data=[go.Pie(labels=tudo.index,
                                    values=tudo["DevEUI"], hole=.2)])

        pie.update_traces(hoverinfo="label+percent", textfont_size=18, textinfo="value",
                        marker=dict(colors=px.colors.sequential.RdBu, line=dict(width=1)))
        pie.update_layout(title=dict(text="Teste", x=0.5, y=0.9, xanchor="center", yanchor="top"))

        # multi_index_chart = px.bar(final, x=final.index, y="DevEUI", color="DevEUI",
        # color_continuous_scale=px.colors.sequential.YlOrBr, text_auto=True)

        barras = go.Figure(data=[go.Bar(x=final.index, y=final["DevEUI"],
                                        text=final["DevEUI"], textposition="auto", hovertext=final["DevEUI"])])
        # met_geral.update_traces(hoverinfo="label+percent",textinfo="value + percent", textfont_size=18, textposition="inside")
        barras.update_traces(marker_color=px.colors.sequential.RdBu)
        barras.update_layout(xaxis_title="Localização", xaxis_tickangle=0, width=750, height=525,
                            xaxis_tickfont_size=15, yaxis_tickfont_size=15)

        col_g1.plotly_chart(pie)
        col_g2.plotly_chart(barras)

    st.markdown("---")
    st.title(":bar_chart: Dashboard NLT")


    # -------- configurando grids ------------
    col_direita, col_esquerda = st.columns(2)
    atividade_col, mesc = st.columns(2)


    try:
        with col_direita:
            tabel = AgGrid(file, height=500, width=500, update_mode=update_mode_value, gridOptions=gd_options, theme="streamlit",
                        allow_unsafe_jscode=True, reload_data=False, key="grid1", data_return_mode=return_mode_value, fit_columns_on_grid_load=True)
        # ----------grid atividade--------------
        grid_filt_atividade = tabel.data.groupby(
            by=["Atividade"]).count()[["DevEUI"]]

        grid_filt_atividade.loc["Total"] = grid_filt_atividade["DevEUI"].sum()


        grid_filt_atividade["%"] = round(
            ((grid_filt_atividade["DevEUI"] / grid_filt_atividade.loc["Total", "DevEUI"]) * 100), 2)

        grid_filt_atividade.reset_index(drop=False, inplace=True)

        # ----------grid porta--------------

        grid_filt_porta = tabel.data.groupby(
            by=["Porta"]).count()[["DevEUI"]].reset_index(drop=False)

        # ----------grid porta--------------

        grid_filt_status = tabel.data.groupby(by=["Status"]).count()[
            ["DevEUI"]].reset_index()
        # geral table de porta em cima da atualizada
        with col_esquerda:
            tabel_porta = AgGrid(grid_filt_porta, key="grid3", editable=False, theme="streamlit", reload_data=True,
                                gridOptions=gd.configure_auto_height(autoHeight=True), fit_columns_on_grid_load=True)
            tabel_porta.data.set_index("Porta", drop=False, inplace=True)
            tabel_porta.data.sort_values(by="DevEUI", inplace=True, ascending=True)

            tabel_status = AgGrid(grid_filt_status, key="gid5", editable=False,
                                height=100, theme="streamlit", reload_data=True, fit_columns_on_grid_load=True)
            

            fig_porta = px.bar(tabel_porta.data, x="DevEUI", y=list(map(str, tabel_porta.data.index)), template="plotly_dark", color="DevEUI", title="DevEUI POR PORTAS",
                            color_continuous_scale=px.colors.sequential.OrRd)

            fig_porta.update_layout(yaxis_title="N° da porta", xaxis=dict(showgrid=True, tickfont=dict(size=15), titlefont=dict(size=18)),
                                    yaxis=dict(tickfont=dict(size=15), titlefont=dict(size=18)))

        with mesc:
            grid_filt_mesclado = tabel.data.pivot_table(tabel.data, aggfunc="count",
                                                        index=["Status", "Atividade"]).reset_index().drop(columns=["Porta"])

            tabel_mesclado = AgGrid(grid_filt_mesclado, key="grid5", editable=False,
                                    height=120, theme="streamlit", reload_data=True,
                                    gridOptions=gd.configure_auto_height(autoHeight=True), fit_columns_on_grid_load=True)
        with atividade_col:
            tabel_atividade = AgGrid(grid_filt_atividade, key="grid4",
                                    editable=False, height=120, gridOptions=gd.configure_auto_height(autoHeight=True), theme="streamlit", reload_data=True, fit_columns_on_grid_load=True)
                                    
            tabel_atividade.data.set_index("Atividade", inplace=True)

            fig_atividade = px.bar(tabel_atividade.data, x=tabel_atividade.data.index, y="DevEUI", labels=["Teste"],
                                template="plotly", title="ATIVIDADE DOS DEVEUI'S", color="DevEUI", color_continuous_scale=px.colors.sequential.RdBu)
            
            fig_atividade.update_layout(legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ))

            tabel_status.data.set_index("Status", inplace=True)
            fig_local = px.bar(tabel_status.data, x=tabel_status.data.index, y="DevEUI",
                            template="plotly_dark", title="LOCAL DOS DEVEUI'S", color="DevEUI", color_continuous_scale=px.colors.sequential.RdBu)

        sel_linha = tabel["selected_rows"]
        st.write(sel_linha)
        novo, novo1 = st.columns(2)
        novo.plotly_chart(fig_atividade, use_container_width=True)
        novo1.plotly_chart(fig_local, use_container_width=True)
        st.plotly_chart(fig_porta, use_container_width=True)
    except:
        st.error("Não há DevEUIs' selecionados")

    # material, balham, streamlit, alpine

        st.subheader("Downloads:")

        arquivo = to_excel(file)
        arquivo1 = convert_csv(file)
        excel = st.download_button(label="Download arquivo xlsx :bar_chart:",
                                data=arquivo, file_name="analise_nlt.xlsx")
        csv = st.download_button(
            label="Download arquivo csv :bar_chart:",
            data=arquivo1,
            file_name='large_df.csv',
            mime='text/csv',
        )


        hide_st_style = """
                    <style>
                    #MainMenu {visibility: hidden;}
                    footer {visibility: hidden;}
                    header {visibility: hidden;}
                    </style>
                    """

        # st.markdown(hide_st_style, unsafe_allow_html=True)
