-- MODELO. Execute como ADMINISTRADOR do MySQL somente depois de revisar.
-- Substitua TROQUE_POR_UMA_SENHA_FORTE e restrinja o host quando possível.
-- '%' permite diferentes origens: proteja a rede com firewall / lista de IPs.
CREATE USER IF NOT EXISTS 'agile_dashboard'@'%'
    IDENTIFIED BY 'TROQUE_POR_UMA_SENHA_FORTE';

GRANT SELECT ON `analise_agil`.`vw_indicadores_sprint` TO 'agile_dashboard'@'%';
GRANT SELECT ON `analise_agil`.`vw_conclusao_por_sprint` TO 'agile_dashboard'@'%';
GRANT SELECT ON `analise_agil`.`vw_movimentacao_sprints` TO 'agile_dashboard'@'%';
GRANT SELECT ON `analise_agil`.`sprints` TO 'agile_dashboard'@'%';
GRANT SELECT ON `analise_agil`.`tarefas_sprints` TO 'agile_dashboard'@'%';
GRANT SELECT ON `analise_agil`.`tarefas` TO 'agile_dashboard'@'%';

-- Sem INSERT, UPDATE, DELETE, DROP, ALTER ou CREATE.
SHOW GRANTS FOR 'agile_dashboard'@'%';
