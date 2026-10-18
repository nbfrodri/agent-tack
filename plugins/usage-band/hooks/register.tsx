import { atom, read, update } from 'claude-code'
import type { Engine, Register, SessionContextUsage, SessionCost, SessionRateLimit } from 'claude-code'

import type { Usage, UsageWindow } from '../types'

const usage = atom({ plugin: 'usage-band', key: 'usage' } as const, { windows: [] } as Usage)
const isHidden = atom({ plugin: 'usage-band', key: 'isHidden' } as const, false)
// An atom, not a local, so setting it re-renders the band as soon as the mode is known.
const chip = atom({ plugin: 'usage-band', key: 'chip' } as const, 'tack · …')

const LABELS: Record<string, string> = { five_hour: '5h', seven_day: '7d', spend_limit: 'spend' }
const WARN_AT = [80, 90]
const BAR_CELLS = 10

export function contextPercent(value: number | undefined): number | undefined {
  return value !== undefined && Number.isFinite(value) ? Math.min(100, Math.max(0, Math.round(value))) : undefined
}

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

// `tack usage threshold` prints the percentage the offer to delegate to Codex starts at, or nothing.
export function thresholdFrom(stdout: string): number | undefined {
  const value = Number(stdout.trim())
  return Number.isInteger(value) && value > 0 && value <= 100 ? value : undefined
}

// The windows the offer to delegate to Codex follows, with the label the on-screen message uses.
const OFFERED: Record<string, string> = { five_hour: '5h', seven_day: '7d' }

// The message shown once when the 5h or weekly window crosses the percentage the offer starts at.
export function crossedDelegation(before: UsageWindow[], after: UsageWindow[], at: number | undefined): string | undefined {
  if (at === undefined) return undefined
  for (const window of after) {
    if (!(window.kind in OFFERED)) continue
    const previous = before.find(one => one.kind === window.kind)?.percentUsed ?? 0
    if (previous < at && window.percentUsed >= at) {
      return `${OFFERED[window.kind]} usage passed ${at}%: ask the assistant to hand tasks to Codex (cross-delegate)`
    }
  }
  return undefined
}

// A cost limit applies only in a project-only mode (tack prints a WARNING line for those)
// and only when `tack config unleash-max-cost` holds a positive amount.
export function costLimit(modeShow: string, configValue: string): number | undefined {
  if (!modeShow.startsWith('WARNING:')) return undefined
  const amount = Number(configValue.trim().split(' ')[0])
  return Number.isFinite(amount) && amount > 0 ? amount : undefined
}

const CHIP_PENDING = 'tack · …'
const CHIP_UNKNOWN = 'tack · ?'
const CHIP_TRIES = 3

// `tack mode` prints "<mode> (<source>)". `tack status --quiet` exits 1 when the project is not
// enabled; any other failure (tack not found, an error) means the state is unknown, not off.
export function modeChip(statusExit: number, modeOutput: string): string {
  if (statusExit === 1) return 'tack · off'
  const mode = modeOutput.trim().split(' ')[0]
  return statusExit === 0 && mode ? `tack · ${mode}` : CHIP_UNKNOWN
}

export function chipNeedsRetry(label: string): boolean {
  return label === CHIP_PENDING || label === CHIP_UNKNOWN
}

export function overBudget(costUsd: number | undefined, limitUsd: number | undefined): boolean {
  return limitUsd !== undefined && costUsd !== undefined && costUsd >= limitUsd
}

