import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

import type { Activity, ActivityStatus } from '../types'

const PANE = 'agent-activity'
const KEEP = 300
const entries = atom({ plugin: 'agent-activity', key: 'entries' } as const, [] as Activity[])

const STATUS_STYLE: Record<ActivityStatus, { mark: string; color: string }> = {
  running: { mark: '…', color: 'cyan' },
  ok: { mark: '✓', color: 'green' },
  error: { mark: '✗', color: 'red' },
  denied: { mark: '⛔', color: 'red' },
  ask: { mark: '?', color: 'yellow' },
}

// The field that says most about a call, in the order the built-in tools use them.
export function summarize(input: unknown): string {
  if (!input || typeof input !== 'object') return ''
  const fields = input as Record<string, unknown>
  for (const key of ['command', 'skill', 'file_path', 'pattern', 'url', 'query', 'description', 'prompt']) {
    const value = fields[key]
    if (typeof value === 'string' && value.trim()) return value.replace(/\s+/g, ' ').trim().slice(0, 160)
  }
  return ''
}

export function kindOf(tool: string): Activity['kind'] {
  if (tool === 'Skill') return 'skill'
  if (tool === 'Agent' || tool === 'Task') return 'subagent'
  return 'tool'
}

export function statusOf(result: { deny?: string; isError?: boolean } | undefined): ActivityStatus {
  if (!result) return 'error'
  if (typeof result.deny === 'string') return 'denied'
  return result.isError ? 'error' : 'ok'
}

export function clock(at: number): string {
  const time = new Date(at)
  return [time.getHours(), time.getMinutes(), time.getSeconds()].map(n => String(n).padStart(2, '0')).join(':')
}

export const register: Register = on => {
  let sequence = 0

  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'activity', description: 'Open the live pane of tool calls, skills, subagents and permission decisions' })
    void $.ui.open({ id: PANE, title: 'Agent activity' })
    return next(e)
  })

  on('command.run', { command: 'activity' }, async $ => {
    await $.ui.open({ id: PANE, title: 'Agent activity' })
    return { text: 'Agent activity pane opened.' }
  })

  on('tool.call', async ($, e, next) => {
    const id = e.tool_use_id || `call-${(sequence += 1)}`
    const entry: Activity = {
      id,
      at: await $.clock.now(),
      kind: kindOf(e.tool),
      label: e.tool,
      detail: summarize(e),
      status: 'running',
      isSubagent: Boolean(e.agentId),
    }
    await update($, entries, list => [...list, entry].slice(-KEEP))
    const result = await next(e)
    const status = statusOf(result)
    await update($, entries, list => list.map(one => (one.id === id ? { ...one, status } : one)))
    return result
  })

  on('tool.check', async ($, e, next) => {
    const verdict = await next(e)
    if (verdict.decision !== 'allow') {
      const entry: Activity = {
        id: `check-${(sequence += 1)}`,
        at: await $.clock.now(),
        kind: 'permission',
        label: `${verdict.decision} ${e.tool}`,
        detail: verdict.reason ?? summarize(e.input),
        status: verdict.decision === 'deny' ? 'denied' : 'ask',
        isSubagent: false,
      }
      await update($, entries, list => [...list, entry].slice(-KEEP))
    }
    return verdict
  })

  on('agent.spawn', async ($, e, next) => {
    const decision = await next(e)
    const entry: Activity = {
      id: `spawn-${(sequence += 1)}`,
      at: await $.clock.now(),
      kind: 'subagent',
      label: `spawn ${e.subagentType}`,
      detail: `${e.description}${'model' in decision && decision.model ? ` (${decision.model})` : ''}`,
      status: 'deny' in decision ? 'denied' : 'ok',
      isSubagent: false,
    }
    await update($, entries, list => [...list, entry].slice(-KEEP))
    return decision
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    const list = await read($, entries)
    const room = Math.max(1, (e.viewport?.rows ?? 24) - 3)
    const tools = list.filter(one => one.kind !== 'permission').length
    const asks = list.filter(one => one.kind === 'permission').length

    return (
      <Box flexDirection="column">
        <Text dimColor>{`${tools} calls · ${asks} permission prompts or denials`}</Text>
        {list.length === 0 && <Text dimColor>Nothing yet.</Text>}
        {list.slice(-room).map(entry => {
          const style = STATUS_STYLE[entry.status]
          return (
            <Box key={entry.id} flexDirection="row" gap={1}>
              <Text dimColor>{clock(entry.at)}</Text>
              <Text color={style.color}>{style.mark}</Text>
              <Text bold color={entry.kind === 'tool' ? undefined : 'magenta'}>
                {`${entry.isSubagent ? '↳ ' : ''}${entry.label}`}
              </Text>
              <Text dimColor wrap="truncate-end">{entry.detail}</Text>
            </Box>
          )
        })}
      </Box>
    )
  })
}
