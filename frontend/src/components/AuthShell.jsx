import LoginShowcase from './LoginShowcase'
import ThemeToggle from './ThemeToggle'

export default function AuthShell({ children }) {
  return (
    <div className="grid min-h-screen gap-6 p-4 sm:p-6 lg:grid-cols-2">
      <LoginShowcase />
      <div className="relative flex flex-col items-center justify-center py-10">
        <div className="absolute right-0 top-0">
          <ThemeToggle />
        </div>
        <div className="w-full max-w-md">{children}</div>
        <p className="mt-10 text-xs text-muted">© 2026 aquaData. Todos os direitos reservados.</p>
      </div>
    </div>
  )
}