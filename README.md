# aquaData

Sistema web de análise de performance de atletas de natação. O treinador cadastra atletas e registra treinos e competições; o sistema calcula métricas de nado, mostra a evolução de cada atleta, prevê o tempo do próximo registro por Regressão Linear e gera relatórios exportáveis.

Trabalho de Conclusão de Curso de Sistemas de Informação (IFSULDEMINAS, campus Machado), de Enrique Rocha Lobo da Silva e João Henrique Souza Almeida.

- Frontend: https://aqua-data-u1mo.vercel.app
- API (documentação interativa): https://aquadata-api.onrender.com/docs (no plano gratuito, a primeira requisição depois de 15 minutos parada leva cerca de um minuto)

## Funcionalidades

| Tela | O que faz |
|---|---|
| Início | Resumo do treinador, últimos treinos e previsões por atleta com selo de tendência (Melhorando, Estável, Atenção) |
| Atletas | Cadastro, edição, busca e inativação de atletas |
| Treinos | Registro de treinos e competições (trecho de nado puro por extensão ou totais), lista com filtros e detalhes com as métricas |
| Desempenho | Evolução de cada métrica por atleta e prova, com linha de tendência e previsão do próximo registro |
| Relatórios | Visão consolidada de todas as provas do atleta num período, exportação em PDF (impressão do navegador) e planilha CSV |

Métricas calculadas: velocidade média (Vm), velocidade de nado (VN), comprimento de braçada (CB), cadência, índice de nado (IN), SWOLF e SWOLF a cada 25 m. As fórmulas estão em [docs/regras-e-calculos.md](docs/regras-e-calculos.md).

## Tecnologias

| Camada | Tecnologias |
|---|---|
| Frontend | React 19, Vite 8, Tailwind CSS 4, React Router 7, Recharts 3, lucide-react |
| Backend | Python 3.13, FastAPI, SQLAlchemy 2, Alembic, Pydantic 2, PyJWT, pwdlib (Argon2), scikit-learn, NumPy, SciPy |
| Banco | PostgreSQL 18 |
| Testes | pytest (unitários e de integração com PostgreSQL), oxlint, GitHub Actions |
| Hospedagem | Vercel (frontend), Render (API) e Neon (banco PostgreSQL), todos no plano gratuito |

## Estrutura do repositório

```
AquaData/
├── backend/             API FastAPI
│   ├── app/
│   │   ├── api/         rotas (uma por recurso)
│   │   ├── core/        configuração, banco, segurança
│   │   ├── models/      tabelas (SQLAlchemy)
│   │   ├── schemas/     entrada e saída da API (Pydantic)
│   │   └── services/    regras de negócio em funções puras
│   ├── alembic/         migrations
│   ├── scripts/         estudos de simulação, carga de dados simulados, validação
│   └── tests/           testes unitários e de integração
├── frontend/            aplicação React
│   └── src/
│       ├── pages/       telas
│       ├── components/  componentes (ui/ = componentes básicos)
│       ├── services/    chamadas à API
│       ├── context/     autenticação e tema
│       └── utils/       formatação e definições das métricas
├── docs/                documentação técnica
└── .github/workflows/   integração contínua
```

## Como rodar localmente

Pré-requisitos: Python 3.13, Node.js 22 e PostgreSQL 18. Os comandos abaixo são para PowerShell (Windows).

### 1. Banco

Criar no PostgreSQL um usuário `aquadata` e os bancos `aquadata` (desenvolvimento) e, para os testes de integração, `aquadata_test`.

### 2. Backend

Na pasta `backend`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Editar o `.env` (variáveis na tabela abaixo) e criar as tabelas:

```powershell
alembic upgrade head
fastapi dev app/main.py
```

A API fica em `http://localhost:8000` e a documentação interativa em `http://localhost:8000/docs`.

| Variável | Obrigatória | Descrição |
|---|---|---|
| `DATABASE_URL` | Sim | Conexão com o banco, ex.: `postgresql+psycopg://aquadata:SENHA@localhost:5432/aquadata` (`postgresql://` também é aceito e convertido) |
| `SECRET_KEY` | Sim | Chave de assinatura dos tokens JWT; gerar com `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `CORS_ORIGINS` | Não | Lista JSON das origens do frontend; padrão `["http://localhost:5173"]` |
| `TEST_DATABASE_URL` | Só para testes | Banco dos testes de integração; o nome precisa terminar em `_test` |

### 3. Frontend

Na pasta `frontend`:

```powershell
npm install
Copy-Item .env.example .env
npm run dev
```

Abrir `http://localhost:5173` (use `localhost`, não `127.0.0.1`, por causa do CORS). A variável `VITE_API_URL` aponta para a API (padrão `http://localhost:8000`).

### Dados simulados (opcional, só no banco local)

Depois de criar uma conta pela tela de cadastro, na pasta `backend`:

```powershell
python -m scripts.seed_simulated --email SEU_EMAIL
```

## Testes

Na pasta `backend`, com o venv ativo:

```powershell
python -m pytest -rs
```

Sem `TEST_DATABASE_URL`, os testes de integração são pulados e os unitários rodam normalmente. No frontend: `npm run lint` e `npm run build`. Detalhes em [docs/testes/README.md](docs/testes/README.md).

## Documentação

| Documento | Conteúdo |
|---|---|
| [docs/arquitetura.md](docs/arquitetura.md) | Visão geral, camadas, autenticação e implantação |
| [docs/api.md](docs/api.md) | Rotas da API, parâmetros e respostas de erro |
| [docs/banco-de-dados.md](docs/banco-de-dados.md) | Tabelas, restrições e migrations |
| [docs/regras-e-calculos.md](docs/regras-e-calculos.md) | Métricas, tendência, modelo de predição, selo e relatórios |
| [docs/desenvolvimento.md](docs/desenvolvimento.md) | Fluxo de trabalho, padrões, implantação e problemas conhecidos |
| [docs/testes/README.md](docs/testes/README.md) | Camadas de teste e roteiro de ponta a ponta |
| [docs/validacao/README.md](docs/validacao/README.md) | Protocolo de validação das métricas com dados reais |

## Limitações conhecidas

- Token JWT guardado no `localStorage` (vulnerável a XSS) e sem renovação automática (expira em 60 minutos).
- Cadastro de treinador aberto a qualquer pessoa.
- Previsão por Regressão Linear: supõe evolução aproximadamente linear, usa a ordem dos registros (não o intervalo de dias) e não exibe intervalo de confiança.
- SWOLF não calculado no medley.
- Exportação em PDF depende da impressão do navegador.
- Hospedagem gratuita: a API desliga depois de 15 minutos sem uso e leva cerca de um minuto para voltar.