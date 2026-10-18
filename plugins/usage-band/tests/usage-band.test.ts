import { expect, test } from 'claude-code/testing'

import { bar, chipNeedsRetry, colorFor, contextPercent, costLimit, crossedDelegation, crossedWarning, modeChip, overBudget, resetLabel, thresholdFrom, toUsage } from '../hooks/register'
import { register } from '../hooks/register'
import type { Engine } from 'claude-code'

test('unchanged context refreshes after two minutes and failed refreshes retry', async () => {
  const handlers: Record<string, Function> = {}
  register(((event: string, ...args: Function[]) => { handlers[event] = args[args.length - 1] }) as never)
  let now = 1000
  let exitCode = 0
  let throws = false
  let calls = 0
  const engine = {
    clock: { now: async () => now },
    process: { run: async (args: string[], options: { timeoutMs: number }) => {
      if (args[3] === 'context') {
        expect(options.timeoutMs).toBe(5000)
        calls += 1
        if (throws) throw new Error('unavailable')
      }
      return { exitCode, stdout: 'auto', stderr: '' }
    } },
    ui: { toast: () => {} },
  } as unknown as Engine
  const measure = (percent = 62) => handlers['session.measure'](engine,
    { context: { percent }, rateLimits: [] }, async () => {})
  await measure()
  await measure()
  expect(calls).toBe(1)
  now += 120000
  exitCode = 1
  await measure()
  expect(calls).toBe(2)
  throws = true
  await measure()
  expect(calls).toBe(3)
  throws = false
  exitCode = 0
  await measure()
  await measure()
  expect(calls).toBe(4)
  now += 119999
  await measure()
  expect(calls).toBe(4)
  await measure(63)
  expect(calls).toBe(5)
})

test('context percentage is finite, rounded and clamped', () => {
  expect(contextPercent(61.8)).toBe(62)
  expect(contextPercent(-2)).toBe(0)
  expect(contextPercent(120)).toBe(100)
  expect(contextPercent(undefined)).toBeUndefined()
  expect(contextPercent(NaN)).toBeUndefined()
  expect(contextPercent(Infinity)).toBeUndefined()
})

test('the offer to delegate starts at the percentage tack prints, or not at all', () => {
  expect(thresholdFrom('50\n')).toBe(50)
  expect(thresholdFrom('')).toBeUndefined()
  expect(thresholdFrom('off')).toBeUndefined()
  expect(thresholdFrom('0')).toBeUndefined()
  expect(thresholdFrom('101')).toBeUndefined()
})

test('the delegation message appears once, when the 5h window crosses the percentage', () => {
  const low = [{ kind: 'five_hour', percentUsed: 40 }]
  const high = [{ kind: 'five_hour', percentUsed: 52 }]
  expect(crossedDelegation(low, high, 50)).toBe('5h usage passed 50%: ask the assistant to hand tasks to Codex (cross-delegate)')
  expect(crossedDelegation(high, [{ kind: 'five_hour', percentUsed: 60 }], 50)).toBeUndefined()
  expect(crossedDelegation(low, [{ kind: 'five_hour', percentUsed: 45 }], 50)).toBeUndefined()
  expect(crossedDelegation([], high, 50)?.startsWith('5h usage passed 50%')).toBe(true)
  expect(crossedDelegation(low, high, undefined)).toBeUndefined()
  expect(crossedDelegation([{ kind: 'spend_limit', percentUsed: 10 }], [{ kind: 'spend_limit', percentUsed: 90 }], 50)).toBeUndefined()
})

test('the weekly window gets its own message at the same percentage', () => {
  const low = [{ kind: 'five_hour', percentUsed: 10 }, { kind: 'seven_day', percentUsed: 45 }]
  const high = [{ kind: 'five_hour', percentUsed: 12 }, { kind: 'seven_day', percentUsed: 51 }]
  expect(crossedDelegation(low, high, 50)).toBe('7d usage passed 50%: ask the assistant to hand tasks to Codex (cross-delegate)')
  expect(crossedDelegation(high, [{ kind: 'five_hour', percentUsed: 13 }, { kind: 'seven_day', percentUsed: 60 }], 50)).toBeUndefined()
})

