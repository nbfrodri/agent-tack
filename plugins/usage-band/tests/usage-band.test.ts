import { expect, test } from 'claude-code/testing'

import { bar, colorFor, costLimit, crossedWarning, modeChip, overBudget, resetLabel, toUsage } from '../hooks/register'

test('mode chip names the active mode, or off when tack is not enabled', () => {
  expect(modeChip(0, 'auto (default)\n')).toBe('tack · auto')
  expect(modeChip(0, 'unleash (local)')).toBe('tack · unleash')
  expect(modeChip(1, 'auto (default)')).toBe('tack · off')
  expect(modeChip(0, '')).toBe('tack · off')
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
