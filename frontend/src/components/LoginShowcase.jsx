import { Pause, Play } from 'lucide-react'
import { useState } from 'react'
import { LOGIN_HIGHLIGHTS } from '../content/loginHighlights'
import { prefersReducedMotion } from '../utils/motion'
import LoginVideo from './LoginVideo'

export default function LoginShowcase() {
  const [active, setActive] = useState(0)
  const [paused, setPaused] = useState(prefersReducedMotion)
  const current = LOGIN_HIGHLIGHTS[active]
  const next = () => setActive((i) => (i + 1) % LOGIN_HIGHLIGHTS.length)

  return (
    <section
      aria-label="Destaques do aquaData"
      className="relative hidden overflow-hidden rounded-3xl bg-[#071a29] lg:block"
    >
      <LoginVideo paused={paused} />
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/25 to-transparent"
      />

      <button
        type="button"
        onClick={() => setPaused((p) => !p)}
        aria-label={paused ? 'Retomar vídeo e destaques' : 'Pausar vídeo e destaques'}
        className="absolute right-4 top-4 grid size-10 place-items-center rounded-full bg-black/40 text-white backdrop-blur transition-colors hover:bg-black/60 focus-visible:outline-2 focus-visible:outline-white"
      >
        {paused ? <Play size={16} aria-hidden="true" /> : <Pause size={16} aria-hidden="true" />}
      </button>

      <div className="absolute inset-x-0 bottom-0 p-10 text-white">
        <h2 className="text-2xl font-semibold tracking-tight">{current.title}</h2>
        <p className="mt-2 max-w-md text-sm text-white/80">{current.description}</p>

        <ol className="mt-8 grid grid-cols-4 gap-4">
          {LOGIN_HIGHLIGHTS.map((item, index) => (
            <li key={item.id}>
              <button
                type="button"
                onClick={() => setActive(index)}
                aria-current={index === active ? 'true' : undefined}
                className="block w-full text-left focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-white"
              >
                <span className="text-[11px] font-semibold uppercase tracking-wider">
                  {item.label}
                </span>
                <span className="mt-2 block h-1 overflow-hidden rounded-full bg-white/30">
                  <span
                    onAnimationEnd={index === active ? next : undefined}
                    style={index === active && paused ? { animationPlayState: 'paused' } : undefined}
                    className={`block h-full origin-left rounded-full bg-white ${
                      index < active
                        ? 'w-full'
                        : index === active
                          ? 'w-full animate-fill motion-reduce:animate-none'
                          : 'w-0'
                    }`}
                  />
                </span>
              </button>
            </li>
          ))}
        </ol>
      </div>
    </section>
  )
}