// Minimal 'claude-code/testing' for running the mods' unit tests with Node (tests/mods-unit.sh):
// test() collects cases and runs them once the test file has been loaded; expect() covers the
// matchers the tests use. A failure sets a non-zero exit code.
import { isDeepStrictEqual } from 'node:util'

const cases = []
let scheduled = false

export function test(name, body) {
  cases.push({ name, body })
  if (!scheduled) {
    scheduled = true
    setTimeout(run, 0)
  }
}

async function run() {
  let failed = 0
  for (const { name, body } of cases) {
    try {
      await body()
      console.log(`  ✔ ${name}`)
    } catch (error) {
      failed += 1
      console.log(`  ✘ ${name}: ${error.message}`)
    }
  }
  console.log(`${cases.length - failed} passed, ${failed} failed`)
  process.exitCode = failed ? 1 : 0
}

function fail(message) {
  throw new Error(message)
}

export function expect(actual) {
  const show = value => JSON.stringify(value)
  return {
    toBe: expected => Object.is(actual, expected) || fail(`expected ${show(expected)}, got ${show(actual)}`),
    toEqual: expected => isDeepStrictEqual(actual, expected) || fail(`expected ${show(expected)}, got ${show(actual)}`),
    toBeUndefined: () => actual === undefined || fail(`expected undefined, got ${show(actual)}`),
  }
}
