# Guia de desenvolvimento

Como dar continuidade ao projeto: fluxo de trabalho, padrões, implantação e problemas já conhecidos. Para rodar localmente, ver o [README](../README.md).

## Fluxo de trabalho

O projeto foi conduzido com Scrum (sprints de duas semanas), com as tarefas no Jira (chave `AQ`). Cada ticket vira uma branch e um Pull Request.

1. **Criar a branch** a partir da `main` do repositório remoto, com a chave do ticket no nome:
   ```powershell
   git fetch origin
   git switch -c feat/AQ-N-descricao origin/main
   ```
   Prefixos: `feat/` (funcionalidade), `fix/` (correção), `test/`, `docs/`, `chore/`.
2. **Desenvolver e testar** (seção "Antes do Pull Request").
3. **Adicionar os arquivos pelo nome** (`git add caminho/do/arquivo`), nunca `git add .`, para não enviar arquivos locais, segredos ou dados por engano. Conferir com `git diff --cached --stat`.
4. **Commit** no padrão Conventional Commits, com a chave do ticket: `feat(AQ-N): descrição`, `fix(AQ-N): ...`, `test(AQ-N): ...`, `docs(AQ-N): ...`.
5. **Pull Request** revisado pelo outro integrante; o GitHub Actions roda os testes automaticamente.
6. **Squash and merge**, editando o título do squash para o mesmo padrão do commit.
7. Depois do merge, **Sync fork** no fork lido pelo Render (seção "Implantação").

Mudanças pedidas depois do merge vão numa branch nova (`fix/...`). Quando uma versão já validada recebe alteração no mesmo ticket, fazer o commit dela antes, para cada versão ficar no histórico.

## Antes do Pull Request

Na pasta `backend`, com o venv ativo:

```powershell
python -m pytest -rs
```

Com migration nova: `alembic upgrade head`, `alembic downgrade -1` e `alembic upgrade head`.

Na pasta `frontend`:

```powershell
npm run lint
npm run build
```

E testar a funcionalidade no navegador (`http://localhost:5173`). Para mudanças grandes, seguir o roteiro de ponta a ponta em [testes/README.md](testes/README.md).

## Padrões de código

**Backend**
- Rotas finas: a regra de negócio fica em `services/`, em funções puras (sem banco nem HTTP), e ganha testes unitários.
- Toda consulta de dados do treinador filtra pelo treinador logado; nas rotas de um atleta, usar a dependência `OwnedAthlete` (`api/deps.py`), que já responde 404 para atleta de outro treinador.
- Validação de entrada nos esquemas Pydantic (`schemas/`); validações que envolvem vários campos em `model_validator`.
- Mensagens de erro e textos para o usuário em português.
- Constantes de regra (mínimos, faixas) com nome e comentário explicando a origem (decisão da equipe, fonte ou estudo).

**Frontend**
- Chamadas à API só por `services/` (nunca `fetch` direto nas telas).
- Cores pelas variáveis semânticas do tema (`bg-surface`, `text-fg`, `text-muted`...), nunca cores fixas, para funcionar no tema claro e no escuro.
- Componentes básicos em `components/ui/`; reutilizar antes de criar.
- Acessibilidade: cor nunca é o único indicador (seta e texto junto), rótulos em campos e botões de ícone (`aria-label`), foco visível.
- Filtros das telas de análise guardados na URL, para o link poder ser compartilhado.

**Testes**
- Unitários: `backend/tests/test_*.py`, valores esperados calculados à mão e comentados no teste.
- Integração: `backend/tests/integration/`, passando pela API e por um banco PostgreSQL de teste (detalhes em [testes/README.md](testes/README.md)).

## Implantação

| Serviço | Origem | Configuração |
|---|---|---|
| Vercel (frontend) | Repositório principal, pasta `frontend` | Variável `VITE_API_URL` (endereço da API, sem barra no final). Mudou a variável, refazer o deploy |
| Render (API) | **Fork** `EnrLobo/AquaData`, branch `main`, pasta `backend` | Web service Python, instância Free. Build: `pip install -r requirements.txt`. Início: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Health check: `/health`. Variáveis: `PYTHON_VERSION` (`3.13`), `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS` (lista JSON com o endereço do frontend, sem barra no final) |
| Neon (banco) | PostgreSQL 18 gerenciado, plano Free | Região AWS US East 1 (N. Virginia), a mesma região do Render. `DATABASE_URL` = connection string **direta** (sem pooler), com `sslmode=require`. Mesma versão do ambiente local e do GitHub Actions |

