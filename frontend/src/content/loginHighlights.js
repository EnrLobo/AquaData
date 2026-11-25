import photoHistorico from '../assets/login-natacao.webp'
import photoMetricas from '../assets/login-metricas.webp'
import photoPrevisao from '../assets/login-previsao.webp'
import photoRelatorios from '../assets/login-relatorios.webp'

// Destaques da tela de entrada. Cada um tem a sua foto (AQ-26), que troca junto com o texto.
// imagePosition: parte da foto que fica visível quando o painel corta as bordas.
export const LOGIN_HIGHLIGHTS = [
  {
    id: 'historico',
    label: 'Histórico',
    title: 'Histórico de desempenho',
    description:
      'Acompanhe a evolução de cada atleta, treino a treino, e compare as sessões ao longo do tempo.',
    image: photoHistorico,
    imagePosition: 'center',
  },
  {
    id: 'metricas',
    label: 'Métricas',
    title: 'Métricas calculadas automaticamente',
    description:
      'SWOLF, comprimento de braçada, cadência e velocidade a partir de dados básicos de treino e prova.',
    image: photoMetricas,
    imagePosition: 'center 30%',
  },
  {
    id: 'previsao',
    label: 'Previsão',
    title: 'Previsão de desempenho',
    description:
      'O sistema estima os próximos tempos a partir do histórico e mostra se o treino está surtindo efeito.',
    image: photoPrevisao,
    imagePosition: 'center',
  },
  {
    id: 'relatorios',
    label: 'Relatórios',
    title: 'Relatórios por atleta',
    description:
      'Reúna indicadores e gráficos de evolução em um relatório pronto para o treinador.',
    image: photoRelatorios,
    imagePosition: 'center 30%',
  },
]

// Crédito exigido pela licença gratuita do Magnific (antigo Freepik): a frase
// "Designed by Freepik" visível, com link para o site
export const LOGIN_PHOTO_CREDIT = { label: 'Designed by Magnific', href: 'https://www.magnific.com' }