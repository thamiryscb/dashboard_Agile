# Agile Scrum — Sprint Intelligence

Painel interativo feito com **Streamlit + Plotly**, que consulta o banco **MySQL `analise_agil`**. Destina-se **exclusivamente à análise de Agile Scrum** dos projetos Aurora, Meso, Spring XD e UserGrid.

**Sem dados fictícios. Sem índices compostos artificiais nem métricas alheias ao Agile Scrum.** Não modifica registros: executa somente `SELECT`.

## Conteúdo do dashboard

- **Visão executiva:** projetos, sprints, tarefas concluídas, proporção de vínculos `Completed`, velocidade, alterações e comparativo visual de quatro KPIs independentes (conclusão, velocidade, entregas e escopo). Inclui insights calculados a partir dos resultados.
- **Sprints e entregas:** média, mínimo, máximo, mediana, evolução por sprint, boxplot, velocidade média e tabela comparativa.
- **Escopo e conclusão:** tarefas adicionadas/retiradas, gráficos de dispersão, H3 por faixas e correlações por projeto.
- **Hipóteses H1–H3:** amplitude de entregas; correlação entre desenvolvedores e entregas (H2); correlação entre mudanças de escopo e proporção de vínculos concluídos (H3).
- **Dados e auditoria:** qualidade dos registros, análise de ausências, tabelas filtradas e download de CSV.

Filtros de projeto, estado e data inicial das sprints recalculam os indicadores. Os números do catálogo histórico seguem apenas o filtro de projeto (não data/estado), com aviso na interface.

## Rodar no Windows com VS Code

1. Extraia o ZIP e abra esta pasta (`AgileScrum_Dashboard_Compartilhavel`) no VS Code.
2. Copie `.streamlit/secrets.toml.example` para `.streamlit/secrets.toml`. Preencha com as credenciais do **seu MySQL** (preferencialmente usuário de leitura). Esse arquivo está no `.gitignore`.
3. Para testar apenas no PC local, é possível usar seu usuário MySQL habitual; para compartilhar o painel, utilize a conta somente leitura indicada em `sql/usuario_somente_leitura.sql` (não publique credenciais `root`). No terminal PowerShell, execute:

```powershell
py -m pip install -r requirements.txt
py -m streamlit run app.py --server.port 8502
```

4. Abra `http://localhost:8502`. A conexão é estabelecida pelo servidor; **não há caixa de login MySQL para visitantes**.

> O código NÃO contém senha, dados CSV ou exportação do banco. Se os valores não aparecerem, verifique se o MySQL está em execução e as views necessárias existem.

## Dados necessários no MySQL

Banco `analise_agil` com:

| Objeto | Uso |
|---|---|
| `vw_indicadores_sprint` | projeto, sprint_id, nome, estado, inicio, fim, total_tarefas, tarefas_concluidas, pontos_concluidos, taxa_conclusao |
| `vw_conclusao_por_sprint` | projeto, sprint_id, total_vinculos, tarefas_concluidas, percentual_completed |
| `vw_movimentacao_sprints` | projeto, sprint_id, tarefas_adicionadas, tarefas_retiradas |
| `sprints` | projeto, sprint_id, qtd_desenvolvedores, origem_registro |
| `tarefas_sprints` | projeto, sprint_id, status (e contagem histórica) |
| `tarefas` | projeto (contagem histórica) |

Todas as três views acima são **obrigatórias**. O painel interrompe a exibição quando alguma não está acessível, em vez de inventar resultados. A coluna `qtd_desenvolvedores` é necessária para H2. A base consolidada esperada tem **238 sprints originais**, além de duas referências incompletas fora da análise por sprint.

Para conferir:

```sql
USE analise_agil;
SELECT projeto, COUNT(*) FROM vw_conclusao_por_sprint GROUP BY projeto;
SELECT projeto, COUNT(*) FROM vw_movimentacao_sprints GROUP BY projeto;
SELECT projeto, COUNT(*) FROM vw_indicadores_sprint GROUP BY projeto;
```

## Tornar acessível por link (outras pessoas)

Leia **`PUBLICACAO_ONLINE.md`** para duas maneiras de compartilhar: **(a)** link temporário via Cloudflare Tunnel mantendo o MySQL no seu PC; **(b)** publicação duradoura no Streamlit Community Cloud com GitHub e banco MySQL remoto. O arquivo inclui a diferença entre MySQL `127.0.0.1` e MySQL de nuvem, como adicionar Secrets e medidas de segurança.

**Atenção:** subir apenas o código ao Streamlit Community Cloud **não torna seu MySQL local acessível**. Para uma URL que funcione fora do seu computador, o servidor Streamlit deve conseguir chegar ao banco. Solução recomendada: servidor MySQL remoto seguro, configurado com credencial de **somente leitura** e TLS com verificação de certificado. Não exponha seu MySQL doméstico diretamente na internet.

O app pode ser público (qualquer pessoa com o link visualiza os indicadores) ou privado (acesso limitado a convidados), conforme as opções de compartilhamento da hospedagem. Visitantes nunca recebem as credenciais do banco.

## Métricas e ressalvas

- **Entregas:** soma de `tarefas_concluidas` por sprint, podendo somar registros de uma mesma tarefa em sprints distintas.
- **Velocidade:** média de `pontos_concluidos` por sprint. Story points têm escala relativa a cada projeto; não são uma medida universal de produtividade.
- **Conclusão:** no painel comparativo, `100 × soma(vinculos_completed) / soma(total_vinculos)` sobre as **sprints originais filtradas**. Difere da média simples das taxas individuais de sprint e pode diferir da taxa global que inclui as duas referências incompletas do UserGrid.
- **Escopo:** adições + retiradas segundo a view de movimentação. Não significa sucesso ou fracasso.
- **H1/H2/H3:** investigação descritiva; correlação de Pearson não é teste de significância e não permite inferir causalidade.
- **Origem:** histórico dos quatro projetos de software livre do dataset Agile Scrum.

## Estrutura

```text
AgileScrum_Dashboard_Compartilhavel/
├── app.py
├── analytics.py
├── data_layer.py
├── requirements.txt
├── README.md
├── PUBLICACAO_ONLINE.md
├── ROTEIRO_DEMO.md
├── sql/usuario_somente_leitura.sql
├── .gitignore
└── .streamlit/
    ├── config.toml
    └── secrets.toml.example
```

Nenhuma credencial ou dump de dados é incluído no ZIP.

## Quando aparecer “Conexão de dados indisponível”

A mensagem pública não detalha erros por segurança. Na pasta do projeto, rode:

```powershell
py diagnostico_mysql.py
```

O diagnóstico (1) procura `.streamlit/secrets.toml` na pasta correta; (2) valida a sintaxe TOML; (3) testa a autenticação; (4) consulta diretamente as views; (5) reproduz as junções e a validação das colunas do dashboard. **A senha não é impressa**. Se ele mostrar uma falha, compartilhe apenas o texto do erro, sem fornecer credenciais nem o conteúdo do arquivo `secrets.toml`.

Se não houver o `secrets.toml`, **não basta editar `secrets.toml.example`**: é necessário fazer uma cópia com o nome exato `.streamlit/secrets.toml`. Caso utilize Windows, ative a opção de visualizar extensões de arquivos para evitar `secrets.toml.txt`.
