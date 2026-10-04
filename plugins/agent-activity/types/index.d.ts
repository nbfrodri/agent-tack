export type ActivityStatus = 'running' | 'ok' | 'error' | 'denied' | 'ask'

export type Activity = {
  id: string
  at: number
  kind: 'tool' | 'skill' | 'subagent' | 'permission'
  label: string
  detail: string
  status: ActivityStatus
  isSubagent: boolean
}

declare module 'claude-code' {
  interface PluginState {
    'agent-activity': { entries: Activity[] }
  }
}
