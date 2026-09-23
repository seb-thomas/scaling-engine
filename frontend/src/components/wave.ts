/** Three stacked wavy lines in `color`, as a data URI for a repeating background */
export function wavePattern(color: string): string {
  const c = encodeURIComponent(color)
  return `data:image/svg+xml,%3Csvg width='32' height='24' viewBox='0 0 32 24' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M2 6 Q 4 4, 6 6 T 10 6 T 14 6 T 18 6 T 22 6 T 26 6 T 30 6' stroke='${c}' stroke-width='1.5' fill='none'/%3E%3Cpath d='M2 12 Q 4 10, 6 12 T 10 12 T 14 12 T 18 12 T 22 12 T 26 12 T 30 12' stroke='${c}' stroke-width='1.5' fill='none'/%3E%3Cpath d='M2 18 Q 4 16, 6 18 T 10 18 T 14 18 T 18 18 T 22 18 T 26 18 T 30 18' stroke='${c}' stroke-width='1.5' fill='none'/%3E%3C/svg%3E`
}

export function waveStyle(color: string): string {
  return `background-image: url("${wavePattern(color)}"); background-repeat: repeat; background-size: 32px 24px`
}
