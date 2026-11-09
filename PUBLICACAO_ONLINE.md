# Publicar o dashboard Agile Scrum para outras pessoas acessarem

## O que muda ao publicar?

A hospedagem executa o aplicativo Python/Streamlit em um servidor. A pessoa abre o endereço HTTPS do painel no navegador sem instalar nada. **O servidor**, e não o visitante, acessa o MySQL. O aplicativo não pede senha do banco ao público.

Arquitetura:

```text
Visitantes (navegador)
          |
          v
Streamlit Community Cloud (dashboard, HTTPS)
          |
          | SELECT + credencial somente leitura + TLS
          v
MySQL remoto (schema analise_agil)
```

**Importante:** `127.0.0.1` / `localhost` na nuvem representa o próprio servidor da nuvem, **não** seu computador. Não é possível usar o MySQL instalado no seu Windows como `MYSQL_HOST = '127.0.0.1'` numa implantação em nuvem.

## Passo 1 — Obtenha uma instância MySQL acessível pela hospedagem

Opções usuais incluem serviço gerenciado MySQL ou servidor próprio com conectividade adequada. Importe **uma cópia** do schema `analise_agil` com tabelas e views, usando seus arquivos SQL/dump originais; preserve também os dados da coluna `qtd_desenvolvedores` e a view `vw_conclusao_por_sprint`.

> A hospedagem do Streamlit não hospeda automaticamente seu banco; é necessário configurar essa etapa separadamente. Não copie o dump com os dados para o repositório GitHub por acidente.

Cuidados:

- Exponha a porta MySQL apenas à infraestrutura autorizada, de preferência com lista de IPs permitidos, firewall ou rede privada.
- Exija **TLS verificado** para conexão remota e use a CA fornecida pelo provedor MySQL.
- Crie conta **exclusiva de leitura**; nunca disponibilize `root` ou senhas no GitHub.
- Caso use lista de IPs de saída da Streamlit Community Cloud, confira a relação **atualizada** na documentação oficial porque pode mudar: https://docs.streamlit.io/deploy/streamlit-community-cloud/status
- A publicação torna visíveis os indicadores da base a quem tiver permissão para acessar o app.

O arquivo `sql/usuario_somente_leitura.sql` contém um modelo para criar usuário MySQL com acesso SELECT; **troque a senha exemplo** e adapte o host às regras do provedor.

## Passo 2 — Configurar credenciais privadas

O aplicativo lê as variáveis `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`. Elas precisam ser definidas somente no servidor da aplicação; os visitantes **não precisam** inseri-las.

Exemplo para inserir em **Advanced settings → Secrets** da hospedagem (substitua pelas credenciais do banco remoto):

```toml
MYSQL_HOST = "endereco-do-mysql-remoto"
MYSQL_PORT = 3306
MYSQL_USER = "agile_dashboard"
MYSQL_PASSWORD = "SENHA_SEGURA_DO_USUARIO_READ_ONLY"
MYSQL_DATABASE = "analise_agil"

# Opcionalmente cole a CA do MySQL como string multilinha:
# MYSQL_SSL_CA_PEM = """-----BEGIN CERTIFICATE-----
# ...
# -----END CERTIFICATE-----"""
```

Para uma conexão TLS com certificado autenticado, defina `MYSQL_SSL_CA_PEM` com o certificado CA válido emitido para o serviço MySQL (ou `MYSQL_SSL_CA_PATH` se disponibilizado no servidor). **O aplicativo valida o certificado e a identidade do host quando a CA é configurada.** A CA é um certificado público, não uma senha e não é a chave privada do servidor.

**Nunca** inclua o arquivo real `.streamlit/secrets.toml` no GitHub. Ele está listado no `.gitignore`. O arquivo `secrets.toml.example` é apenas um modelo.

## Passo 3 — Publique o código no GitHub

1. Crie um repositório GitHub **separado para este painel Agile Scrum**.
2. Envie o conteúdo desta pasta (app.py, analytics.py, data_layer.py, requirements.txt, .streamlit/config.toml, README.md etc.).
3. Confira que `secrets.toml`, dumps SQL com informações privadas e senhas **não foram enviados**.

## Passo 4 — Implantar Streamlit Community Cloud

1. Abra https://share.streamlit.io/ e conecte sua conta GitHub.
2. Escolha **Create app / Deploy an app** e selecione o repositório e arquivo principal `app.py`.
3. Em **Advanced settings → Secrets**, cole as variáveis reais do banco remoto.
4. Conclua a implantação e abra a URL gerada (`https://...streamlit.app`).
5. Em **App settings → Sharing**, escolha **público** para compartilhar livremente o link, ou **privado** para restringir acesso às pessoas convidadas.
6. Teste a URL em outro computador/rede ou janela anônima.

Documentação oficial:

- Publicação: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- Secrets: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- Compartilhamento: https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app
- MySQL remoto: https://docs.streamlit.io/develop/tutorials/databases/mysql

## Alternativa imediata — Link temporário pela internet com o MySQL no seu PC

**Esta é a alternativa mais simples para uma apresentação pontual sem migrar o banco**. O aplicativo permanece conectado ao MySQL local no Windows, e somente a página do Streamlit é compartilhada pela internet por um túnel temporário.

1. Instale `cloudflared` (ferramenta oficial Cloudflare): https://developers.cloudflare.com/tunnel/downloads/
2. Verifique se o MySQL está funcionando e se o painel local abre em `http://localhost:8502`.
3. Deixe o Streamlit rodando. Abra **outro terminal PowerShell** e execute:

```powershell
cloudflared tunnel --url http://localhost:8502
```

4. Copie o endereço HTTPS `https://...trycloudflare.com` exibido no terminal e envie ao grupo.
5. O painel será acessível de outras redes enquanto **seu computador, Streamlit, MySQL e cloudflared** permanecerem ligados.

Este endereço é **temporário** e muda ao reiniciar o túnel. Segundo a Cloudflare, Quick Tunnels são para testes/demonstrações; não substituem uma hospedagem de produção. **Qualquer pessoa com a URL poderá ver os indicadores**, a menos que você configure restrições de acesso. Não compartilhe informações privadas sem autorização. O tunnel expõe **a interface Streamlit**, não a porta 3306 do MySQL.

Fonte: https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/

---

## Alternativa rápida — Mesmo Wi-Fi/rede local

Para um teste **somente dentro da mesma rede e com autorização do administrador da rede**, rode no seu computador:

```powershell
py -m streamlit run app.py --server.address 0.0.0.0 --server.port 8502
```

Compartilhe com quem estiver na rede o endereço `http://IP-DO-SEU-PC:8502` (substitua pelo IPv4 da máquina, disponível com `ipconfig`). O Windows Firewall pode solicitar autorização. **Seu computador e MySQL precisam permanecer ligados.** Isso não equivale a publicar para a internet, e tráfego HTTP na rede local não fornece o HTTPS da hospedagem.

## Checklist antes de compartilhar

- [ ] Painel abre sem pedir usuário/senha de MySQL.
- [ ] Acesso ao banco utiliza conta SELECT, sem privilégios de escrita.
- [ ] Schema contém as três views obrigatórias e os 238 registros de sprints originais.
- [ ] Acesso remoto possui TLS com certificado validado.
- [ ] Firewall/lista de IPs restringe o banco; não publique root na internet.
- [ ] Testei o endereço em outro dispositivo.
- [ ] Preferência público/privado foi configurada conforme o público esperado.

**Este pacote entrega o painel pronto para publicação, mas não cria automaticamente uma URL.** A URL só existe depois que a pessoa responsável fizer o deploy e conectar uma instância MySQL acessível.
