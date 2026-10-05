// Stand-in for the 'claude-code' module when the mods' unit tests run without Claude Code
// (tests/mods-unit.sh). The tests exercise exported pure functions; these only let the mod load.
export function atom(ref, initial) {
  return { ref, initial }
}

export async function read(_engine, cell) {
  return cell.initial
}

export async function update(_engine, cell, change) {
  return change(cell.initial)
}
