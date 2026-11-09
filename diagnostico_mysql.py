"""Diagnóstico local da conexão Agile Scrum -> MySQL.

Execute na pasta do projeto: py diagnostico_mysql.py
NÃO publica senha ou detalhes privados no navegador.
"""
from __future__ import annotations

import os
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SECRETS = ROOT / ".streamlit" / "secrets.toml"
REQUIRED_VIEWS = (
    "vw_indicadores_sprint",
    "vw_conclusao_por_sprint",
    "vw_movimentacao_sprints",
)


def banner(label: str) -> None:
    print("\n" + "=" * 64)
    print(label)
    print("=" * 64)


def safe(message: object, password: str) -> str:
    """Remove the configured password if an exception ever includes it."""
    message = str(message)
    return message.replace(password, "[SENHA OCULTA]") if password else message


def load_conf() -> dict:
    banner("1/4 — Arquivo de configuração")
    print("Pasta do programa:", ROOT)
    print("Arquivo esperado: .streamlit/secrets.toml")
    if SECRETS.exists():
        try:
            with SECRETS.open("rb") as fh:
                d = tomllib.load(fh)
        except tomllib.TOMLDecodeError as exc:
            raise RuntimeError("O arquivo secrets.toml contém sintaxe TOML inválida: " + str(exc)) from exc
        print("OK: arquivo encontrado e formato TOML válido.")
    else:
        d = {}
        alternatives = [
            ROOT / ".streamlit" / "secrets.toml.example",
            ROOT / ".streamlit" / "secrets.toml.txt",
        ]
        for alt in alternatives:
            if alt.exists():
                print("AVISO: existe", alt.name, ", mas ele NÃO é o arquivo carregado pelo Streamlit.")
        print("AVISO: não foi localizado o secrets.toml. Tentaremos apenas variáveis de ambiente.")

    keys = ("MYSQL_HOST", "MYSQL_PORT", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE")
    values = {k: str(d.get(k, os.getenv(k, ""))).strip() for k in keys}
    values["MYSQL_HOST"] = values["MYSQL_HOST"] or "127.0.0.1"
    values["MYSQL_PORT"] = values["MYSQL_PORT"] or "3306"
    values["MYSQL_DATABASE"] = values["MYSQL_DATABASE"] or "analise_agil"
    missing = [key for key in ("MYSQL_USER", "MYSQL_PASSWORD") if not values[key]]
    if missing:
        raise RuntimeError(
            "O programa não encontrou estas configurações: " + ", ".join(missing)
            + ". Crie o arquivo .streamlit/secrets.toml a partir do modelo e salve-o."
        )
    try:
        values["MYSQL_PORT"] = int(values["MYSQL_PORT"])
    except ValueError as exc:
        raise RuntimeError("MYSQL_PORT deve ser um número inteiro como 3306.") from exc
    print("Host:", values["MYSQL_HOST"])
    print("Porta:", values["MYSQL_PORT"])
    print("Usuário:", values["MYSQL_USER"])
    print("Schema:", values["MYSQL_DATABASE"])
    print("Senha: CONFIGURADA (valor oculto)")
    if values["MYSQL_USER"] == values["MYSQL_DATABASE"]:
        print("ATENÇÃO: o nome do usuário coincide com o do banco. Isso só é correto se essa conta MySQL realmente existir.")

    values["MYSQL_SSL_CA_PATH"] = str(d.get("MYSQL_SSL_CA_PATH", os.getenv("MYSQL_SSL_CA_PATH", "")))
    values["MYSQL_SSL_CA_PEM"] = str(d.get("MYSQL_SSL_CA_PEM", os.getenv("MYSQL_SSL_CA_PEM", "")))
    return values


def hint(err) -> str:
    n = getattr(err, "errno", None)
    return {
        1045: "Acesso negado: usuário/senha incorretos ou usuário não autorizado nesse host. Veja o login no Workbench.",
        1044: "Seu usuário não tem acesso ao schema analise_agil.",
        1049: "O schema MYSQL_DATABASE não foi encontrado nesse servidor.",
        1142: "Falta permissão SELECT na tabela ou view. Use um usuário com leitura autorizada.",
        1146: "Uma das tabelas ou views solicitadas não existe nesse schema.",
        1356: "Uma view existe, mas sua definição/DEFINER ou os privilégios estão inválidos.",
        2003: "O serviço MySQL está desligado, a porta está diferente ou a conexão foi bloqueada.",
        2005: "O nome MYSQL_HOST não pôde ser resolvido.",
        2059: "Problema de compatibilidade no plugin de autenticação do MySQL.",
    }.get(n, "Veja o código MySQL e a mensagem acima; não é necessário recriar seu banco sem identificar a causa.")


def main() -> int:
    conf = load_conf()
    try:
        import mysql.connector
    except ImportError:
        print("ERRO: pacote mysql-connector-python não instalado neste Python.")
        print("Execute: py -m pip install -r requirements.txt")
        return 1

    banner("2/4 — Login no servidor MySQL")
    cn = None
    try:
        kwargs = dict(
            host=conf["MYSQL_HOST"], port=conf["MYSQL_PORT"],
            user=conf["MYSQL_USER"], password=conf["MYSQL_PASSWORD"],
            database=conf["MYSQL_DATABASE"], connection_timeout=10,
            autocommit=True,
        )
        if conf["MYSQL_SSL_CA_PATH"].strip():
            kwargs.update(ssl_ca=conf["MYSQL_SSL_CA_PATH"].strip(),
                          ssl_verify_cert=True, ssl_verify_identity=True)
        # Para CA PEM em secret (sem caminho), deixe a chamada oficial do data_layer configurar o arquivo temporário.
        cn = mysql.connector.connect(**kwargs)
        cursor = cn.cursor()
        cursor.execute("SELECT USER(), CURRENT_USER(), DATABASE()")
        print("OK: login realizado. USER(), CURRENT_USER(), DATABASE():", cursor.fetchone())
        banner("3/4 — Views e linhas disponíveis")
        for name in REQUIRED_VIEWS:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM `{conf['MYSQL_DATABASE']}`.`{name}`")
                result = cursor.fetchone()
                print(f"OK: {name} = {result[0]} linhas")
            except mysql.connector.Error as exc:
                print(f"FALHA: {name}", safe(exc, conf["MYSQL_PASSWORD"]))
                print("Causa provável:", hint(exc))
                return 1
    except mysql.connector.Error as exc:
        print("FALHA no MySQL:", safe(exc, conf["MYSQL_PASSWORD"]))
        print("Causa provável:", hint(exc))
        return 1
    finally:
        if cn is not None and cn.is_connected():
            cn.close()

    banner("4/4 — Leitura e preparação dos indicadores no dashboard")
    try:
        from data_layer import get_mysql_data, prepare_sprints
        sources, source_errors = get_mysql_data(
            conf["MYSQL_HOST"], conf["MYSQL_PORT"], conf["MYSQL_USER"],
            conf["MYSQL_PASSWORD"], conf["MYSQL_DATABASE"],
            ssl_ca_pem=conf["MYSQL_SSL_CA_PEM"],
            ssl_ca_path=conf["MYSQL_SSL_CA_PATH"],
        )
        for src, error in source_errors.items():
            print("AVISO fonte opcional", src, ":", safe(error, conf["MYSQL_PASSWORD"]))
        base, alerts = prepare_sprints(sources)
        print("OK: dados processados com sucesso.")
        print("Sprints:", len(base), "| Projetos:", base["projeto"].nunique())
        print("Por projeto:")
        print(base.groupby("projeto").size().to_string())
        for a in alerts:
            print("AVISO:", safe(a, conf["MYSQL_PASSWORD"]))
        print("\nTudo certo. Inicie o painel: py -m streamlit run app.py --server.port 8502")
        return 0
    except Exception as exc:
        print("FALHA no processamento:", type(exc).__name__, safe(exc, conf["MYSQL_PASSWORD"]))
        print("As views podem funcionar individualmente e ainda assim ter uma coluna ausente ou chave duplicada.")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("\nERRO DE CONFIGURAÇÃO:", type(exc).__name__, str(exc))
        print("Verifique se há um único secrets.toml, salvo na pasta .streamlit do projeto.")
        sys.exit(1)
