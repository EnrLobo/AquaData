# Regras de negócio e cálculos

Todas as regras abaixo estão em funções puras em `backend/app/services/`, cobertas por testes unitários em `backend/tests/`.

## 1. Registro de treino

- Cada registro é **um esforço medido** (um tiro ou uma prova) dentro do dia, de treino ou de competição.
- **Ciclo de braçada:** os dois braços juntos contam 1 ciclo.
- **Trecho de nado puro:** entre as bandeirolas, 5 m de cada borda (por extensão: piscina − 10 m, ou seja, 15 m em piscina de 25 m e 40 m em piscina de 50 m). Exclui saída e viradas. O formulário aceita os dados **por extensão** (soma sozinho) ou **totais**; a API guarda só os totais.
- **Duas contagens de ciclos:** no trecho de nado puro (base de VN, CB, cadência e IN) e na prova completa (base do SWOLF).

Validações (`schemas/session.py`):
- distância total múltipla do tamanho da piscina;
- trecho de nado puro menor ou igual à distância e ao tempo totais;
- ciclos da prova maiores ou iguais aos ciclos do trecho;
- velocidade (total e do trecho) até 3 m/s; acima disso é erro de digitação (os recordes ficam perto de 2,4 m/s);
- data não futura.

## 2. Métricas (`services/metrics.py`)

| Métrica | Fórmula | Unidade | Casas |
|---|---|---|---|
| Vm (velocidade média) | distância total ÷ tempo total | m/s | 2 |
| VN (velocidade de nado) | distância do trecho ÷ tempo do trecho | m/s | 2 |
| CB (comprimento de braçada) | distância do trecho ÷ ciclos do trecho | m/ciclo | 2 |
| Cadência | ciclos do trecho ÷ tempo do trecho × 60 | ciclos/min | 1 |
| IN (índice de nado) | CB × VN | m²/s | 2 |
| SWOLF | tempo total (s) + braçadas da prova completa | adimensional | 1 |
| SWOLF a cada 25 m | SWOLF × 25 ÷ distância total | adimensional | 1 |

- **Braçadas para o SWOLF:** crawl e costas = ciclos × 2 (braços alternados); peito e borboleta = ciclos × 1 (braços simultâneos). **Medley:** SWOLF não calculado.
- O arredondamento é feito só no resultado final.
- Uma métrica sem divisão possível (ex.: zero ciclos) volta nula, sem derrubar a listagem.
- Coerência verificada em teste: VN = CB × cadência ÷ 60.

Exemplo de referência (usado nos testes e na validação): 100 m livre em 60 s; trecho de 60 m em 40 s com 40 ciclos; 50 ciclos na prova → Vm 1,67; VN 1,50; CB 1,50; cadência 60,0; IN 2,25; SWOLF 160,0; SWOLF a cada 25 m 40,0.

## 3. Tendência na tela Desempenho (`services/performance.py`)

- Reta de **regressão linear por mínimos quadrados** sobre a ordem dos registros do **período filtrado** (y = a + b·x, x = posição na série); devolve a inclinação (variação por registro) e o R².
- **A partir de 3 registros:** linha tracejada e valor da variação (`MIN_TREND_POINTS`).
- **A partir de 10 registros com valor:** seta, cor e texto de melhora ou piora (`MIN_CONCLUSIVE_POINTS`, campo `conclusive`). Abaixo disso, "poucos treinos para indicar tendência (N de 10)".
- O sentido de melhora depende da métrica (tempo e SWOLF: menor é melhor; velocidades, CB e IN: maior é melhor; cadência: sem juízo de melhora).
- A decisão usa a inclinação, não o primeiro e o último valor: um registro atípico no fim não inverte a leitura.

## 4. Predição do tempo (`services/prediction.py`)

**Modelo:** um por atleta e por prova (mesmo nado, distância e piscina), ajustado com `LinearRegression` do scikit-learn:

```
tempo = b0 + b1 · ordem + b2 · competição
```

- `ordem` = posição do registro na série (1, 2, 3...); `competição` = 1 para competição, 0 para treino.
- `b1` = variação do tempo a cada novo registro; `b2` = diferença entre competição e treino. A variável competição só entra quando há treinos e competições na prova.
- Métricas de nado não entram como variáveis de entrada, porque não são conhecidas antes do próximo registro.

**Constantes:**

| Constante | Valor | Significado |
|---|---|---|
| `MIN_RECORDS` | 6 | Registros na prova para haver previsão (4 de treino + 2 de teste) |
| `TEST_FRACTION` | 0,2 | Últimos 20% dos registros vão para o teste (mínimo 2) |
| `FUTURE_STEPS` | 3 | Registros futuros projetados no gráfico ("Próx. 1, 2, 3", sem datas) |
| `MIN_TREND_RECORDS` | 10 | Registros para exibir o selo de tendência |
| `STABLE_BAND_PCT` | 0,2 | Faixa de estabilidade do selo, em % do último tempo |

**Avaliação:** divisão **temporal** (os registros mais antigos ajustam o modelo; os mais recentes testam). Medidas: MAE (segundos) e MAPE (%), além de RMSE e R². Depois da avaliação, a previsão final usa **todo o histórico**. A avaliação só é feita para o tempo; nas outras métricas, a reta projetada é apoio visual (mesmo modelo, mínimo de 6 registros com valor).

**Outros detalhes:** previsão menor ou igual a zero é descartada; o modelo não é guardado (é ajustado a cada consulta).

## 5. Selo de tendência no Início

1. variação % = b1 ÷ último tempo × 100;
2. ≤ −0,2% → **Melhorando**; ≥ +0,2% → **Atenção**; entre os dois → **Estável**;
3. só a partir de **10 registros** na prova; com 6 a 9, "Poucos registros (N de 10)".

- Usar a porcentagem põe provas curtas e longas na mesma escala.
- Ordem da lista: Atenção → Estável → Melhorando → poucos registros.
- O R² é exibido como informação, mas não entra na regra.
- **Prova principal** de cada atleta: a mais registrada entre as que têm 6 ou mais registros (desempate pelo registro mais recente).

O mínimo de 10 registros e a exclusão do R² da regra vêm de um estudo de simulação (`scripts/simulate_record_count.py`): com 10 registros, o selo acertou de 70% a 78% das séries com ruído típico de nadadores, e a confusão entre melhora e piora praticamente desapareceu.

## 6. Relatórios (`services/report.py`)

- Um bloco por prova do atleta com registros no período, ordenados pela quantidade de registros (desempate pela mais recente).
- O período filtra registros, tempos, métricas e pontos do gráfico; **previsão, selo e reta do modelo usam todo o histórico** da prova.
- Melhor tempo: em caso de empate, o mais antigo.
- Planilha CSV: 19 colunas (dados medidos e métricas), padrão brasileiro (`;`, vírgula decimal, UTF-8 com BOM, tempo também em `m:ss,cc`).

## 7. Estudos e validação

| Script | O que faz |
|---|---|
| `scripts/simulate_prediction.py` | Simula atletas com comportamento conhecido e ruído do tamanho da variação real de nadadores, e mede se o modelo recupera a tendência (8 cenários) |
| `scripts/simulate_record_count.py` | Mede a confiabilidade do selo conforme o número de registros (6 a 20) e compara três regras |
| `scripts/seed_simulated.py` | Cria atletas simulados para demonstração, só no banco local |
| `scripts/validate_metrics.py` | Compara as métricas do sistema com o cálculo manual feito com dados reais (protocolo em `docs/validacao/README.md`) |

Rodar na pasta `backend`, com o venv ativo: `python -m scripts.<nome> --help`.