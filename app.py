"""Agile Scrum Sprint Intelligence | Painel analítico público de sprints.

Fonte ÚNICA: MySQL analise_agil. 100% SELECT; nenhuma geração de dados sintéticos.
"""
from __future__ import annotations

import html
import os
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from analytics import auto_insights, pearson_by_project, project_summary, scope_buckets, significance_phrase
from data_layer import filter_status_data, get_mysql_data, prepare_sprints

st.set_page_config(
    page_title="Agile Scrum | Sprint Intelligence",
    page_icon="⚡", layout="wide", initial_sidebar_state="expanded",
)

INK = "#E8F0FF"
MUTED = "#96A9C3"
ACCENT = "#69E4C6"
BLUE = "#638BFF"
PINK = "#CC8DFF"
AMBER = "#FFC677"
RED = "#FB8F9B"
PROJECT_COLORS = {
    "Aurora": "#638BFF", "Meso": "#FFC677", "Spring_XD": "#69E4C6", "UserGrid": "#C39CFF"
}
PALETTE = [BLUE, ACCENT, PINK, AMBER, RED, "#74C9FF"]

st.markdown("""
<style>
:root {--bg:#080F1E; --panel:#101C31; --stroke:#25354E; --fg:#ECF2FF; --sub:#A7B6CC;}
html,body,[class*="css"] {font-family:Inter,'Segoe UI',system-ui,sans-serif;}
.stApp {background:radial-gradient(ellipse at 92% 0%,rgba(55,75,137,.24),transparent 38%), #080F1E;color:var(--fg)}
[data-testid="stHeader"]{background:transparent}
.block-container {padding-top:1.3rem;padding-bottom:3.0rem;max-width:1650px;}
[data-testid="stSidebar"] {background:#0D182A!important;border-right:1px solid #243450;}
[data-testid="stSidebar"] * {color:#E0E9F8;}
[data-testid="stSidebar"] .stButton button {background:linear-gradient(125deg,#5575E9,#6E91FE);color:white!important;border:0;border-radius:10px;font-weight:700;}
h1,h2,h3 {color:#F0F5FF!important;letter-spacing:-.03em!important;}
h1 {font-weight:820!important;}
h3 {font-weight:720!important;}
p,li {color:#C5D1E4;}
[data-testid="stTabs"] button {color:#9EB1CC!important;font-weight:650!important;font-size:.92rem;}
[data-testid="stTabs"] button[aria-selected="true"] {color:#80F0D0!important;}
[data-testid="stTabContent"] {padding-top:.65rem;}
[data-testid="stMetric"] {background:#111E33;border:1px solid #2A3A52;border-radius:15px;padding:12px 15px;}
[data-testid="stMetricLabel"] {color:#B3C2DA!important;}
[data-testid="stMetricValue"] {color:#F1F6FF!important;}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:17px!important;border-color:#273751!important;background:rgba(16,27,48,.80);}
[data-testid="stPlotlyChart"] {border:1px solid #25364F;background:#0F1A2D;border-radius:15px;padding:4px 6px;}
[data-testid="stDataFrame"] {border:1px solid #2B3B55;border-radius:12px;overflow:hidden;}
.stAlert {border-radius:12px;}
[data-testid="stDownloadButton"] button {border-radius:12px;border:1px solid #5373B7!important;color:#EAF1FF!important;font-weight:650!important;}
[data-testid="stExpander"] {border:1px solid #293951!important;border-radius:13px!important;}
.kicker {font-size:.72rem;font-weight:800;letter-spacing:.15em;color:#74E5C7;text-transform:uppercase;}
.hero {position:relative;isolation:isolate;overflow:hidden;border:1px solid #304B69;border-radius:22px;padding:30px 34px 27px;
 background:radial-gradient(ellipse at 92% 15%,rgba(64,149,194,.20),transparent 34%),linear-gradient(128deg,#132B49,#16223B 63%,#20254A);margin-bottom:21px;}
.hero:after {content:'';position:absolute;width:330px;height:330px;right:-110px;top:-165px;border-radius:50%;border:1px solid rgba(120,224,214,.28);box-shadow:0 0 0 47px rgba(120,224,214,.025),0 0 0 95px rgba(120,224,214,.022);z-index:-1;}
.hero h1{font-size:2.48rem!important;line-height:1.14;margin:7px 0 11px!important;color:#F3F8FF!important;max-width:860px;}
.hero p{font-size:.97rem;color:#BACCE2;max-width:750px;margin:0 0 16px;}
.live-pill {display:inline-block;font-size:.72rem;font-weight:750;color:#9AF5D5;background:#183F47;border:1px solid #386965;border-radius:100px;padding:6px 11px;letter-spacing:.035em;}
.micro {font-size:.76rem;color:#9EB1CB;}
.metric-card {min-height:124px;background:linear-gradient(153deg,#13223B,#0E1B30);border:1px solid #2B3E59;border-radius:17px;padding:16px 17px;margin-bottom:11px;box-shadow:0 6px 24px rgba(0,0,0,.11)}
.metric-card .tag{font-size:.77rem;font-weight:650;color:#A9BBD3;min-height:32px;line-height:1.3;}
.metric-card .value{font-size:1.95rem;font-weight:830;letter-spacing:-.047em;color:#F6F9FF;line-height:1.2;}
.metric-card .foot{font-size:.68rem;color:#74DCC3;margin-top:8px;}
.panel-title {font-size:1.15rem;font-weight:750;color:#F0F6FF;margin-top:14px;margin-bottom:4px;}
.panel-note {font-size:.79rem;color:#95A9C6;margin-bottom:10px;}
.insight {border:1px solid #30445E;border-left:3px solid #67DCBC;border-radius:13px;background:#12223A;padding:13px 17px;margin-bottom:10px;}
.insight .overline {font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;color:#94B6D0;font-weight:780;margin-bottom:5px;}
.insight .who {font-size:1.02rem;font-weight:750;color:#EEF7FF;margin-bottom:4px;}
.insight .desc {font-size:.85rem;color:#B7C7D9;line-height:1.5;}
.separator {border-top:1px solid #253650;margin:14px 0 18px;}
.mini-banner {background:#142440;border:1px solid #2C4B65;border-radius:12px;padding:12px 16px;font-size:.84rem;color:#BFD3E8;margin:15px 0;}
.section-kicker{color:#77E7C8;font-weight:750;font-size:.76rem;text-transform:uppercase;letter-spacing:.12em;margin-top:12px;}
@media(max-width:900px){.hero h1{font-size:1.84rem!important}.hero{padding:22px 19px}.metric-card{min-height:105px}}
</style>
""", unsafe_allow_html=True)


