
# Agile Scrum — Sprint Intelligence

Dashboard interativo desenvolvido em **Python, Streamlit e Plotly**, integrado ao banco de dados **MySQL (`analise_agil`)**.

A aplicação permite analisar indicadores de desempenho de quatro projetos de software livre: **Aurora, Meso, Spring XD e UserGrid**, utilizando dados históricos do Agile Scrum Sprint Velocity Dataset.

O sistema realiza somente consultas (`SELECT`), sem modificar os registros do banco.

## Funcionalidades

O dashboard disponibiliza:

- **Visão executiva:** indicadores de projetos, sprints, entregas, velocidade e conclusão.
- **Análise de entregas:** evolução temporal, médias, valores mínimos e máximos e dispersão por projeto.
- **Análise de escopo:** tarefas adicionadas e retiradas durante as sprints.
- **Hipóteses H1, H2 e H3:** investigação das entregas, tamanho das equipes e alterações de escopo.
- **Exploração dos dados:** consultas, filtros interativos, verificações de qualidade e exportação CSV.

Os indicadores são recalculados conforme os filtros aplicados, respeitando as particularidades das métricas históricas.

## Tecnologias utilizadas

- Python
- Streamlit
- Plotly
- MySQL
- mysql-connector-python

## Estrutura do projeto

```text
dashboard_Agile/
├── app.py
├── analytics.py
├── data_layer.py
├── requirements.txt
├── README.md
├── .gitignore
├── sql/
│   └── usuario_somente_leitura.sql
└── .streamlit/
    ├── config.toml
    └── secrets.toml.example
```

## Como executar

### 1. Clonar o repositório

```powershell
git clone https://github.com/thamiryscb/dashboard_Agile.git
cd dashboard_Agile
```

### 2. Instalar as dependências

É necessário possuir Python e MySQL configurados.

No terminal do VS Code, execute:

```powershell
py -m pip install -r requirements.txt
```

### 3. Configurar a conexão com MySQL

Copie o arquivo:

`.streamlit/secrets.toml.example`

E renomeie a cópia para:

`.streamlit/secrets.toml`

Configure as credenciais do banco:

```toml
MYSQL_HOST = "127.0.0.1"
MYSQL_PORT = 3306
MYSQL_USER = "usuario_leitura"
MYSQL_PASSWORD = "SUA_SENHA"
MYSQL_DATABASE = "analise_agil"
```

O arquivo `secrets.toml` contém informações privadas e está incluído no `.gitignore`.

**Importante:** nunca publique credenciais reais no GitHub. Recomenda-se utilizar um usuário MySQL com permissão somente de leitura.

### 4. Executar o dashboard

```powershell
py -m streamlit run app.py --server.port 8502
```

Acesse no navegador:

http://localhost:8502

## Estrutura necessária no MySQL

O banco `analise_agil` deve conter as tabelas:

- `projetos`
- `tarefas`
- `sprints`
- `tarefas_sprints`
- `issues_origem`

Também são necessárias as views:

- `vw_indicadores_sprint`
- `vw_conclusao_por_sprint`
- `vw_movimentacao_sprints`

A aplicação utiliza essas estruturas para consultar e calcular os indicadores apresentados.

Para verificar se as views estão disponíveis:

```sql
USE analise_agil;

SHOW FULL TABLES WHERE Table_type = 'VIEW';
```

O repositório contém o código da aplicação, mas não inclui o banco de dados completo nem credenciais de acesso.


## Importação do banco de dados

O repositório disponibiliza o arquivo
`sql/analise_agil.sql`, contendo a estrutura
e os dados utilizados pelo dashboard.

Para importar no MySQL Workbench:

1. Abra **Server → Data Import**.
2. Selecione **Import from Self-Contained File**.
3. Escolha `sql/analise_agil.sql`.
4. Se necessário, selecione ou crie o schema `analise_agil`.
5. Clique em **Start Import**.

Após a importação, configure o arquivo
`.streamlit/secrets.toml` e execute a aplicação.

O banco contém registros históricos dos projetos
Aurora, Meso, Spring XD e UserGrid.

## Considerações sobre os indicadores

- **Entregas:** representam tarefas concluídas por sprint. Uma tarefa pode aparecer em diferentes ciclos.
- **Velocidade:** corresponde à média de pontos concluídos por sprint, considerando a escala de cada projeto.
- **Conclusão:** representa a proporção de vínculos classificados como `Completed` no recorte analisado.
- **Escopo:** considera tarefas adicionadas e retiradas durante as sprints.
- **Hipóteses:** as análises são exploratórias. Correlações não representam necessariamente relações de causalidade.

## Fonte dos dados

Os dados foram obtidos do repositório público:

[Agile Scrum Sprint Velocity Dataset](https://github.com/RandulaKoralage/AgileScrumSprintVelocityDataSet)

O conjunto de dados reúne informações históricas de projetos de software livre extraídas da plataforma Jira.

## Repositório

Desenvolvido como parte do projeto acadêmico **EJFlow — Gerenciador de Projetos para Empresas Juniores**, da Universidade Federal do Rio Grande do Norte (UFRN).
