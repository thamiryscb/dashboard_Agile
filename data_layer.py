"""Consulta exclusivamente de leitura ao MySQL da análise Agile Scrum.

Não gera números fictícios, não importa arquivos e não altera o banco.
"""
from __future__ import annotations

import os
import re
import tempfile

import mysql.connector
import pandas as pd

SCHEMA_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Os nomes de objetos são constantes em código, não vêm de entradas do usuário.
QUERIES = {
    "sprints": "SELECT * FROM {schema}.`vw_indicadores_sprint`",
    "conclusao": "SELECT * FROM {schema}.`vw_conclusao_por_sprint`",
    "movimentacao": "SELECT * FROM {schema}.`vw_movimentacao_sprints`",
    "desenvolvedores": (
        "SELECT `projeto`, `sprint_id`, `qtd_desenvolvedores` "
        "FROM {schema}.`sprints` WHERE `origem_registro` = 'dataset'"
    ),
    "status": (
        "SELECT ts.`projeto`, ts.`sprint_id`, ts.`status`, "
        "COUNT(*) AS `quantidade` FROM {schema}.`tarefas_sprints` ts "
        "INNER JOIN {schema}.`sprints` s "
        "ON s.`projeto` = ts.`projeto` AND s.`sprint_id` = ts.`sprint_id` "
        "WHERE s.`origem_registro` = 'dataset' "
        "GROUP BY ts.`projeto`, ts.`sprint_id`, ts.`status`"
    ),
    "catalogo": "SELECT `projeto`, COUNT(*) AS `tarefas_catalogo` FROM {schema}.`tarefas` GROUP BY `projeto`",
    "historico_vinculos": "SELECT `projeto`, COUNT(*) AS `vinculos_historicos` FROM {schema}.`tarefas_sprints` GROUP BY `projeto`",
}
REQUIRED = {"sprints", "conclusao", "movimentacao"}


def get_mysql_data(host: str, port: int, user: str, password: str, schema: str,
                   ssl_ca_pem: str = "", ssl_ca_path: str = "") -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    """Consulta fontes MySQL por SELECT. TLS com validação se for fornecido CA.

    Em implantação pública, configure um banco remoto e uma CA válida do provedor.
    O certificado privado e a senha nunca são exibidos aos visitantes.
    """
    if not SCHEMA_RE.fullmatch(schema):
        raise ValueError("Schema inválido.")
    args = dict(
        host=host, port=int(port), user=user, password=password,
        database=schema, connection_timeout=10,
        charset="utf8mb4", use_unicode=True, autocommit=True,
    )
    tmp_ca = None
    try:
        if ssl_ca_pem.strip():
            if "BEGIN CERTIFICATE" not in ssl_ca_pem:
                raise ValueError("MYSQL_SSL_CA_PEM deve conter um certificado CA PEM válido.")
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".pem", delete=False) as cert:
                cert.write(ssl_ca_pem.strip() + "\n")
                tmp_ca = cert.name
            ssl_ca_path = tmp_ca
        if ssl_ca_path.strip():
            args.update(ssl_disabled=False, ssl_ca=ssl_ca_path,
                        ssl_verify_cert=True, ssl_verify_identity=True)
        conn = mysql.connector.connect(**args)
        data, errors = {}, {}
        try:
            cursor = conn.cursor(dictionary=True)
            try:
                for name, sql in QUERIES.items():
                    try:
                        cursor.execute(sql.format(schema=f"`{schema}`"))
                        data[name] = pd.DataFrame(cursor.fetchall())
                    except mysql.connector.Error as exc:
                        errors[name] = f"{exc.msg} (MySQL {exc.errno})"
                        data[name] = pd.DataFrame()
            finally:
                cursor.close()
        finally:
            conn.close()
    finally:
        if tmp_ca and os.path.exists(tmp_ca):
            os.remove(tmp_ca)
    unavailable = [n for n in REQUIRED if n in errors or data[n].empty]
    if unavailable:
        raise ValueError("Fontes obrigatórias indisponíveis: " + ", ".join(sorted(unavailable)))
    return data, errors


def _unique_keys(frame: pd.DataFrame, name: str) -> None:
    if frame.duplicated(["projeto", "sprint_id"]).any():
        raise ValueError(f"A fonte {name} possui chaves projeto+sprint_id repetidas. Corrija antes de usar o dashboard.")


def _numeric(frame: pd.DataFrame, columns: list[str]) -> None:
    for col in columns:
        if col in frame:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")