export const register: Register = on => {
  let limitUsd: number | undefined
  let delegateAt: number | undefined
  let recordedContext: number | undefined
  const recorded: Record<string, string> = {}
  let chipTries = 0
  let chipError = ''

  // Asks tack for the project's state; at session start the call can fail before the session is
  // ready, so an unknown answer is retried with the next measurement instead of reading as off.
  const refreshChip = async ($: Engine) => {
    chipTries += 1
    try {
      const status = await $.process.run(['tack', 'status', '--quiet'], { timeoutMs: 5000 })
      const mode = await $.process.run(['tack', 'mode'], { timeoutMs: 5000 })
      const label = modeChip(status.exitCode, mode.exitCode === 0 ? mode.stdout : '')
      chipError = label === CHIP_UNKNOWN ? `tack status exited ${status.exitCode}: ${status.stderr.trim()}` : ''
      await update($, chip, () => label)
    } catch (error) {
      chipError = `could not run tack: ${error instanceof Error ? error.message : String(error)}`
      await update($, chip, () => CHIP_UNKNOWN)
    }
  }

  on('session.start', async ($, e, next) => {
    const { context, rateLimits, cost } = await $.session.usage()
    await update($, usage, () => toUsage(context, rateLimits, cost))
    await $.command.register({ name: 'usage-band', description: 'Show or hide the usage band above the prompt' })
    try {
      const mode = await $.process.run(['tack', 'mode', 'show'], { timeoutMs: 5000 })
      const config = await $.process.run(['tack', 'config', 'unleash-max-cost', '--get'], { timeoutMs: 5000 })
      limitUsd = mode.exitCode === 0 && config.exitCode === 0 ? costLimit(mode.stdout, config.stdout) : undefined
    } catch {
      limitUsd = undefined
    }
    try {
      const threshold = await $.process.run(['tack', 'usage', 'threshold'], { timeoutMs: 5000 })
      delegateAt = threshold.exitCode === 0 ? thresholdFrom(threshold.stdout) : undefined
    } catch {
      delegateAt = undefined
    }
    await refreshChip($)
    return next(e)
  })

  // The hook that runs with each message reads this to offer Codex once per 5h or weekly window.
  const recordWindows = async ($: Engine, windows: UsageWindow[]) => {
    for (const window of windows) {
      if (!(window.kind in OFFERED)) continue
      const percent = Math.min(100, Math.max(0, Math.round(window.percentUsed)))
      const key = `${percent}|${window.resetsAt ?? ''}`
      if (recorded[window.kind] === key) continue
      try {
        const result = await $.process.run(['tack', 'usage', 'set', window.kind, String(percent), window.resetsAt ?? ''], { timeoutMs: 5000 })
        if (result.exitCode === 0) recorded[window.kind] = key
      } catch {
        // The offer is optional: a failed record must not disturb the session.
      }
    }
  }

  on('tool.call', async ($, e, next) => {
    const current = await read($, usage)
    if (overBudget(current.costUsd, limitUsd)) {
      return {
        deny: `This autonomous session reached its cost limit of $${limitUsd} (tack config unleash-max-cost). Stop, update the handoff and summarise what is done, what is pending and the assumptions made.`,
      }
    }
    return next(e)
  })

  on('session.measure', async ($, e, next) => {
    const before = (await read($, usage)).windows
    const after = toUsage(e.context, e.rateLimits, e.cost)
    await update($, usage, () => after)
    const warning = crossedWarning(before, after.windows)
    if (warning) $.ui.toast(warning)
    const delegation = crossedDelegation(before, after.windows, delegateAt)
    if (delegation) $.ui.toast(delegation)
    const percent = contextPercent(after.contextPercent)
    if (percent !== undefined && percent !== recordedContext) {
      try {
        const result = await $.process.run(['tack', 'usage', 'set', 'context', String(percent)], { timeoutMs: 5000 })
        if (result.exitCode === 0) recordedContext = percent
      } catch {
        // Context hints are optional: a failed record must not disturb the session.
      }
    }
    if (delegateAt !== undefined) await recordWindows($, after.windows)
    if (chipTries < CHIP_TRIES && chipNeedsRetry(await read($, chip))) await refreshChip($)
    return next(e)
  })

  on('command.run', { command: 'usage-band' }, async $ => {
    const hidden = await update($, isHidden, value => !value)
    const why = chipError ? ` (tack chip: ${chipError})` : ''
    return { text: (hidden ? 'Usage band hidden.' : 'Usage band shown.') + why }
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const current = await read($, usage)
    if (e.props.hasSurvey || (await read($, isHidden))) return next(e)

    const { Box, Text } = $.ui.resolve(e)
    const now = await $.clock.now()
    const hasData = current.windows.length > 0 || current.contextPercent !== undefined

    return (
      <Box flexDirection="row" gap={3}>
        <Text color="cyan">{await read($, chip)}</Text>
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
