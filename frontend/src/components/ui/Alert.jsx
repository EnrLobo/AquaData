export default function Alert({ children }) {
  return (
    <p role="alert" className="rounded-lg bg-danger-soft px-4 py-3 text-sm text-danger">
      {children}
    </p>
  )
}