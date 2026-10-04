import { expect, test } from 'claude-code/testing'

import { clock, kindOf, statusOf, summarize } from '../hooks/register'

test('summary picks the most telling field and flattens whitespace', () => {
  expect(summarize({ tool: 'Bash', command: 'git status\n  --short' })).toBe('git status --short')
  expect(summarize({ tool: 'Skill', skill: 'dev-workflow' })).toBe('dev-workflow')
  expect(summarize({ tool: 'Read', file_path: '/repo/a.ts' })).toBe('/repo/a.ts')
  expect(summarize({ tool: 'X' })).toBe('')
  expect(summarize(undefined)).toBe('')
})

test('skills and subagents are told apart from plain tools', () => {
  expect(kindOf('Skill')).toBe('skill')
  expect(kindOf('Agent')).toBe('subagent')
  expect(kindOf('Bash')).toBe('tool')
})

test('status reflects denials and errors', () => {
  expect(statusOf({ deny: 'guard said no' })).toBe('denied')
  expect(statusOf({ isError: true })).toBe('error')
  expect(statusOf({ isError: false })).toBe('ok')
})

test('clock prints a zero-padded local time', () => {
  expect(clock(new Date(2026, 9, 4, 9, 5, 7).getTime())).toBe('09:05:07')
})
