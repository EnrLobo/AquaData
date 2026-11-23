# Validação das métricas com dados reais (AQ-25)

Objetivo: confirmar, com registros medidos no clube parceiro, que o sistema calcula as métricas corretamente e medir quanto tempo ele economiza em relação ao cálculo à mão.

Dois resultados:
1. **Correção:** as métricas do sistema coincidem com as calculadas à mão (dentro da tolerância de arredondamento).
2. **Tempo:** quanto tempo o treinador gasta calculando à mão e quanto gasta cadastrando o mesmo registro no sistema.

## 1. Antes da coleta

- [ ] Autorização dos atletas (e dos responsáveis, se houver menores).
- [ ] Atletas cadastrados no sistema em produção, com nomes reais.
- [ ] Material: cronômetro (ou celular), prancheta com a ficha de coleta, celular para filmar (opcional, para recontar depois), calculadora para o cálculo manual.
- [ ] Bandeirolas da piscina (5 m de cada borda) visíveis para marcar o trecho de nado puro.

## 2. Coleta na piscina

Para cada registro (um tiro ou prova), anotar na ficha:

| Dado | Como medir |
|---|---|
| Nado, distância e piscina | Ex.: livre, 100 m, piscina de 25 m |
| Tempo total | Do sinal de saída ao toque final |
| Trecho de nado puro (m) | Entre as bandeirolas: 15 m por extensão em piscina de 25 m (40 m em 50 m); somar as extensões medidas |
| Tempo do trecho (s) | Soma dos tempos entre as bandeirolas |
| Ciclos no trecho | Ciclos de braçada entre as bandeirolas (os dois braços = 1 ciclo) |
| Ciclos na prova | Ciclos de braçada da prova completa |

Se possível, filmar o tiro para recontar os ciclos depois e conferir erros de contagem.

## 3. Os dois procedimentos cronometrados

Os dois partem da **mesma ficha preenchida**. Cronometrar cada um separadamente:

1. **Cálculo manual:** o treinador calcula as 7 métricas com a calculadora, usando as fórmulas da seção 4, e anota os resultados. O cronômetro começa quando ele pega a ficha e para quando a última métrica está anotada.
2. **Cadastro no sistema:** alguém cadastra o registro na tela de novo treino (`/treinos/novo`). O cronômetro começa ao abrir o formulário e para quando o treino aparece salvo com as métricas.

Para não favorecer nenhum lado, alternar a ordem (em metade dos registros, fazer primeiro o cálculo manual; na outra metade, primeiro o sistema), e a pessoa que calcula à mão não deve ver as métricas do sistema antes de terminar.

## 4. Fórmulas para o cálculo manual

| Métrica | Fórmula | Casas |
|---|---|---|
| Vm (m/s) | distância total ÷ tempo total | 2 |
| VN (m/s) | trecho (m) ÷ tempo do trecho (s) | 2 |
| CB (m por ciclo) | trecho (m) ÷ ciclos no trecho | 2 |
| Cadência (ciclos/min) | ciclos no trecho ÷ tempo do trecho × 60 | 1 |
| IN (m²/s) | CB × VN | 2 |
| SWOLF | tempo total (s) + braçadas da prova (crawl e costas: ciclos × 2; peito e borboleta: ciclos × 1; medley: não calcular) | 1 |
| SWOLF a cada 25 m | SWOLF × 25 ÷ distância total | 1 |

Exemplo para conferir: 100 m livre em 1:00,00; trecho de 60 m em 40,00 s com 40 ciclos; 50 ciclos na prova → Vm 1,67; VN 1,50; CB 1,50; cadência 60,0; IN 2,25; SWOLF 160,0; SWOLF a cada 25 m 40,0.

## 5. Planilha da coleta

Uma linha por registro, no Excel ou Planilhas Google, salva como **CSV UTF-8** com `;` separando as colunas (padrão do Excel em português). A primeira linha deve ser exatamente o cabeçalho abaixo:

```
registro;atleta;nado;distancia_m;piscina_m;tempo_total;trecho_m;trecho_s;ciclos_trecho;ciclos_prova;vm_manual;vn_manual;cb_manual;cadencia_manual;in_manual;swolf_manual;swolf25_manual;tempo_calculo_manual;tempo_cadastro_sistema
```

| Coluna | Exemplo | Observação |
|---|---|---|
| `registro` | R01 | Identificação do registro |
| `atleta` | Nome do atleta | Fica só na planilha local |
| `nado` | livre | livre, costas, peito, borboleta ou medley |
| `distancia_m`, `piscina_m` | 100; 25 | Metros |
| `tempo_total` | 1:00,00 | `m:ss,cc` ou segundos (`60,00`) |
| `trecho_m`, `trecho_s` | 60; 40,00 | Trecho de nado puro |
| `ciclos_trecho`, `ciclos_prova` | 40; 50 | Ciclos de braçada |
| `vm_manual` ... `swolf25_manual` | 1,67 | Métricas calculadas à mão; vazio = não calculada |
| `tempo_calculo_manual` | 4:00 | Tempo gasto no cálculo manual (`m:ss`) |
| `tempo_cadastro_sistema` | 1:00 | Tempo gasto no cadastro no sistema (`m:ss`) |

## 6. Gerar os resultados

Na pasta `backend`, com o venv ativo:

```powershell
python -m scripts.validate_metrics --planilha=coleta.csv --csv=validacao.csv
```

O script lê a planilha, recalcula as métricas com **as mesmas funções do sistema** e mostra:
- concordância por métrica: quantos registros foram comparados, quantos concordam, maior diferença e diferença média;
- os registros com diferença acima da tolerância e em quais métricas;
- tempo médio e mediano do cálculo manual e do cadastro, e quantas vezes o sistema foi mais rápido.

O arquivo `validacao.csv` traz a comparação registro por registro.

**Tolerância:** uma unidade na última casa exibida (±0,01 para Vm, VN, CB e IN; ±0,1 para cadência e SWOLF). Diferenças desse tamanho vêm do arredondamento em etapas diferentes (ex.: arredondar a VN antes de calcular o IN). Diferenças maiores indicam erro de conta ou de fórmula e devem ser investigadas uma a uma.

**Ligação com os testes de integração (AQ-24):** os testes já confirmam que a API devolve exatamente o que essas funções calculam; por isso, recalcular pela planilha equivale a ler as métricas na tela. Para reforçar, conferir algumas métricas na tela de detalhes do treino.

## 7. Complementar (se houver tempo): vídeos de provas oficiais

Registros extraídos de vídeos públicos de provas, com o **tempo oficial** como referência para a Vm. Os ciclos e o tempo entre as bandeirolas são contados quadro a quadro.
- Guardar só os números e a referência do vídeo (título, canal, endereço, data de acesso); o vídeo não entra no repositório.
- Limitações: a cerca de 30 quadros por segundo, cada marcação tem erro de cerca de 0,03 s; o ângulo da câmera dificulta ver as bandeirolas.

## 8. Limitações a registrar

- Amostra pequena, de um único clube.
- A contagem dos ciclos e a marcação do trecho dependem de quem mede (filmar ajuda a conferir).
- O tempo do cadastro inclui digitar os dados; o do cálculo manual não inclui passar a limpo.
- A previsão não é validada com dados reais nesta etapa (exige pelo menos 6 registros por prova); fica como trabalho futuro.