test('the message returns after the window resets and usage climbs again', () => {
  const high = [{ kind: 'five_hour', percentUsed: 70 }]
  const fresh = [{ kind: 'five_hour', percentUsed: 3 }]
  expect(crossedDelegation(high, fresh, 50)).toBeUndefined()
  expect(crossedDelegation(fresh, [{ kind: 'five_hour', percentUsed: 51 }], 50)?.startsWith('5h usage passed 50%')).toBe(true)
})


test('mode chip names the active mode, or off when tack is not enabled', () => {
  expect(modeChip(0, 'auto (default)\n')).toBe('tack · auto')
  expect(modeChip(0, 'unleash (local)')).toBe('tack · unleash')
  expect(modeChip(1, 'auto (default)')).toBe('tack · off')
})

test('mode chip says it does not know when tack could not answer', () => {
  expect(modeChip(127, '')).toBe('tack · ?')
  expect(modeChip(2, '')).toBe('tack · ?')
  expect(modeChip(0, '')).toBe('tack · ?')
})

test('an unknown or pending chip is asked again, a known one is not', () => {
  expect(chipNeedsRetry('tack · …')).toBe(true)
  expect(chipNeedsRetry('tack · ?')).toBe(true)
  expect(chipNeedsRetry('tack · off')).toBe(false)
  expect(chipNeedsRetry('tack · auto')).toBe(false)
})

test('cost limit applies only in project-only modes with a positive amount', () => {
  expect(costLimit('WARNING: unleash mode is active\nMode unleash rules:', '5 (local)\n')).toBe(5)
  expect(costLimit('WARNING: unleash mode is active', '2.50 (global)')).toBe(2.5)
  expect(costLimit('Mode lite rules:', '5 (local)')).toBeUndefined()
  expect(costLimit('WARNING: unleash mode is active', 'none (default)')).toBeUndefined()
})

test('over budget once the cost reaches the limit', () => {
  expect(overBudget(4.99, 5)).toBe(false)
  expect(overBudget(5, 5)).toBe(true)
  expect(overBudget(undefined, 5)).toBe(false)
  expect(overBudget(9, undefined)).toBe(false)
})

test('bar fills one cell per ten percent and clamps', () => {
  expect(bar(0)).toBe('░░░░░░░░░░')
  expect(bar(68)).toBe('███████░░░')
  expect(bar(140)).toBe('██████████')
})

test('color warns at 70 and alerts at 90', () => {
  expect(colorFor(69)).toBe('green')
  expect(colorFor(70)).toBe('yellow')
  expect(colorFor(90)).toBe('red')
})

test('reset label shows the time today and the weekday later', () => {
  const now = new Date(2026, 9, 4, 12, 0).getTime()
  expect(resetLabel(new Date(2026, 9, 4, 17, 40).toISOString(), now)).toBe('resets 17:40')
  expect(resetLabel(new Date(2026, 9, 5, 9, 5).toISOString(), now)).toBe('resets Mon 09:05')
  expect(resetLabel(undefined, now)).toBe('')
})

test('warns once when a window crosses 80 or 90 percent', () => {
  const before = [{ kind: 'five_hour', percentUsed: 79 }]
  expect(crossedWarning(before, [{ kind: 'five_hour', percentUsed: 81 }])).toBe('5h usage passed 80%')
  expect(crossedWarning([{ kind: 'five_hour', percentUsed: 81 }], [{ kind: 'five_hour', percentUsed: 85 }])).toBeUndefined()
  expect(crossedWarning([{ kind: 'seven_day', percentUsed: 70 }], [{ kind: 'seven_day', percentUsed: 95 }])).toBe('7d usage passed 90%')
})

test('usage keeps the windows, context fill and cost', () => {
  const usage = toUsage({ window: 200000, percent: 42 }, [{ kind: 'seven_day', percentUsed: 31, resetsAt: 'x' }], { usd: 1.5 } as never)
  expect(usage).toEqual({ windows: [{ kind: 'seven_day', percentUsed: 31, resetsAt: 'x' }], contextPercent: 42, costUsd: 1.5 })
})
