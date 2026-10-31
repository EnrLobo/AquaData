import { Eye, EyeOff } from 'lucide-react'
import { useState } from 'react'
import TextField from './TextField'

export default function PasswordField(props) {
  const [visible, setVisible] = useState(false)

  return (
    <TextField
      {...props}
      type={visible ? 'text' : 'password'}
      trailing={
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? 'Ocultar senha' : 'Mostrar senha'}
          aria-pressed={visible}
          className="grid size-9 place-items-center rounded-lg text-muted transition-colors hover:text-fg focus-visible:outline-2 focus-visible:outline-brand-text"
        >
          {visible ? <EyeOff size={18} aria-hidden="true" /> : <Eye size={18} aria-hidden="true" />}
        </button>
      }
    />
  )
}