// Cole aqui o ID do vídeo do YouTube (a parte depois de v= no link).
// Vazio: o painel mostra um degradê azul-marinho.
export const LOGIN_VIDEO = {
  youtubeId: '',
  src: '', // alternativa: caminho de um arquivo próprio
  poster: '',
}

export const LOGIN_HIGHLIGHTS = [
  {
    id: 'historico',
    label: 'Histórico',
    title: 'Histórico de desempenho',
    description:
      'Acompanhe a evolução de cada atleta, treino a treino, e compare as sessões ao longo do tempo.',
  },
  {
    id: 'metricas',
    label: 'Métricas',
    title: 'Métricas calculadas automaticamente',
    description:
      'SWOLF, comprimento de braçada, cadência e velocidade a partir de dados básicos de treino e prova.',
  },
  {
    id: 'previsao',
    label: 'Previsão',
    title: 'Previsão de desempenho',
    description:
      'A regressão linear estima os próximos tempos e mostra se o treino está surtindo efeito.',
  },
  {
    id: 'relatorios',
    label: 'Relatórios',
    title: 'Relatórios por atleta',
    description:
      'Reúna indicadores e gráficos de evolução em um relatório pronto para o treinador.',
  },
]