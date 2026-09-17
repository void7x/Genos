import type { CSSProperties, SVGProps } from 'react'
import { GENOS_ICON_PATHS, type IconName } from './icons'

export type { IconName }

interface IconProps extends Omit<SVGProps<SVGSVGElement>, 'name'> {
  name: IconName
  size?: number
}

/**
 * The single icon set for the whole product.
 *
 * One visual language: 24×24 viewBox, 1.6 stroke, rounded caps, currentColor.
 * No external icon dependency, no mixed styles.
 */
export function Icon({ name, size = 14, style, ...rest }: IconProps) {
  const paths = GENOS_ICON_PATHS[name]
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      strokeWidth={1.6}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      style={{ flex: '0 0 auto', ...style } as CSSProperties}
      {...rest}
    >
      {paths.map((d, i) => (
        <path key={i} d={d} />
      ))}
    </svg>
  )
}

/** The Genos mark. Identity element used in the bubble and title bar. */
export function GenosMark({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id="genos-mark-grad" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
          <stop stopColor="#d9d2ff" />
          <stop offset="1" stopColor="#8b7bf7" />
        </linearGradient>
      </defs>
      <path
        d="M18.8 7.6a8 8 0 1 0 .2 8.8"
        stroke="url(#genos-mark-grad)"
        strokeWidth="2.1"
        strokeLinecap="round"
      />
      <path d="M12 12h6.4" stroke="url(#genos-mark-grad)" strokeWidth="2.1" strokeLinecap="round" />
      <circle cx="12" cy="12" r="1.5" fill="#a99cff" />
    </svg>
  )
}
