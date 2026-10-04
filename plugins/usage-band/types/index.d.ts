export type UsageWindow = { kind: string; percentUsed: number; resetsAt?: string }

export type Usage = {
  windows: UsageWindow[]
  contextPercent?: number
  costUsd?: number
}

declare module 'claude-code' {
  interface PluginState {
    'usage-band': { usage: Usage; isHidden: boolean; chip: string }
  }
}
