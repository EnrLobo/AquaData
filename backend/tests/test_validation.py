"""Validação das métricas com dados reais (AQ-25): leitura da planilha e comparação."""

import pytest

from app.services.validation import (
    VALIDATION_COLUMNS,
    ValidationInputError,
    check_row,
    parse_decimal,
    parse_row,
    parse_time,
    read_rows,
    summarize_metrics,
    summarize_timing,
    tolerance,
)

# Registro de referência (mesmo dos testes das métricas): 100 m livre em 1:00,00;
# trecho de 60 m em 40 s com 40 ciclos; 50 ciclos na prova completa.
# Valores certos: Vm 1,67; VN 1,50; CB 1,50; cadência 60,0; IN 2,25; SWOLF 160,0; SWOLF 25 m 40,0
REFERENCIA = {
    "registro": "R01",
    "atleta": "Atleta Teste",
    "nado": "Livre",
    "distancia_m": "100",
    "piscina_m": "25",
    "tempo_total": "1:00,00",
    "trecho_m": "60",
    "trecho_s": "40,00",
    "ciclos_trecho": "40",
    "ciclos_prova": "50",
    "vm_manual": "1,67",
    "vn_manual": "1,50",
    "cb_manual": "1,50",
    "cadencia_manual": "60,0",
    "in_manual": "2,25",
    "swolf_manual": "160",
    "swolf25_manual": "40,0",
    "tempo_calculo_manual": "4:00",
    "tempo_cadastro_sistema": "1:00",
}


def linha(**alteracoes) -> dict:
    return {**REFERENCIA, **alteracoes}


def planilha(*linhas: dict) -> str:
    texto = ";".join(VALIDATION_COLUMNS) + "\r\n"
    for item in linhas:
        texto += ";".join(item.get(coluna, "") for coluna in VALIDATION_COLUMNS) + "\r\n"
    return "\ufeff" + texto


def test_leitura_de_numeros_e_tempos_no_padrao_brasileiro():
    assert parse_decimal("1,67") == 1.67
    assert parse_decimal("1.67") == 1.67
    assert parse_decimal("1.234,5") == 1234.5
    assert parse_decimal("  ") is None
    assert parse_time("1:04,62") == pytest.approx(64.62)
    assert parse_time("64,62") == pytest.approx(64.62)
    assert parse_time("3:20") == 200  # tempo cronometrado do procedimento
    assert parse_time("") is None
    for invalido in ("abc", "1:75", "x:10"):
        with pytest.raises(ValidationInputError):
            parse_time(invalido)


def test_calculo_manual_correto_concorda_em_todas_as_metricas():
    resultado = check_row(parse_row(linha()))
    assert resultado.metrics.vm == 1.67 and resultado.metrics.swolf == 160.0
    assert all(check.agrees for check in resultado.checks)
    assert resultado.disagreements == []


def test_diferenca_de_arredondamento_fica_dentro_da_tolerancia():
    # treinador arredondou diferente: Vm 1,66 (truncou 1,666...) e IN 2,26
    resultado = check_row(parse_row(linha(vm_manual="1,66", in_manual="2,26")))
    assert tolerance(2) == pytest.approx(0.01)
    assert resultado.disagreements == []
    assert resultado.checks[0].difference == pytest.approx(-0.01)


def test_erro_de_conta_manual_e_apontado():
    # CB com a distância total no lugar do trecho (100 ÷ 40 = 2,50) e SWOLF sem dobrar os ciclos
    resultado = check_row(parse_row(linha(cb_manual="2,50", swolf_manual="110")))
    divergentes = {check.metric: check for check in resultado.disagreements}
    assert set(divergentes) == {"cb", "swolf"}
    assert divergentes["cb"].difference == pytest.approx(1.0)
    assert divergentes["swolf"].difference == pytest.approx(-50.0)


def test_valor_ausente_nao_entra_na_comparacao():
    # medley: o sistema não calcula SWOLF; métrica manual em branco também não conta
    resultado = check_row(parse_row(linha(nado="medley", cb_manual="")))
    por_metrica = {check.metric: check for check in resultado.checks}
    assert por_metrica["swolf"].system is None and por_metrica["swolf"].agrees is None
    assert por_metrica["cb"].manual is None and por_metrica["cb"].agrees is None
    assert resultado.disagreements == []


def test_peito_conta_um_ciclo_como_uma_bracada():
    resultado = check_row(parse_row(linha(nado="Peito", swolf_manual="110", swolf25_manual="27,5")))
    assert resultado.metrics.swolf == 110.0
    assert resultado.disagreements == []


def test_resumo_por_metrica_e_por_tempo():
    texto = planilha(
        linha(),
        linha(registro="R02", cb_manual="2,50", tempo_calculo_manual="5:00",
              tempo_cadastro_sistema="1:30"),
        linha(registro="R03", tempo_calculo_manual="", tempo_cadastro_sistema=""),
    )
    linhas = read_rows(texto)
    assert len(linhas) == 3
    resumo = {item.metric: item for item in summarize_metrics([check_row(r) for r in linhas])}
    assert (resumo["cb"].compared, resumo["cb"].agreed) == (3, 2)
    assert resumo["cb"].agreement_pct == pytest.approx(66.67, abs=0.01)
    assert resumo["cb"].max_abs_difference == pytest.approx(1.0)
    assert resumo["vm"].agreement_pct == 100

    tempos = summarize_timing(linhas)
    assert tempos.n == 2  # R03 sem cronometragem fica de fora
    assert tempos.mean_manual_s == 270  # (240 + 300) ÷ 2
    assert tempos.mean_system_s == 75  # (60 + 90) ÷ 2
    assert tempos.speedup == pytest.approx(3.6)


def test_planilha_com_erro_aponta_a_linha():
    with pytest.raises(ValidationInputError, match="linha 3: nado inválido"):
        read_rows(planilha(linha(), linha(nado="cachorrinho")))
    with pytest.raises(ValidationInputError, match="linha 2: coluna \"tempo_total\" vazia"):
        read_rows(planilha(linha(tempo_total="")))
    with pytest.raises(ValidationInputError, match="colunas ausentes"):
        read_rows("registro;atleta\r\nR01;Fulano\r\n")


def test_linha_em_branco_e_ignorada():
    texto = planilha(linha()) + ";" * (len(VALIDATION_COLUMNS) - 1) + "\r\n"
    assert len(read_rows(texto)) == 1