def esc(s: object) -> str:
    return html.escape(str(s), quote=True)


def number(v: object, decimals: int = 0, suffix: str = "") -> str:
    try:
        v = float(v)
        if not np.isfinite(v):
            return "—"
        s = f"{v:,.{decimals}f}"
        return s.replace(",", "_").replace(".", ",").replace("_", ".") + suffix
    except (ValueError, TypeError):
        return "—"


def metric(title: str, value: str, note: str = "") -> None:
    st.markdown(f"""
    <div class='metric-card'>
      <div class='tag'>{esc(title)}</div><div class='value'>{esc(value)}</div>
      <div class='foot'>{esc(note)}</div>
    </div>""", unsafe_allow_html=True)


def section(title: str, desc: str = "") -> None:
    st.markdown(f"<div class='panel-title'>{esc(title)}</div>" +
                (f"<div class='panel-note'>{esc(desc)}</div>" if desc else ""),
                unsafe_allow_html=True)


def fig_style(fig: go.Figure, height: int = 365, percent: bool = False, legend: bool = True) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=24, r=23, t=29, b=35),
        paper_bgcolor="#0F1A2D", plot_bgcolor="#0F1A2D",
        font=dict(family="Segoe UI, Arial", color="#C0CDE0", size=12),
        colorway=PALETTE,
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.03, x=0, title=None,
                    font=dict(color="#C4D2E7", size=11)),
        hoverlabel=dict(bgcolor="#213753", font_color="#FFFFFF"),
        hovermode="closest",
    )
    fig.update_xaxes(showgrid=False, linecolor="#33445C", zeroline=False, automargin=True,
                     tickfont=dict(color="#ADC0D9"))
    fig.update_yaxes(showgrid=True, gridcolor="#263650", zeroline=False, automargin=True,
                     ticksuffix="%" if percent else "", tickfont=dict(color="#ADC0D9"))
    return fig