O Render lê o fork porque o integrante que o configurou é colaborador, e não dono, do repositório principal. Por isso, **depois de cada merge**, é preciso fazer o Sync fork no GitHub para a API ser atualizada.

Limites do plano gratuito: a API desliga depois de 15 minutos sem requisições e leva cerca de um minuto para voltar (abrir o sistema alguns minutos antes de uma demonstração); 750 horas de instância por mês no Render; 1 GB de armazenamento e 100 horas de computação por mês no Neon.

**Histórico:** até novembro de 2026, API e banco ficavam na Railway (com `railpack.json` e pré-deploy configurado no painel). O período de teste expirou, as implantações foram pausadas e a equipe migrou para Render e Neon, mantendo tudo gratuito. Como o banco de produção só tinha contas de teste, os dados não foram migrados.

**Segredos:** `.env`, `SECRET_KEY`, senhas e tokens nunca vão para o Git, para prints ou para mensagens. Se algum vazar, gerar um novo valor e trocar no Render (`SECRET_KEY`) ou no Neon (senha do banco). O repositório é público: dados reais de atletas e vídeos de terceiros também não entram nele.

## Problemas conhecidos e soluções

| Problema | Solução |
|---|---|
| Frontend em `127.0.0.1:5173` recebe erro de CORS | Abrir `http://localhost:5173` (a origem liberada) |
| Login funciona local e falha em produção | Os bancos são independentes: cadastrar o treinador também em produção |
| Primeira requisição em produção demora cerca de um minuto | Comportamento do plano gratuito do Render (o serviço desliga sem uso); esperar ou abrir antes |
| Erro de conexão com o Neon por SSL | Manter `sslmode=require` na `DATABASE_URL` e usar a connection string direta, sem pooler |
| Render instala outra versão do Python | Definir a variável `PYTHON_VERSION=3.13` |
| PostgreSQL local e Docker disputando a porta 5432 | Usar só um deles; conferir com `select version()` em qual banco a migration caiu |
| `pip freeze > arquivo` gera arquivo ilegível no PowerShell | Usar `pip freeze \| Set-Content -Encoding ascii requirements.txt` |
| Script com `--csv arquivo.csv` dá "expected one argument" | Usar `--csv=arquivo.csv` |
| CSV aberto no Excel em português com números errados | Gravar com `;` entre colunas, vírgula decimal e UTF-8 com BOM (padrão dos scripts e da exportação) |
| Enum gravado como `FREESTYLE` em vez de `freestyle` | Usar `values_callable=enum_values` nos modelos |
| Migration com `NOT NULL` falha em tabela com dados | Criar a coluna como nula ou com valor padrão |
| Pydantic devolve `Decimal` como texto | Converter para `float` nos esquemas de saída |
| Gráfico em branco no PDF exportado | A página assume a largura da folha A4 e espera os gráficos se redesenharem antes de abrir a impressão (`ReportPage.jsx`) |
| GitHub Actions sem `pytest` | Dependências de teste ficam em `backend/requirements-dev.txt`, separadas do deploy |

## Melhorias futuras já identificadas

- Guardar o token em cookie `HttpOnly` e adicionar renovação de token.
- Restringir o cadastro de treinadores (convite ou aprovação).
- Testes automatizados de ponta a ponta no navegador (ex.: Playwright).
- Divisão do código do frontend por rota (o build avisa sobre o tamanho do pacote).
- Modelos de predição não lineares ou com janela dos registros mais recentes (a reta superestima a melhora quando o atleta estabiliza).
- Intervalo de confiança na previsão.
- SWOLF no medley.
- Renomear a coluna `stroke_count` para `cycle_count` (ela guarda ciclos, não braçadas).