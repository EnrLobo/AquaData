# API

API REST em FastAPI. A documentação interativa, gerada automaticamente a partir do código, fica em `/docs` (Swagger) e lista todos os campos de entrada e saída:
- local: `http://localhost:8000/docs`
- produção: `https://aquadata-api.onrender.com/docs` (a primeira requisição depois de 15 minutos parada leva cerca de um minuto)

Este documento resume as rotas e as regras que o Swagger não mostra.

## Convenções

- Corpo e respostas em JSON, exceto o login (formulário) e a planilha (CSV).
- **Autenticação:** todas as rotas, exceto `/health`, `/auth/register` e `/auth/login`, exigem o cabeçalho `Authorization: Bearer <token>`.
- **Isolamento:** cada treinador só enxerga os próprios atletas e registros. Atleta de outro treinador responde **404**, como se não existisse.
- **Datas** no formato `AAAA-MM-DD`; **tempos** em segundos com duas casas (`64.62`).
- **Valores fixos:**
  - `stroke` (nado): `freestyle`, `backstroke`, `breaststroke`, `butterfly`, `medley`
  - `session_type` (tipo): `training`, `competition`
  - `sex`: `M`, `F`
  - `pool_length_m` (piscina): `25` ou `50`
- **Paginação:** `limit` e `offset`.

## Códigos de resposta

| Código | Quando |
|---|---|
| 200 / 201 / 204 | Sucesso (201 na criação; 204 na exclusão, sem corpo) |
| 401 | Sem token, token inválido ou expirado ("Credenciais inválidas ou token expirado"); login com e-mail ou senha incorretos |
| 404 | Atleta ou registro inexistente, ou de outro treinador |
| 409 | Conflito: e-mail já cadastrado; atleta repetido (mesmo nome e nascimento); registro em atleta inativo |
| 422 | Dados inválidos (validação do Pydantic) ou período com data inicial depois da final |

## Saúde

| Método | Rota | Descrição |
|---|---|---|
| GET | `/health` | Verificação de funcionamento (usada pelo health check do Render) |

## Autenticação

| Método | Rota | Descrição |
|---|---|---|
| POST | `/auth/register` | Cadastra treinador: `name` (2 a 120 caracteres), `email`, `password` (8 a 128). E-mail guardado em minúsculas |
| POST | `/auth/login` | Formulário (`application/x-www-form-urlencoded`) com `username` (= e-mail) e `password`; devolve `access_token` (JWT, 60 minutos) e `token_type` |
| GET | `/auth/me` | Dados do treinador logado (a senha nunca é devolvida) |

## Atletas

| Método | Rota | Descrição |
|---|---|---|
| POST | `/athletes` | Cadastra atleta: `name`, `birth_date` (não futura), `sex` |
| GET | `/athletes` | Lista em ordem alfabética. Filtros: `active` (true/false), `search` (parte do nome, sem diferenciar maiúsculas), `limit` (até 100, padrão 50), `offset` |
| GET | `/athletes/{id}` | Um atleta |
| PATCH | `/athletes/{id}` | Altera um ou mais campos, inclusive `active`. Corpo vazio ou com nulos → 422 |

Não há exclusão de atleta: para "excluir", inativar com `{"active": false}`. Atleta inativo continua com o histórico, mas não recebe registros novos.

## Registros de treino e competição

| Método | Rota | Descrição |
|---|---|---|
| POST | `/athletes/{id}/sessions` | Cria registro (atleta inativo → 409) |
| GET | `/athletes/{id}/sessions` | Registros do atleta, do mais recente ao mais antigo. Filtros: `session_type`, `stroke`, `date_from`, `date_to`, `limit` (até 200, padrão 50), `offset` |
| GET | `/athletes/{id}/sessions/{sid}` | Um registro |
| PUT | `/athletes/{id}/sessions/{sid}` | Substitui o registro inteiro (mesmos campos e validações da criação) |
| DELETE | `/athletes/{id}/sessions/{sid}` | Exclui o registro |
| GET | `/sessions` | Todos os registros do treinador, com `athlete_name`. Filtros: `athlete_id`, `search` (nome do atleta), `session_type`, `stroke`, `date_from`, `date_to`, `limit` (até 200, padrão 10), `offset`. Resposta: `{items, total, limit, offset}` |

Campos do registro:

| Campo | Descrição |
|---|---|
| `session_date` | Data (não futura) |
| `session_type`, `stroke`, `pool_length_m` | Tipo, nado e piscina |
| `distance_m` | Distância total; múltipla do tamanho da piscina |
| `total_time_s` | Tempo total |
| `swim_distance_m`, `swim_time_s` | Trecho de nado puro (entre as bandeirolas); não podem passar da distância e do tempo totais |
| `stroke_count` | Ciclos de braçada no trecho de nado puro |
| `total_cycle_count` | Ciclos de braçada na prova completa (≥ ciclos do trecho) |
| `notes` | Observações (até 1000 caracteres) |

Velocidades acima de 3 m/s (total ou no trecho) são recusadas como erro de digitação. A resposta traz o objeto `metrics` (`vm`, `vn`, `cb`, `cn`, `swim_index`, `swolf`, `swolf_25`), calculado na consulta.

## Painel

| Método | Rota | Descrição |
|---|---|---|
| GET | `/dashboard` | Numa chamada: atletas ativos, total de registros e dos últimos 30 dias, atletas sem registro há 30 dias, 5 últimos registros, 6 atletas pelo último registro e `predictions` (uma por atleta ativo e prova com 6 ou mais registros: próximo treino e competição, variação por registro, selo, MAE, `is_main` para a prova principal). Também `min_trend_records` e `athletes_without_prediction` |

## Desempenho e predição

| Método | Rota | Descrição |
|---|---|---|
| GET | `/athletes/{id}/performance` | Registros filtrados em ordem cronológica, com resumo e tendência por métrica. Filtros: `stroke` (sem ele, o nado mais frequente), `distance_m`, `pool_length_m`, `session_type`, `date_from`, `date_to`. Até 500 registros mais recentes (`truncated` avisa) |
| GET | `/athletes/{id}/prediction` | Parâmetros obrigatórios: `stroke`, `distance_m`, `pool_length_m`. Usa todo o histórico da prova. Devolve previsão do próximo treino e competição, coeficientes, R², avaliação treino/teste (MAE, MAPE, RMSE e tabela previsto × real), histórico, reta do modelo com 3 registros futuros e séries das métricas. Com menos de 6 registros: `available: false` e a mensagem do mínimo (não é erro HTTP) |

## Relatórios

| Método | Rota | Descrição |
|---|---|---|
| GET | `/athletes/{id}/report` | Relatório consolidado: atleta, período coberto, totais e um bloco por prova (tempos, métricas, previsão e pontos do gráfico). Filtros: `date_from`, `date_to` |
| GET | `/athletes/{id}/report/csv` | Planilha com os registros do período e as métricas: `;` entre colunas, vírgula decimal, UTF-8 com BOM; arquivo `relatorio-<nome>-<data>.csv` |

Regra do período: o período filtra registros, tempos, métricas e pontos do gráfico; **previsão, selo e reta do modelo usam sempre todo o histórico** da prova, como no painel e no Desempenho.