def chart(fig: go.Figure, *, height: int = 365, percent: bool = False, legend: bool = True, key: str) -> None:
    st.plotly_chart(fig_style(fig, height, percent, legend), use_container_width=True,
                    config={"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]}, key=key)


def color_for(p: str) -> str:
    return PROJECT_COLORS.get(p, PALETTE[hash(p) % len(PALETTE)])


def add_trend(fig: go.Figure, frame: pd.DataFrame, x: str, y: str) -> None:
    """Regressão visual linear; não extrapola ou realiza inferência causal."""
    for project, group in frame.groupby("projeto"):
        pair = group[[x, y]].dropna()
        if len(pair) < 3 or pair[x].nunique() <= 1:
            continue
        xx = pair[x].to_numpy(dtype=float)
        yy = pair[y].to_numpy(dtype=float)
        if np.unique(yy).size <= 1:
            continue
        slope, intercept = np.polyfit(xx, yy, deg=1)
        path = np.array([xx.min(), xx.max()])
        fig.add_trace(go.Scatter(x=path, y=slope * path + intercept,
                                 mode="lines", name=f"Tendência · {project}",
                                 line=dict(color=color_for(project), dash="dot", width=2),
                                 hoverinfo="skip", showlegend=False))


def correlations_cards(stats: pd.DataFrame, heading: str, prefix: str) -> None:
    section(heading, "Correlação de Pearson por projeto; calculada novamente para o recorte ativo.")
    if stats.empty:
        st.info("Não há sprints suficientes para calcular a correlação.")
        return
    cols = st.columns(min(len(stats), 4))
    for col, row in zip(cols, stats.itertuples(index=False)):
        with col:
            metric(row.projeto, f"{row.r:+.3f}" if pd.notna(row.r) else "—",
                   f"{int(row.sprints)} sprints · {significance_phrase(row.r).lower()}")
    st.caption("Correlação observacional; não é teste de significância nem evidencia causa e efeito.")


def load_secret(name: str, default: str) -> str:
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return default


@st.cache_data(ttl=90, show_spinner="Consultando o MySQL…")
def cached_data(host: str, port: int, user: str, password: str, schema: str,
                ssl_ca_pem: str, ssl_ca_path: str):
    return get_mysql_data(host, port, user, password, schema,
                          ssl_ca_pem=ssl_ca_pem, ssl_ca_path=ssl_ca_path)


# Credenciais ficam exclusivamente no ambiente do servidor, nunca em campos públicos.
host = load_secret("MYSQL_HOST", os.getenv("MYSQL_HOST", "127.0.0.1"))
port = int(load_secret("MYSQL_PORT", os.getenv("MYSQL_PORT", "3306")))
user = load_secret("MYSQL_USER", os.getenv("MYSQL_USER", ""))
password = load_secret("MYSQL_PASSWORD", os.getenv("MYSQL_PASSWORD", ""))
schema = load_secret("MYSQL_DATABASE", os.getenv("MYSQL_DATABASE", "analise_agil"))
ssl_ca_pem = load_secret("MYSQL_SSL_CA_PEM", os.getenv("MYSQL_SSL_CA_PEM", ""))
ssl_ca_path = load_secret("MYSQL_SSL_CA_PATH", os.getenv("MYSQL_SSL_CA_PATH", ""))

with st.sidebar:
    st.markdown("### ◈ **Agile Scrum**")
    st.caption("SPRINT INTELLIGENCE  /  ANALYTICS")
    st.markdown("<div class='separator'></div>", unsafe_allow_html=True)
    st.caption("Base oficial da análise: MySQL · `analise_agil`")
    if st.button("↻  Atualizar indicadores", use_container_width=True):
        cached_data.clear()
        st.rerun()

try:
    if not user or not password:
        raise RuntimeError("Credenciais ausentes na configuração privada do servidor.")
    sources, source_errors = cached_data(host, port, user, password, schema, ssl_ca_pem, ssl_ca_path)
    all_sprints, data_warnings = prepare_sprints(sources)
except Exception as exc:
    st.markdown("<div class='kicker'>Agile Scrum · Fonte de dados</div>", unsafe_allow_html=True)
    st.title("Conexão de dados indisponível")
    st.error("O dashboard não conseguiu carregar os dados do MySQL. Nenhum número fictício será exibido.")
    # Erros detalhados não são exibidos em uma página que poderá ser pública.
    # Diagnóstico completo e seguro para o administrador: python diagnostico_mysql.py
    if not user or not password:
        st.warning("O Streamlit não encontrou MYSQL_USER e/ou MYSQL_PASSWORD. Verifique se o arquivo está salvo como `.streamlit/secrets.toml` na pasta do projeto, não como `.example` ou `.txt`.")
    else:
        try:
            import mysql.connector
            if isinstance(exc, mysql.connector.Error):
                if exc.errno == 1045:
                    st.warning("O MySQL recusou a autenticação. Confira o usuário e a senha definidos no arquivo privado do servidor.")
                elif exc.errno in (2003, 2005):
                    st.warning("O servidor MySQL não foi alcançado. Confira se ele está ativo e se host/porta estão corretos.")
                elif exc.errno in (1049, 1146, 1142, 1356):
                    st.warning("O MySQL foi alcançado, mas existe um problema de acesso ao schema ou a uma view/tabela.")
        except ImportError:
            pass
    st.info("**Como identificar a causa:** abra o terminal do VS Code na pasta do dashboard e execute `py diagnostico_mysql.py`. O teste verifica login, views e dados sem imprimir a senha.")
    st.caption("Views necessárias: vw_indicadores_sprint, vw_conclusao_por_sprint e vw_movimentacao_sprints. Para a publicação, não exiba erros internos aos visitantes.")
    st.stop()

with st.sidebar:
    st.success("Dados consultados no MySQL", icon="✅")
    st.caption(f"Schema: `{schema}` · cache de até 90 s")
    st.divider()
    st.markdown("#### Filtros interativos")
    projects = sorted(all_sprints["projeto"].dropna().unique().tolist())
    selected_projects = st.multiselect("Projetos", projects, default=projects)
    states = sorted(all_sprints["estado"].dropna().unique().tolist())
    selected_states = st.multiselect("Estado da sprint", states, default=states)
    date_col = all_sprints["inicio"].dropna()
    chosen_interval = None
    if not date_col.empty:
        min_date, max_date = date_col.min().date(), date_col.max().date()
        if min_date < max_date:
            chosen_interval = st.date_input(
                "Período de início", value=(min_date, max_date), min_value=min_date, max_value=max_date,
                help="Filtra apenas sprints com data inicial disponível."
            )
    st.divider()
    st.caption("Acesso compartilhável: os visitantes não recebem nem digitam credenciais do banco. Os dados continuam no MySQL.")

selected = all_sprints[
    all_sprints["projeto"].isin(selected_projects) & all_sprints["estado"].isin(selected_states)
].copy()
if chosen_interval is not None and len(chosen_interval) == 2:
    d1, d2 = chosen_interval
    selected = selected[selected["inicio"].dt.date.between(d1, d2)].copy()
if selected.empty:
    st.warning("Nenhuma sprint encontrada para esse conjunto de filtros. Selecione outro projeto, estado ou período.")
    st.stop()

status = filter_status_data(sources.get("status", pd.DataFrame()), selected)
summary = project_summary(selected)
h2 = pearson_by_project(selected, "qtd_desenvolvedores", "tarefas_concluidas")
h3 = pearson_by_project(selected, "alteracoes", "percentual_completed")
buckets = scope_buckets(selected)

n_sprints = len(selected)
n_projects = selected["projeto"].nunique()
total_completed = selected["tarefas_concluidas"].sum(min_count=1)
mean_vel = selected["pontos_concluidos"].mean()
total_changes = selected["alteracoes"].sum(min_count=1)
links = selected["total_vinculos"].sum(min_count=1)
done_links = selected["vinculos_completed"].sum(min_count=1)
weighted_completion = 100 * done_links / links if pd.notna(links) and links > 0 else np.nan

st.markdown(f"""
<div class='hero'>
  <span class='kicker'>Agile Scrum · Sprint Intelligence</span>
  <h1>O desempenho das sprints, em uma visão completa.</h1>
  <p>Entregas, velocidade, conclusão, alterações de escopo e hipóteses H1–H3, com indicadores reais calculados a partir do banco MySQL.</p>
  <span class='live-pill'>● &nbsp; Conectado ao MySQL &nbsp;·&nbsp; {esc(schema)}</span>
  <span style='margin-left:10px' class='micro'>{n_projects} projetos no recorte &nbsp;·&nbsp; indicadores atualizados por consulta</span>
</div>""", unsafe_allow_html=True)

catalog_data = sources.get("catalogo", pd.DataFrame())
link_data = sources.get("historico_vinculos", pd.DataFrame())
def historical_count(table: pd.DataFrame, field: str) -> object:
    if table.empty or not {"projeto", field}.issubset(table.columns):
        return np.nan
    sub = table[table["projeto"].isin(selected_projects)]
    return pd.to_numeric(sub[field], errors="coerce").sum(min_count=1)

catalog_count = historical_count(catalog_data, "tarefas_catalogo")
links_historical = historical_count(link_data, "vinculos_historicos")

cards = st.columns(4)
with cards[0]: metric("Projetos selecionados", number(n_projects), "comparação interativa")
with cards[1]: metric("Sprints no filtro", number(n_sprints), "ciclos originais")
with cards[2]: metric("Entregas", number(total_completed), "concluídas nas sprints")
with cards[3]: metric("Vínculos Completed", number(weighted_completion, 1, "%"), "proporção no filtro")

cards2 = st.columns(4)
with cards2[0]: metric("Tarefas cadastradas", number(catalog_count), "catálogo histórico dos projetos")
with cards2[1]: metric("Vínculos históricos", number(links_historical), "base completa dos projetos")
with cards2[2]: metric("Velocidade média", number(mean_vel, 1), "pontos por sprint* ")
with cards2[3]: metric("Alterações de escopo", number(total_changes), "adicionadas + retiradas")

st.caption("* Story points são estimativas definidas pelas equipes; comparações diretas entre projetos exigem cautela. "
           "'Entregas' soma tarefas concluídas por sprint, podendo contar uma tarefa presente em ciclos diferentes. "
           "Tarefas cadastradas e vínculos históricos respeitam os projetos, mas não o período/estado, pois representam o catálogo integral.")

if data_warnings:
    with st.expander("Avisos de qualidade das fontes"):
        for warning in data_warnings:
            st.warning(warning)
if source_errors:
    with st.expander("Fontes complementares não disponíveis"):
        for k in source_errors:
            st.caption(f"Fonte `{k}` não disponível. Consulte o administrador do banco.")

pages = st.tabs(["✦  Visão executiva", "▥  Sprints e entregas", "◈  Escopo e conclusão",
                 "⌁  Hipóteses H1–H3", "▤  Dados e auditoria"])

# --- Visão executiva -----------------------------------------
with pages[0]:
    st.markdown("<div class='section-kicker'>Comparativo de desempenho entre projetos</div>", unsafe_allow_html=True)
    st.caption("Cada indicador é apresentado separadamente: não existe um índice composto nem uma classificação artificial de equipes.")
    row_a, row_b = st.columns(2, gap="medium")
    with row_a:
        section("Conclusão por projeto", "Proporção de vínculos de tarefas classificados como Completed nas sprints selecionadas.")
        rates = summary.dropna(subset=["taxa_vinculos"]).sort_values("taxa_vinculos", ascending=True)
        if rates.empty:
            st.info("Conclusão não disponível nesta seleção.")
        else:
            fig = px.bar(rates, x="taxa_vinculos", y="projeto", color="projeto", orientation="h",
                         text="taxa_vinculos", color_discrete_map=PROJECT_COLORS,
                         labels={"taxa_vinculos": "Vínculos Completed (%)", "projeto": ""})
            fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside", cliponaxis=False)
            fig.update_xaxes(range=[0, 110])
            chart(fig, height=345, legend=False, key="executive-completion")
    with row_b:
        section("Velocidade média das sprints", "Média dos pontos concluídos por sprint. Story points dependem da escala de cada equipe.")
        v = summary.dropna(subset=["velocidade_media"]).sort_values("velocidade_media", ascending=True)
        if v.empty:
            st.info("Story points indisponíveis neste recorte.")
        else:
            fig = px.bar(v, x="velocidade_media", y="projeto", color="projeto", orientation="h",
                         text="velocidade_media", color_discrete_map=PROJECT_COLORS,
                         labels={"velocidade_media": "Story points por sprint (média)", "projeto": ""})
            fig.update_traces(texttemplate="%{text:.2f}", textposition="outside", cliponaxis=False)
            chart(fig, height=345, legend=False, key="executive-velocity")

    row_c, row_d = st.columns(2, gap="medium")
    with row_c:
        section("Média de tarefas concluídas", "Comparação do volume médio de entregas por sprint.")
        avg = summary.dropna(subset=["media_entregas"]).sort_values("media_entregas", ascending=True)
        fig = px.bar(avg, x="media_entregas", y="projeto", color="projeto", orientation="h",
                     text="media_entregas", color_discrete_map=PROJECT_COLORS,
                     labels={"media_entregas": "Tarefas concluídas/sprint (média)", "projeto": ""})
        fig.update_traces(texttemplate="%{text:.2f}", textposition="outside", cliponaxis=False)
        chart(fig, height=300, legend=False, key="executive-avg-completed")
    with row_d:
        section("Alterações no escopo", "Adições e retiradas registradas ao longo das sprints selecionadas.")
        ch = summary.melt(id_vars=["projeto"], value_vars=["adicionadas", "retiradas"],
                          var_name="Movimento", value_name="Quantidade")
        if ch["Quantidade"].notna().any():
            fig = px.bar(ch, x="projeto", y="Quantidade", color="Movimento", barmode="group",
                         color_discrete_map={"adicionadas": BLUE, "retiradas": AMBER},
                         labels={"projeto": "Projeto"})
            chart(fig, height=300, key="executive-scope")
        else:
            st.info("Movimentação de escopo indisponível.")

    section("Leitura estratégica", "Insights automáticos calculados com os registros filtrados, sem textos pré-definidos por projeto.")
    insights = auto_insights(summary, h2, h3)
    for ix in range(0, len(insights), 3):
        cols = st.columns(3)
        for col, (label, who, desc) in zip(cols, insights[ix:ix+3]):
            with col:
                st.markdown(f"<div class='insight'><div class='overline'>{esc(label)}</div>"
                            f"<div class='who'>{esc(who)}</div><div class='desc'>{esc(desc)}</div></div>",
                            unsafe_allow_html=True)

    col1, col2 = st.columns([1.27, 1], gap="medium")
    with col1:
        section("Entregas por projeto", "Volume de tarefas concluídas por sprint, somado ao longo do recorte.")
        p = summary.sort_values("total_entregas", ascending=False)
        fig = px.bar(p, x="projeto", y="total_entregas", color="projeto", text="total_entregas",
                     color_discrete_map=PROJECT_COLORS,
                     labels={"projeto": "Projeto", "total_entregas": "Entregas"})
        fig.update_traces(textposition="outside", cliponaxis=False)
        chart(fig, height=340, legend=False, key="executive-deliveries")
    with col2:
        section("Status dos vínculos", "Distribuição das classificações de tarefas nas sprints filtradas.")
        if not status.empty:
            dist = status.groupby("status", as_index=False)["quantidade"].sum()
            fig = px.pie(dist, names="status", values="quantidade", hole=.65,
                         color_discrete_sequence=[ACCENT, BLUE, PINK, AMBER, RED])
            fig.update_traces(textinfo="percent", textposition="inside",
                              hovertemplate="%{label}: %{value} (%{percent})<extra></extra>")
            chart(fig, height=340, legend=True, key="executive-status")
        else:
            st.info("Distribuição de status indisponível. Verifique permissões de leitura à tabela tarefas_sprints.")

# --- Sprints e entregas --------------------------------------
with pages[1]:
    minmax = st.columns(4)
    with minmax[0]: st.metric("Média de entregas/sprint", number(selected["tarefas_concluidas"].mean(), 2))
    with minmax[1]: st.metric("Menor entrega", number(selected["tarefas_concluidas"].min()))
    with minmax[2]: st.metric("Maior entrega", number(selected["tarefas_concluidas"].max()))
    with minmax[3]: st.metric("Mediana", number(selected["tarefas_concluidas"].median(), 1))

    section("Evolução temporal das entregas", "Cada ponto representa uma sprint; linhas unem observações de um mesmo projeto.")
    timeline = selected.dropna(subset=["inicio", "tarefas_concluidas"]).sort_values(["projeto", "inicio"])
    if timeline.empty:
        st.info("Não há datas de sprint disponíveis para o gráfico temporal.")
    else:
        fig = px.line(timeline, x="inicio", y="tarefas_concluidas", color="projeto", markers=True,
                      hover_name="rotulo_sprint", color_discrete_map=PROJECT_COLORS,
                      labels={"inicio": "Início da sprint", "tarefas_concluidas": "Tarefas concluídas", "projeto": "Projeto"})
        fig.update_traces(line=dict(width=2.5), marker=dict(size=7))
        chart(fig, height=405, key="sprint-evolution")

    a, b = st.columns(2, gap="medium")
    with a:
        section("Consistência das entregas", "Dispersão por projeto, incluindo sprints com zero entregas.")
        fig = px.box(selected, x="projeto", y="tarefas_concluidas", color="projeto", points="outliers",
                     color_discrete_map=PROJECT_COLORS,
                     labels={"projeto": "Projeto", "tarefas_concluidas": "Concluídas por sprint"})
        chart(fig, height=365, legend=False, key="sprint-box")
    with b:
        section("Velocidade média", "Média de pontos concluídos por sprint dentro de cada projeto.")
        v = summary.dropna(subset=["velocidade_media"])
        if v.empty:
            st.info("Estimativas indisponíveis nesta seleção.")
        else:
            fig = px.bar(v, x="projeto", y="velocidade_media", color="projeto", text="velocidade_media",
                         color_discrete_map=PROJECT_COLORS,
                         labels={"projeto": "Projeto", "velocidade_media": "Pontos concluídos / sprint"})
            fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
            chart(fig, height=365, legend=False, key="sprint-velocity")

    section("Painel comparativo das entregas", "Média, mínimos, máximos e volume de pontos, recalculados conforme filtros.")
    col_names = {"projeto": "Projeto", "sprints": "Sprints", "total_entregas": "Concluídas",
                 "media_entregas": "Média/sprint", "min_entregas": "Mínimo", "max_entregas": "Máximo",
                 "velocidade_media": "Velocidade média", "pontos_totais": "Pontos concluídos"}
    table = summary[list(col_names)].rename(columns=col_names)
    st.dataframe(table, hide_index=True, use_container_width=True,
                 column_config={"Média/sprint": st.column_config.NumberColumn(format="%.2f"),
                                "Velocidade média": st.column_config.NumberColumn(format="%.2f")})

# --- Escopo -------------------------------------------------
with pages[2]:
    ac, bc, cc = st.columns(3)
    with ac: st.metric("Tarefas adicionadas", number(selected["tarefas_adicionadas"].sum(min_count=1)))
    with bc: st.metric("Tarefas retiradas", number(selected["tarefas_retiradas"].sum(min_count=1)))
    with cc: st.metric("Alterações acumuladas", number(total_changes))

    section("Movimentação de escopo", "Adições e retiradas registradas por sprint, agregadas nos projetos selecionados.")
    melted = summary.melt(id_vars=["projeto"], value_vars=["adicionadas", "retiradas"],
                          var_name="Movimento", value_name="Quantidade")
    if melted["Quantidade"].notna().any():
        fig = px.bar(melted, x="projeto", y="Quantidade", color="Movimento", barmode="group",
                     color_discrete_map={"adicionadas": BLUE, "retiradas": AMBER},
                     labels={"projeto": "Projeto"})
        chart(fig, height=355, key="scope-movement")
    else:
        st.info("A view de movimentação não tem valores disponíveis para este filtro.")

    section("Escopo × percentual Completed", "Relação descritiva por sprint, com linha de tendência por projeto. Não há inferência causal.")
    scope = selected.dropna(subset=["alteracoes", "percentual_completed"])
    if scope.empty:
        st.info("Não há pares válidos de movimentação e conclusão para a seleção.")
    else:
        fig = px.scatter(scope, x="alteracoes", y="percentual_completed", color="projeto",
                         hover_name="rotulo_sprint", color_discrete_map=PROJECT_COLORS,
                         labels={"alteracoes": "Adicionadas + retiradas", "percentual_completed": "Vínculos Completed (%)", "projeto": "Projeto"})
        fig.update_traces(marker=dict(size=10, opacity=.76, line=dict(width=1, color="#0F1B2B")))
        add_trend(fig, scope, "alteracoes", "percentual_completed")
        fig.update_yaxes(range=[0, 105])
        chart(fig, height=390, percent=True, key="scope-scatter")

    correlations_cards(h3, "H3 · Correlação de Pearson", "H3")
    section("Mudanças de escopo por faixa", "Média simples dos percentuais de sprint, mantendo a mesma definição usada na investigação H3.")
    if not buckets.empty:
        fig = px.bar(buckets, x="faixa", y="media_completed", color="projeto", barmode="group",
                     hover_data={"n_sprints": True, "media_alteracoes": ":.1f"},
                     color_discrete_map=PROJECT_COLORS,
                     labels={"faixa": "Alterações na sprint", "media_completed": "Completed médio (%)", "n_sprints": "Sprints", "projeto": "Projeto"})
        fig.update_yaxes(range=[0, 105])
        chart(fig, height=355, percent=True, key="scope-buckets")
    else:
        st.info("Não há dados suficientes para a análise por faixas.")

# --- Hipóteses -----------------------------------------------
with pages[3]:
    st.markdown("<div class='mini-banner'>As hipóteses foram investigadas de forma <b>exploratória</b>. Os coeficientes abaixo são calculados diretamente sobre sprints reais do filtro e <b>não indicam causalidade nem significância estatística</b>.</div>", unsafe_allow_html=True)

    section("H1 · As entregas variam entre sprints?", "Intervalo mínimo–máximo e média de tarefas concluídas, por projeto.")
    h1fig = go.Figure()
    for row in summary.itertuples(index=False):
        clr = color_for(row.projeto)
        h1fig.add_trace(go.Scatter(
            x=[row.min_entregas, row.max_entregas], y=[row.projeto, row.projeto], mode="lines",
            line=dict(color=clr, width=7), hovertemplate="Intervalo de entregas: %{x}<extra></extra>", showlegend=False))
        h1fig.add_trace(go.Scatter(
            x=[row.media_entregas], y=[row.projeto], mode="markers+text",
            marker=dict(color="#F8FBFF", size=13, symbol="diamond", line=dict(color=clr, width=3)),
            text=[f" média {row.media_entregas:.1f}"], textposition="top right",
            hovertemplate=f"{esc(row.projeto)} · média %{{x:.2f}}<extra></extra>", showlegend=False))
    h1fig.update_xaxes(title="Tarefas concluídas por sprint")
    chart(h1fig, height=345, legend=False, key="hyp-h1")
    st.caption("Extremos não explicam, por si só, as causas da variação das entregas.")

    st.divider()
    section("H2 · Tamanho da equipe e entregas", "Quantidade de desenvolvedores × tarefas concluídas, com tendência linear por projeto.")
    dev = selected.dropna(subset=["qtd_desenvolvedores", "tarefas_concluidas"])
    dev = dev[dev["qtd_desenvolvedores"] > 0]
    if not dev.empty:
        fig = px.scatter(dev, x="qtd_desenvolvedores", y="tarefas_concluidas", color="projeto",
                         hover_name="rotulo_sprint", color_discrete_map=PROJECT_COLORS,
                         labels={"qtd_desenvolvedores": "Desenvolvedores na sprint",
                                 "tarefas_concluidas": "Tarefas concluídas", "projeto": "Projeto"})
        fig.update_traces(marker=dict(size=9, opacity=.75))
        add_trend(fig, dev, "qtd_desenvolvedores", "tarefas_concluidas")
        chart(fig, height=370, key="hyp-h2-scatter")
    else:
        st.info("Coluna sprints.qtd_desenvolvedores sem dados suficientes.")
    correlations_cards(h2, "H2 · Coeficientes por projeto", "H2")

    st.divider()
    section("H3 · Alterações e conclusão", "Movimentações registradas × proporção de vínculos Completed por sprint.")
    if not scope.empty:
        fig = px.scatter(scope, x="alteracoes", y="percentual_completed", color="projeto",
                         hover_name="rotulo_sprint", color_discrete_map=PROJECT_COLORS,
                         labels={"alteracoes": "Adicionadas + retiradas",
                                 "percentual_completed": "Vínculos Completed (%)", "projeto": "Projeto"})
        fig.update_traces(marker=dict(size=9, opacity=.78))
        add_trend(fig, scope, "alteracoes", "percentual_completed")
        fig.update_yaxes(range=[0, 105])
        chart(fig, height=370, percent=True, key="hyp-h3-scatter")
    else:
        st.info("Sem dados suficientes para H3.")
    correlations_cards(h3, "H3 · Coeficientes por projeto", "H3")

# --- Auditoria -----------------------------------------------
with pages[4]:
    section("Rastreabilidade e qualidade", "Cada indicador abaixo tem origem em tabelas ou views SQL. Nenhum registro é escrito ou gerado.")
    missing_counts = [
        ("Sprints no filtro", len(selected)),
        ("Chaves projeto+sprint duplicadas", int(all_sprints.duplicated(["projeto", "sprint_id"]).sum())),
        ("Sprints sem total_tarefas", int(selected["total_tarefas"].isna().sum())),
        ("Sprints sem taxa por vínculo", int(selected["percentual_completed"].isna().sum())),
        ("Sprints sem contagem de equipe", int(selected["qtd_desenvolvedores"].isna().sum())),
        ("Sprints sem escopo calculável", int(selected["alteracoes"].isna().sum())),
    ]
    q = pd.DataFrame(missing_counts, columns=["Verificação", "Resultado"])
    st.dataframe(q, hide_index=True, use_container_width=True)

    sections = {
        "Consolidação por projeto": summary,
        "Sprints e indicadores (filtrados)": selected.drop(columns=["rotulo_sprint", "duracao_dias"], errors="ignore"),
        "Correlação H2": h2,
        "Correlação H3": h3,
        "H3 por faixa": buckets,
        "Distribuição de status": status,
    }
    section("Explorador de dados reais", "O conteúdo da tabela e do arquivo exportado acompanha os filtros ativos.")
    selected_tab = st.selectbox("Escolha a tabela", list(sections), key="audit-table-select")
    frame = sections[selected_tab]
    st.dataframe(frame, hide_index=True, use_container_width=True, height=360)
    st.download_button(
        "↓ Exportar tabela filtrada (CSV)",
        data=frame.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"agile_{selected_tab.lower().replace(' ', '_').replace('(', '').replace(')', '')}.csv",
        mime="text/csv", use_container_width=False,
    )
    with st.expander("Fontes SQL utilizadas"):
        st.code("""-- Consultas somente leitura, com origem no MySQL analise_agil.
SELECT * FROM analise_agil.vw_indicadores_sprint;
SELECT * FROM analise_agil.vw_conclusao_por_sprint;
SELECT * FROM analise_agil.vw_movimentacao_sprints;
SELECT projeto, sprint_id, qtd_desenvolvedores
  FROM analise_agil.sprints WHERE origem_registro = 'dataset';
SELECT ts.projeto, ts.sprint_id, ts.status, COUNT(*) AS quantidade
  FROM analise_agil.tarefas_sprints ts
  INNER JOIN analise_agil.sprints s ON s.projeto = ts.projeto
       AND s.sprint_id = ts.sprint_id
  WHERE s.origem_registro = 'dataset'
  GROUP BY ts.projeto, ts.sprint_id, ts.status;""", language="sql")
    with st.expander("Dicionário de indicadores e limitações"):
        st.markdown("""
- **Entregas:** soma de `tarefas_concluidas` por sprint. Não corresponde necessariamente a tarefas únicas.
- **Velocidade média:** `AVG(pontos_concluidos)` por sprint. A escala de story points depende da equipe.
- **Vínculos Completed:** `100 × SUM(vinculos_completed) / SUM(total_vinculos)` sobre as sprints filtradas.
- **Média de conclusão por sprint:** média aritmética de `percentual_completed` por sprint; diferente da taxa agregada.
- **Escopo:** quantidade de tarefas adicionadas + retiradas por sprint, conforme `vw_movimentacao_sprints`.
- **H1:** mínimos, máximos e médias de tarefas concluídas por sprint.
- **H2:** coeficiente de Pearson entre `qtd_desenvolvedores` e `tarefas_concluidas`.
- **H3:** coeficiente de Pearson entre alterações de escopo e `percentual_completed`.
- **Delimitação:** considera somente sprints com `origem_registro = 'dataset'` (238 na base original). Referências incompletas do UserGrid não são incluídas nos cálculos por sprint. O percentual global de todos os vínculos da tabela pode diferir.
- **Limites:** associações não implicam causalidade; gráficos não são testes de significância. O painel usa apenas dados históricos dos projetos de software livre do dataset Agile Scrum.
""")

st.markdown("<div class='separator'></div>", unsafe_allow_html=True)
st.caption("Agile Scrum · Sprint Intelligence  ·  Dados de projetos de software livre  ·  Fonte: MySQL / "
           + esc(schema) + "  ·  Consulta somente leitura  ·  Atualização sob demanda ou ao expirar o cache.")
