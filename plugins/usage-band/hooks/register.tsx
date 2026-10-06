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
      const config = await $.process.run(['tack', 'config', 'unleash-max-cost'], { timeoutMs: 5000 })
      limitUsd = mode.exitCode === 0 && config.exitCode === 0 ? costLimit(mode.stdout, config.stdout) : undefined
    } catch {
      limitUsd = undefined
    }
    await refreshChip($)
    return next(e)
  })

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
