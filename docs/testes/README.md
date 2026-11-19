# Testes do aquaData

O sistema é verificado em quatro camadas:

| Camada | O que verifica | Onde | Como roda |
|---|---|---|---|
| Testes unitários | Funções puras: fórmulas das métricas, tendência, modelo de predição, simulação, relatório e planilha | `backend/tests/test_*.py` | `pytest`, sem banco |
| Testes de integração | API de verdade + banco PostgreSQL: autenticação, isolamento entre treinadores, validações, gravação, métricas na consulta, previsão, painel, desempenho, relatório, planilha, regras do banco e migrations | `backend/tests/integration/` | `pytest`, com banco de teste |
| Integração contínua (CI) | Os dois tipos acima, mais lint e build do frontend, a cada Pull Request | `.github/workflows/tests.yml` | GitHub Actions |
| Roteiro de ponta a ponta | Frontend + backend + banco pelo navegador, como o treinador usa | Este arquivo (seção 3) | Manual, com prints |

## 1. Testes unitários

Na pasta `backend`, com o venv ativo:

```powershell
python -m pytest --ignore=tests/integration
```

## 2. Testes de integração

As requisições passam pela API (rotas, validação, token JWT, isolamento por treinador) e gravam num **banco PostgreSQL separado**, criado pelas próprias migrations do Alembic. A cada execução, o banco de teste é apagado e recriado, e as migrations sobem, descem e sobem de novo (o que confirma que são reversíveis).

### Preparar uma vez

1. Criar o banco `aquadata_test` no PostgreSQL local, com o mesmo usuário do banco de desenvolvimento (pelo pgAdmin: *Databases → Create → Database*, nome `aquadata_test`, dono `aquadata`).
2. Acrescentar ao `backend/.env` a linha abaixo, com a mesma porta e senha do `DATABASE_URL`, trocando só o nome do banco:

```
TEST_DATABASE_URL=postgresql+psycopg://aquadata:SENHA@localhost:PORTA/aquadata_test
```

O nome do banco **precisa terminar em `_test`**: é uma trava para nunca apagar o banco de desenvolvimento por engano.

### Rodar

Na pasta `backend`, com o venv ativo:

```powershell
python -m pytest -rs
```

Sem `TEST_DATABASE_URL`, os testes de integração aparecem como *skipped* (pulados) e os unitários rodam normalmente. No GitHub Actions, a falta da variável é erro.

## 3. Roteiro de ponta a ponta (manual)

Executar pelo navegador, primeiro no ambiente local e, depois, em produção (Vercel + Railway). Para cada passo, marcar o resultado e guardar um print em `docs/img/` (nome sugerido: `e2e-E01.png`, `e2e-E02.png`...).

**Dados usados:**
- local: os atletas simulados (`python -m scripts.seed_simulated --email SEU_EMAIL`) e um atleta cadastrado à mão;
- produção: só dados cadastrados à mão (dados simulados não vão para produção).

**Valores de referência para conferir as métricas (E07):** 100 m livre, piscina de 25 m, tempo 1:00,00; trecho de nado puro de 60 m em 40,00 s com 40 ciclos; 50 ciclos na prova completa → Vm 1,67 m/s; VN 1,50 m/s; CB 1,50 m; cadência 60,0 ciclos/min; IN 2,25 m²/s; SWOLF 160,0; SWOLF a cada 25 m 40,0.

| Nº | Passo | Resultado esperado | Local | Produção |
|---|---|---|---|---|
| E01 | Cadastrar treinador na tela "Cadastre-se" | Conta criada e Início aberto | | |
| E02 | Sair e entrar de novo; tentar senha errada | Login abre o Início; senha errada mostra "E-mail ou senha incorretos" | | |
| E03 | Sem estar logado, abrir `/atletas` pela barra de endereço | Redireciona para o login | | |
| E04 | Cadastrar atleta; tentar o mesmo nome e nascimento de novo | Atleta na lista; repetição recusada com mensagem | | |
| E05 | Buscar o atleta pelo nome; inativar; filtrar inativos; reativar | Busca, filtro e inativação refletem na lista sem recarregar | | |
| E06 | Registrar treino por extensão (4 × 25 m) | Formulário soma tempo e ciclos do trecho; treino aparece em Treinos | | |
| E07 | Abrir os detalhes do treino com os valores de referência | Métricas iguais aos valores de referência | | |
| E08 | Tentar treino inválido (ex.: 110 m em piscina de 25 m) | Mensagem de erro; nada gravado | | |
| E09 | Editar o tempo do treino; excluir um treino | Métricas recalculadas; treino excluído some da lista | | |
| E10 | Lista de Treinos: busca, filtros e paginação | Resultados e contagem coerentes | | |
| E11 | Desempenho de um atleta com 12 registros | Gráfico de tempo com reta do modelo e área "Previsão"; cartões com seta e tendência; painel de previsão com MAE | | |
| E12 | Desempenho de um atleta com 6 a 9 registros | Previsão aparece; cartões mostram "poucos treinos (N de 10)" | | |
| E13 | Início: seção Previsões | Selos Melhorando/Estável/Atenção; "Poucos registros (N de 10)" por último; "Ver gráfico" abre o Desempenho filtrado | | |
| E14 | Relatórios: atleta com mais de uma prova, períodos "Tudo" e "30 dias" | Um bloco por prova; números mudam com o período; previsão não muda | | |
| E15 | Exportar PDF (tema claro e escuro) | Cabeçalho com logo, treinador, data e aviso; gráficos visíveis; sem menu e filtros; sempre claro | | |
| E16 | Baixar planilha (CSV) e abrir no Excel ou Planilhas Google | Acentos corretos, vírgula decimal, uma informação por coluna | | |
| E17 | Com um segundo treinador, tentar abrir pela URL um atleta do primeiro | Mensagem de atleta não encontrado; nada do primeiro treinador aparece | | |
| E18 | Alternar tema claro/escuro e abrir no celular (ou janela estreita) | Tema salvo ao recarregar; menu horizontal no celular | | |

Resultado: preencher com **OK** ou **Falhou** (descrevendo o que aconteceu). Falhas viram ticket de correção (`fix/...`).