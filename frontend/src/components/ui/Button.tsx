import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { Icon, type IconName } from './Icon'

type Variant = 'default' | 'primary' | 'ghost' | 'danger'
type Size = 'sm' | 'md' | 'lg'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  icon?: IconName
  iconRight?: IconName
  kbd?: string
  block?: boolean
  children?: ReactNode
}

const VARIANT_CLASS: Record<Variant, string> = {
  default: '',
  primary: 'btn--primary',
  ghost: 'btn--ghost',
  danger: 'btn--danger',
}

const SIZE_CLASS: Record<Size, string> = {
  sm: 'btn--sm',
  md: '',
  lg: 'btn--lg',
}

/** The one button. Every clickable action in Genos uses this. */
export function Button({
  variant = 'default',
  size = 'md',
  icon,
  iconRight,
  kbd,
  block,
  className = '',
  children,
  ...rest
}: ButtonProps) {
  const classes = ['btn', VARIANT_CLASS[variant], SIZE_CLASS[size], block ? 'btn--block' : '', className]
    .filter(Boolean)
    .join(' ')

  return (
    <button type="button" className={classes} {...rest}>
      {icon ? <Icon name={icon} size={size === 'sm' ? 12 : 13} /> : null}
      {children}
      {iconRight ? <Icon name={iconRight} size={size === 'sm' ? 12 : 13} /> : null}
      {kbd ? <kbd className="btn__kbd">{kbd}</kbd> : null}
    </button>
  )
}
