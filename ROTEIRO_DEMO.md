# Roteiro de demonstração — Dashboard Agile Scrum

**Objetivo:** mostrar a capacidade de analisar o histórico de projetos ágeis usando dados reais de um banco MySQL.

## 1. Contexto (15 s)

"O painel apresenta informações históricas de quatro projetos de software livre presentes em um dataset Agile Scrum. Todos os indicadores são consultados diretamente do MySQL e podem ser filtrados por projeto, estado e período."

## 2. Visão geral (40 s)

Abra a aba **Visão executiva**. Mostre os cards de projetos, sprints, entregas e alterações. Compare a proporção de vínculos Completed, a velocidade média e a média de tarefas concluídas entre projetos. Explique que cada indicador é independente e não há um índice composto de produtividade.

## 3. Entregas e escopo (30 s)

Abra **Sprints e entregas** e destaque o histórico, mínimo, máximo e dispersão das entregas. Em **Escopo e conclusão**, mostre adições, retiradas e sua distribuição, lembrando que associação não é causalidade.

## 4. Hipóteses H1–H3 (30 s)

- H1: a quantidade de entregas varia de sprint para sprint.
- H2: correlação entre quantidade de desenvolvedores e tarefas concluídas.
- H3: correlação entre alterações de escopo e proporção de vínculos Completed.

Mostre que os coeficientes são atualizados quando os filtros mudam.

## 5. Rastreabilidade (15 s)

Abra **Dados e auditoria** e demonstre a exportação CSV. Explique as três views obrigatórias e que o dashboard não modifica o banco. Encerre mostrando o link público/privado da hospedagem, se já publicado.

**Cuidados:** não afirmar que *story points* são comparáveis entre equipes; não apresentar correlação como causalidade; explicar que são projetos históricos de software livre.
