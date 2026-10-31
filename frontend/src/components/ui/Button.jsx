import { buttonClasses } from './button-styles'

export default function Button({
  variant = 'primary',
  size = 'md',
  type = 'button',
  className = '',
  ...props
}) {
  return <button type={type} className={buttonClasses(variant, size, className)} {...props} />
}