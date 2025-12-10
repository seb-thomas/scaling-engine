import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Deterministic date formatting to avoid SSR/client hydration mismatches
// Using manual formatting instead of toLocaleDateString which varies by locale

const MONTHS_FULL = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
]

const MONTHS_SHORT = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
]

/**
 * Format date as "January 15, 2024"
 */
export function formatDateLong(dateString: string): string {
  const date = new Date(dateString)
  const month = MONTHS_FULL[date.getMonth()]
  const day = date.getDate()
  const year = date.getFullYear()
  return `${month} ${day}, ${year}`
}

/**
 * Format date as "Jan 15, 2024"
 */
export function formatDateShort(dateString: string): string {
  const date = new Date(dateString)
  const month = MONTHS_SHORT[date.getMonth()]
  const day = date.getDate()
  const year = date.getFullYear()
  return `${month} ${day}, ${year}`
}

