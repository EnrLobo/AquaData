import { Moon, Sun } from 'lucide-react'
import { useTheme } from '../hooks/useTheme'
import Button from './ui/Button'

export default function ThemeToggle({ showLabel = false }) {
  const { theme, toggle } = useTheme()
  const dark = theme === 'dark'
  return (
    <Button
      variant="ghost"
      size={showLabel ? 'md' : 'icon'}
      onClick={toggle}
      className={showLabel ? 'w-full justify-start' : ''}
      aria-label={dark ? 'Mudar para tema claro' : 'Mudar para tema escuro'}
    >
      {dark ? <Sun size={18} aria-hidden="true" /> : <Moon size={18} aria-hidden="true" />}
      {showLabel && <span>{dark ? 'Tema claro' : 'Tema escuro'}</span>}
    </Button>
  )
}