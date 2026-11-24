import { Info, Sparkles } from 'lucide-react'
import { formatDate } from '../utils/date'
import { SESSION_TYPE_LABEL, formatDecimal, formatTime } from '../utils/session'
import TechnicalDetails from './TechnicalDetails'
import Alert from './ui/Alert'
import Spinner from './ui/Spinner'

function signed(value, digits = 2) {
  const sign = value > 0 ? '+' : value < 0 ? '−' : ''
  return `${sign}${formatDecimal(Math.abs(value), digits)}`
}

// frase simples para a variação do tempo a cada novo registro (b1 do modelo)
function changeText(coef) {
  const abs = formatDecimal(Math.abs(coef), 2)
  if (Math.abs(coef) < 0.005) return 'O tempo está praticamente estável'
  return coef < 0
    ? `O tempo tende a cair ${abs} s a cada novo registro`
    : `O tempo tende a subir ${abs} s a cada novo registro`
}

// frase simples para a diferença entre competição e treino (b2 do modelo)
function competitionText(coef) {
  if (coef == null) return 'Aparece quando a prova tem treinos e competições'
  const abs = formatDecimal(Math.abs(coef), 2)
  if (Math.abs(coef) < 0.005) return 'Competição e treino com tempos parecidos'
  return coef < 0
    ? `Em competição, costuma ser ${abs} s mais rápido`
    : `Em competição, costuma ser ${abs} s mais lento`
}

function PredictionBox({ label, value, last }) {
  const delta = value != null && last != null ? value - last : null
  return (
    <div className="rounded-2xl border border-line bg-canvas p-5">
      <p className="text-sm text-muted">{label}</p>
      <p className="mt-2 text-3xl font-semibold tracking-tight">
        {value != null ? formatTime(value) : <span className="text-muted">—</span>}
      </p>
      {delta != null && (
        <p className="mt-1 text-xs text-muted">
          {signed(delta)} s em relação ao último registro
        </p>
      )}
    </div>
  )
}

// Previsão do próximo registro de uma prova (Regressão Linear, AQ-18/AQ-19).
// Os dados vêm da página (a mesma consulta alimenta o gráfico de tempos).
// Linguagem simples na tela; termos estatísticos em "Detalhes técnicos" (AQ-26).
export default function PredictionPanel({ loading, error, data }) {
  return (
    <section
      aria-labelledby="prediction-title"
      className="mb-8 rounded-2xl border border-line bg-surface p-4 sm:p-6"
    >
      <div className="mb-4 flex items-start gap-3">
        <span
          aria-hidden="true"
          className="grid size-9 shrink-0 place-items-center rounded-full bg-brand-soft text-brand-text"
        >
          <Sparkles size={18} />
        </span>
        <div>
          <h2 id="prediction-title" className="text-lg font-semibold">
            Previsão do próximo registro
          </h2>
          <p className="text-sm text-muted">
            Calculada com todos os tempos já registrados nesta prova (os filtros de tipo e período
            não mudam a previsão).
          </p>
        </div>
      </div>

      {loading ? (
        <Spinner />
      ) : error ? (
        <Alert>{error}</Alert>
      ) : !data.available ? (
        <p className="flex items-start gap-2 rounded-xl bg-subtle px-4 py-3 text-sm text-muted">
          <Info size={16} aria-hidden="true" className="mt-0.5 shrink-0" />
          {data.message}
        </p>
      ) : (
        <PredictionContent data={data} />
      )}
    </section>
  )
}

