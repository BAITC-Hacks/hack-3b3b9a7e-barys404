import type { LucideIcon } from 'lucide-react'

export type View = 'overview' | 'hospitals' | 'hospital' | 'compare' | 'forecasts' | 'data'
export type Mode = 'government' | 'hospital'
export type NavItem = { id: View; label: string; icon: LucideIcon }
