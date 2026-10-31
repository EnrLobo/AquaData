import { Activity, FileText, LogOut, Timer, Users } from 'lucide-react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { initials } from '../utils/text'
import Logo from './Logo'
import ThemeToggle from './ThemeToggle'
import Button from './ui/Button'

const NAV = [
  { to: '/atletas', label: 'Atletas', icon: Users },
  { label: 'Treinos', icon: Timer, soon: true },
  { label: 'Desempenho', icon: Activity, soon: true },
  { label: 'Relatórios', icon: FileText, soon: true },
]

const itemBase = 'flex h-11 items-center gap-3 rounded-xl px-4 text-sm font-medium transition-colors'
const linkClass = ({ isActive }) =>
  `${itemBase} ${isActive ? 'bg-brand-soft text-brand-text' : 'text-muted hover:bg-subtle hover:text-fg'}`

export default function AppLayout() {
  const { coach, signOut } = useAuth()

  return (
    <div className="min-h-screen bg-canvas">
      <aside className="fixed inset-y-0 left-0 hidden w-64 flex-col border-r border-line bg-surface lg:flex">
        <div className="px-6 pt-8">
          <Link to="/atletas" aria-label="aquaData, página inicial">
            <Logo className="h-9" />
          </Link>
        </div>
        <p className="mt-10 px-6 text-[11px] font-semibold uppercase tracking-wider text-muted">
          Menu
        </p>
        <nav aria-label="Principal" className="mt-3 flex-1 space-y-1 px-4">
          {NAV.map((item) => {
            const Icon = item.icon
            return item.soon ? (
              <span
                key={item.label}
                aria-disabled="true"
                className={`${itemBase} cursor-not-allowed text-muted/60`}
              >
                <Icon size={18} aria-hidden="true" />
                {item.label}
                <span className="ml-auto rounded-full bg-subtle px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide">
                  Em breve
                </span>
              </span>
            ) : (
              <NavLink key={item.label} to={item.to} className={linkClass}>
                <Icon size={18} aria-hidden="true" />
                {item.label}
              </NavLink>
            )
          })}
        </nav>
        <div className="border-t border-line p-4">
          <ThemeToggle showLabel />
          <div className="mt-2 flex items-center gap-3 px-1">
            <span
              aria-hidden="true"
              className="grid size-10 shrink-0 place-items-center rounded-full bg-brand-soft text-xs font-semibold text-brand-text"
            >
              {initials(coach.name)}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold">{coach.name}</p>
              <p className="text-xs text-muted">Treinador</p>
            </div>
            <Button variant="ghost" size="icon" onClick={signOut} aria-label="Sair">
              <LogOut size={18} aria-hidden="true" />
            </Button>
          </div>
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 border-b border-line bg-surface/90 backdrop-blur lg:hidden">
          <div className="flex h-16 items-center justify-between px-4">
            <Link to="/atletas" aria-label="aquaData, página inicial">
              <Logo className="h-8" />
            </Link>
            <div className="flex items-center gap-1">
              <ThemeToggle />
              <Button variant="ghost" size="icon" onClick={signOut} aria-label="Sair">
                <LogOut size={18} aria-hidden="true" />
              </Button>
            </div>
          </div>
          <nav aria-label="Principal" className="flex gap-1 overflow-x-auto px-4 pb-2">
            {NAV.filter((item) => !item.soon).map((item) => {
              const Icon = item.icon
              return (
                <NavLink key={item.label} to={item.to} className={linkClass}>
                  <Icon size={18} aria-hidden="true" />
                  {item.label}
                </NavLink>
              )
            })}
          </nav>
        </header>
        <main className="mx-auto max-w-[1600px] px-4 py-8 sm:px-8 lg:px-12 lg:py-12">
          <Outlet />
        </main>
      </div>
    </div>
  )
}