function PredictionContent({ data }) {
  const { model, evaluation, last_session: last } = data
  const lastTime = last?.total_time_s ?? null

  return (
    <>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <PredictionBox label="Se for treino" value={data.training_s} last={lastTime} />
        <PredictionBox label="Se for competição" value={data.competition_s} last={lastTime} />
      </div>
      {data.competition_s == null && (
        <p className="mt-2 text-xs text-muted">
          A previsão para competição aparece quando a prova tem treinos e competições registrados.
        </p>
      )}

      <dl className="mt-6 grid grid-cols-1 gap-4 text-sm sm:grid-cols-3">
        <div>
          <dt className="text-xs text-muted">Último registro</dt>
          <dd className="mt-1 font-medium">
            {formatTime(last.total_time_s)} · {SESSION_TYPE_LABEL[last.session_type]} em{' '}
            {formatDate(last.session_date)}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-muted">Tendência</dt>
          <dd className="mt-1 font-medium">{changeText(model.coef_order)}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted">Competição × treino</dt>
          <dd className="mt-1 font-medium">{competitionText(model.coef_competition)}</dd>
        </div>
      </dl>

      <div className="mt-6 rounded-xl border border-line">
        <div className="px-4 pt-4">
          <h3 className="text-sm font-semibold">Quanto confiar nesta previsão</h3>
          <p className="mt-2 text-sm">
            Para testar, o sistema escondeu os {evaluation.n_test} registros mais recentes e tentou
            adivinhá-los usando só os {evaluation.n_train} anteriores. Em média, a previsão errou{' '}
            <strong>{formatDecimal(evaluation.mae_s)} s</strong> (cerca de{' '}
            <strong>{formatDecimal(evaluation.mape_pct, 1)}%</strong> do tempo).
          </p>
        </div>
        {/* celular: lista; a partir de sm: tabela (AQ-26) */}
        <ul className="mt-3 divide-y divide-line border-t border-line sm:hidden">
          {evaluation.points.map((p) => (
            <li key={p.session_id} className="px-4 py-3 text-sm">
              <p className="text-xs text-muted">
                {formatDate(p.session_date)} · {p.is_competition ? 'Competição' : 'Treino'}
              </p>
              <p className="mt-1">
                Real <strong>{formatTime(p.actual_s)}</strong> · previsto{' '}
                {formatTime(p.predicted_s)} · diferença {signed(p.error_s)} s
              </p>
            </li>
          ))}
        </ul>
        <div className="mt-3 hidden overflow-x-auto sm:block">
          <table className="w-full min-w-[32rem] text-left text-sm">
            <caption className="sr-only">Tempos reais e previstos nos registros de teste</caption>
            <thead className="bg-subtle text-xs uppercase tracking-wide text-muted">
              <tr>
                <th scope="col" className="px-4 py-2 font-medium">Data</th>
                <th scope="col" className="px-4 py-2 font-medium">Tipo</th>
                <th scope="col" className="px-4 py-2 font-medium">Tempo real</th>
                <th scope="col" className="px-4 py-2 font-medium">Previsto</th>
                <th scope="col" className="px-4 py-2 font-medium">Diferença</th>
              </tr>
            </thead>
            <tbody>
              {evaluation.points.map((p) => (
                <tr key={p.session_id} className="border-t border-line">
                  <td className="px-4 py-2 text-muted">{formatDate(p.session_date)}</td>
                  <td className="px-4 py-2">{p.is_competition ? 'Competição' : 'Treino'}</td>
                  <td className="px-4 py-2 font-medium">{formatTime(p.actual_s)}</td>
                  <td className="px-4 py-2">{formatTime(p.predicted_s)}</td>
                  <td className="px-4 py-2">{signed(p.error_s)} s</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <TechnicalDetails className="mt-4">
        <p>
          Regressão Linear por mínimos quadrados, ajustada com os {model.n} registros da prova:
          tempo = b0 + b1 · ordem + b2 · competição.
        </p>
        <dl className="mt-2 grid grid-cols-1 gap-x-6 gap-y-1 sm:grid-cols-2">
          <div className="flex justify-between gap-3">
            <dt>b0 (intercepto)</dt>
            <dd className="font-medium text-fg">{formatDecimal(model.intercept, 3)} s</dd>
          </div>
          <div className="flex justify-between gap-3">
            <dt>b1 (variação por registro)</dt>
            <dd className="font-medium text-fg">{signed(model.coef_order, 3)} s</dd>
          </div>
          <div className="flex justify-between gap-3">
            <dt>b2 (competição − treino)</dt>
            <dd className="font-medium text-fg">
              {model.coef_competition != null ? `${signed(model.coef_competition, 3)} s` : '—'}
            </dd>
          </div>
          <div className="flex justify-between gap-3">
            <dt>R² (ajuste no histórico, 0 a 1)</dt>
            <dd className="font-medium text-fg">
              {model.r2 != null ? formatDecimal(model.r2, 2) : '—'}
            </dd>
          </div>
          <div className="flex justify-between gap-3">
            <dt>MAE (erro absoluto médio)</dt>
            <dd className="font-medium text-fg">{formatDecimal(evaluation.mae_s)} s</dd>
          </div>
          <div className="flex justify-between gap-3">
            <dt>MAPE (erro percentual médio)</dt>
            <dd className="font-medium text-fg">{formatDecimal(evaluation.mape_pct, 1)}%</dd>
          </div>
          <div className="flex justify-between gap-3">
            <dt>RMSE (raiz do erro quadrático médio)</dt>
            <dd className="font-medium text-fg">{formatDecimal(evaluation.rmse_s)} s</dd>
          </div>
          <div className="flex justify-between gap-3">
            <dt>Divisão treino/teste (temporal)</dt>
            <dd className="font-medium text-fg">
              {evaluation.n_train} / {evaluation.n_test}
            </dd>
          </div>
        </dl>
      </TechnicalDetails>

      <p className="mt-4 text-xs text-muted">
        É uma estimativa baseada só nos tempos registrados; não considera descanso, saúde ou fase
        do treinamento. Use como apoio à decisão do treinador.
      </p>
    </>
  )
}