def prepare_sprints(data: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, list[str]]:
    """Faz junções 1:1 entre as views, sem multiplicar sprints nem preencher ausências."""
    raw = data["sprints"]
    expected = {
        "projeto", "sprint_id", "nome", "estado", "inicio", "fim",
        "total_tarefas", "tarefas_concluidas", "pontos_concluidos", "taxa_conclusao",
    }
    missing = expected - set(raw.columns)
    if missing:
        raise ValueError("vw_indicadores_sprint sem colunas: " + ", ".join(sorted(missing)))
    if raw.empty:
        raise ValueError("A view vw_indicadores_sprint está vazia.")
    f = raw.copy()
    _unique_keys(f, "vw_indicadores_sprint")
    _numeric(f, ["sprint_id", "total_tarefas", "tarefas_concluidas", "pontos_concluidos", "taxa_conclusao"])
    for col in ["inicio", "fim"]:
        f[col] = pd.to_datetime(f[col], errors="coerce")
    for col in ["projeto", "nome", "estado"]:
        f[col] = f[col].fillna("Não informado").astype(str)
    f["rotulo_sprint"] = f["nome"] + " · #" + f["sprint_id"].astype(str)
    f["duracao_dias"] = (f["fim"] - f["inicio"]).dt.total_seconds() / 86400
    warnings = []

    # A view nova é a fonte da medida de conclusão coerente para OS QUATRO projetos.
    c = data.get("conclusao", pd.DataFrame()).copy()
    c_expected = {"projeto", "sprint_id", "total_vinculos", "tarefas_concluidas", "percentual_completed"}
    if not c.empty and c_expected.issubset(c.columns):
        _unique_keys(c, "vw_conclusao_por_sprint")
        c = c[list(c_expected)].rename(columns={"tarefas_concluidas": "vinculos_completed"})
        _numeric(c, ["sprint_id", "total_vinculos", "vinculos_completed", "percentual_completed"])
        f = f.merge(c, on=["projeto", "sprint_id"], how="left", validate="one_to_one")
    else:
        if not c.empty:
            warnings.append("A view de conclusão possui colunas inesperadas.")
        for col in ["total_vinculos", "vinculos_completed", "percentual_completed"]:
            f[col] = float("nan")
        warnings.append("Sem vw_conclusao_por_sprint: a conclusão comparável nos quatro projetos não está disponível.")

    m = data.get("movimentacao", pd.DataFrame()).copy()
    m_expected = {"projeto", "sprint_id", "tarefas_adicionadas", "tarefas_retiradas"}
    if not m.empty and m_expected.issubset(m.columns):
        _unique_keys(m, "vw_movimentacao_sprints")
        m = m[list(m_expected)]
        _numeric(m, ["sprint_id", "tarefas_adicionadas", "tarefas_retiradas"])
        f = f.merge(m, on=["projeto", "sprint_id"], how="left", validate="one_to_one")
    else:
        for col in ["tarefas_adicionadas", "tarefas_retiradas"]:
            f[col] = float("nan")
        warnings.append("Sem vw_movimentacao_sprints compatível: análises de escopo indisponíveis.")

    dev = data.get("desenvolvedores", pd.DataFrame()).copy()
    if not dev.empty and {"projeto", "sprint_id", "qtd_desenvolvedores"}.issubset(dev.columns):
        _unique_keys(dev, "sprints (qtd_desenvolvedores)")
        _numeric(dev, ["sprint_id", "qtd_desenvolvedores"])
        f = f.merge(dev[["projeto", "sprint_id", "qtd_desenvolvedores"]],
                    on=["projeto", "sprint_id"], how="left", validate="one_to_one")
    else:
        f["qtd_desenvolvedores"] = float("nan")
        warnings.append("Quantidade de desenvolvedores indisponível. Verifique sprints.qtd_desenvolvedores.")

    f["alteracoes"] = f["tarefas_adicionadas"] + f["tarefas_retiradas"]
    f["percentual_completed"] = f["percentual_completed"].where(f["percentual_completed"].between(0, 100))
    f["pontos_concluidos"] = f["pontos_concluidos"].where(f["pontos_concluidos"] >= 0)
    f = f.sort_values(["projeto", "inicio", "sprint_id"], na_position="last").reset_index(drop=True)
    return f, warnings


def filter_status_data(status: pd.DataFrame, frame: pd.DataFrame) -> pd.DataFrame:
    """Retorna contagens de status apenas das sprints no filtro atual."""
    if status.empty or not {"projeto", "sprint_id", "status", "quantidade"}.issubset(status.columns):
        return pd.DataFrame(columns=["projeto", "sprint_id", "status", "quantidade"])
    valid = frame[["projeto", "sprint_id"]].drop_duplicates()
    result = status.merge(valid, on=["projeto", "sprint_id"], how="inner")
    result["quantidade"] = pd.to_numeric(result["quantidade"], errors="coerce")
    return result
