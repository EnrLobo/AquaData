import { Info, Sparkles } from 'lucide-react'
import { formatDate } from '../utils/date'
import { SESSION_TYPE_LABEL, formatDecimal, formatTime } from '../utils/session'
import Alert from './ui/Alert'
import Spinner from './ui/Spinner'

function signed(value, digits = 2) {
  const sign = value > 0 ? '+' : value < 0 ? '−' : ''
  return `${sign}${formatDecimal(Math.abs(value), digits)}`
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
export default function PredictionPanel({ loading, error, data }) {
  return (
    <section
      aria-labelledby="prediction-title"
      className="mb-8 rounded-2xl border border-line bg-surface p-6"
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
            Regressão Linear com todo o histórico desta prova (os filtros de tipo e período não se
            aplicam aqui).
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
      <div className="grid gap-4 sm:grid-cols-2">
        <PredictionBox label="Se for treino" value={data.training_s} last={lastTime} />
        <PredictionBox label="Se for competição" value={data.competition_s} last={lastTime} />
      </div>
      {data.competition_s == null && (
        <p className="mt-2 text-xs text-muted">
          A previsão para competição aparece quando a prova tem treinos e competições registrados.
        </p>
      )}

      <dl className="mt-6 grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <dt className="text-xs text-muted">Último registro</dt>
          <dd className="mt-1 font-medium">
            {formatTime(last.total_time_s)} · {SESSION_TYPE_LABEL[last.session_type]} em{' '}
            {formatDate(last.session_date)}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-muted">Variação por registro</dt>
          <dd className="mt-1 font-medium">{signed(model.coef_order, 3)} s</dd>
        </div>
        <div>
          <dt className="text-xs text-muted">Competição em relação ao treino</dt>
          <dd className="mt-1 font-medium">
            {model.coef_competition != null ? `${signed(model.coef_competition)} s` : '—'}
          </dd>
        </div>
        <div>
          <dt
            className="text-xs text-muted"
            title="Coeficiente de determinação: quanto a reta explica a variação dos tempos (0 a 1)"
          >
            Ajuste no histórico (R²)
          </dt>
          <dd className="mt-1 font-medium">
            {model.r2 != null ? formatDecimal(model.r2, 2) : '—'} · {model.n} registros
          </dd>
        </div>
      </dl>

      <div className="mt-6 rounded-xl border border-line">
        <div className="flex flex-wrap items-baseline justify-between gap-2 px-4 pt-4">
          <h3 className="text-sm font-semibold">Qualidade da previsão</h3>
          <p className="text-xs text-muted">
            Treinado com os {evaluation.n_train} registros mais antigos e testado nos{' '}
            {evaluation.n_test} mais recentes
          </p>
        </div>
        <p className="px-4 pt-2 text-sm">
          Erro médio de <strong>{formatDecimal(evaluation.mae_s)} s</strong> (MAE), ou{' '}
          <strong>{formatDecimal(evaluation.mape_pct, 1)}%</strong> do tempo (MAPE). RMSE:{' '}
          {formatDecimal(evaluation.rmse_s)} s.
        </p>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[32rem] text-left text-sm">
            <thead className="bg-subtle text-xs uppercase tracking-wide text-muted">
              <tr>
                <th scope="col" className="px-4 py-2 font-medium">Data</th>
                <th scope="col" className="px-4 py-2 font-medium">Tipo</th>
                <th scope="col" className="px-4 py-2 font-medium">Real</th>
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

      <p className="mt-4 text-xs text-muted">
        Estimativa estatística baseada só nos tempos registrados; não considera descanso, saúde ou
        fase do treinamento. Use como apoio à decisão do treinador.
      </p>
    </>
  )
}