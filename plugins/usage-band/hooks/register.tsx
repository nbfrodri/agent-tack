import { atom, read, update } from 'claude-code'
import type { Register, SessionContextUsage, SessionCost, SessionRateLimit } from 'claude-code'

import type { Usage, UsageWindow } from '../types'

const usage = atom({ plugin: 'usage-band', key: 'usage' } as const, { windows: [] } as Usage)
const isHidden = atom({ plugin: 'usage-band', key: 'isHidden' } as const, false)

const LABELS: Record<string, string> = { five_hour: '5h', seven_day: '7d', spend_limit: 'spend' }
const WARN_AT = [80, 90]
const BAR_CELLS = 10

export function toUsage(context: SessionContextUsage, rateLimits: SessionRateLimit[], cost?: SessionCost): Usage {
  return {
    windows: rateLimits.map(({ kind, percentUsed, resetsAt }) => ({ kind, percentUsed, resetsAt })),
    contextPercent: context.percent,
    costUsd: cost?.usd,
  }
}

export function bar(percent: number): string {
  const filled = Math.min(BAR_CELLS, Math.max(0, Math.round((percent / 100) * BAR_CELLS)))
  return '█'.repeat(filled) + '░'.repeat(BAR_CELLS - filled)
}

export function colorFor(percent: number): string {
  if (percent >= 90) return 'red'
  if (percent >= 70) return 'yellow'
  return 'green'
}

// Same-day resets show only the time; later ones add the weekday, which is what the weekly window needs.
export function resetLabel(resetsAt: string | undefined, now: number): string {
  if (!resetsAt) return ''
  const at = new Date(resetsAt)
  if (Number.isNaN(at.getTime())) return ''
  const time = `${String(at.getHours()).padStart(2, '0')}:${String(at.getMinutes()).padStart(2, '0')}`
  const sameDay = new Date(now).toDateString() === at.toDateString()
  if (sameDay) return `resets ${time}`
  const day = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][at.getDay()]
  return `resets ${day} ${time}`
}

export function crossedWarning(before: UsageWindow[], after: UsageWindow[]): string | undefined {
  for (const window of after) {
    const previous = before.find(one => one.kind === window.kind)?.percentUsed ?? 0
    const threshold = WARN_AT.filter(at => previous < at && window.percentUsed >= at).pop()
    if (threshold !== undefined) {
      return `${LABELS[window.kind] ?? window.kind} usage passed ${threshold}%`
    }
  }
  return undefined
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const { context, rateLimits, cost } = await $.session.usage()
    await update($, usage, () => toUsage(context, rateLimits, cost))
    await $.command.register({ name: 'usage-band', description: 'Show or hide the usage band above the prompt' })
    return next(e)
  })

  on('session.measure', async ($, e, next) => {
    const before = (await read($, usage)).windows
    const after = toUsage(e.context, e.rateLimits, e.cost)
    await update($, usage, () => after)
    const warning = crossedWarning(before, after.windows)
    if (warning) $.ui.toast(warning)
    return next(e)
  })

  on('command.run', { command: 'usage-band' }, async $ => {
    const hidden = await update($, isHidden, value => !value)
    return { text: hidden ? 'Usage band hidden.' : 'Usage band shown.' }
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const current = await read($, usage)
    if (e.props.hasSurvey || (await read($, isHidden))) return next(e)

    const { Box, Text } = $.ui.resolve(e)
    const now = await $.clock.now()
    const hasData = current.windows.length > 0 || current.contextPercent !== undefined

    return (
      <Box flexDirection="row" gap={3}>
        {!hasData && <Text dimColor>usage: waiting for the first response</Text>}
        {current.windows.map(window => (
          <Box key={window.kind} flexDirection="row" gap={1}>
            <Text bold>{LABELS[window.kind] ?? window.kind}</Text>
            <Text color={colorFor(window.percentUsed)}>{bar(window.percentUsed)}</Text>
            <Text>{`${Math.round(window.percentUsed)}%`}</Text>
            <Text dimColor>{resetLabel(window.resetsAt, now)}</Text>
          </Box>
        ))}
        {current.contextPercent !== undefined && (
          <Text dimColor>{`ctx ${current.contextPercent}%`}</Text>
        )}
        {current.costUsd !== undefined && <Text dimColor>{`$${current.costUsd.toFixed(2)}`}</Text>}
      </Box>
    )
  })
}
