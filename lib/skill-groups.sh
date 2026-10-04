#!/usr/bin/env bash
# Skill groups (skill-groups.txt): which skills to install, from `tack config skill-groups
# --global` (default: every group). core is always included. Sourced by install.sh and
# lib/doctor.sh after lib/keys.sh; defines functions only.

# skill_groups_selected: prints the selected groups, comma-separated, core first.
skill_groups_selected() {
  local value
  value="$(key_get global skillGroups 2>/dev/null)" || value=all
  value="$(printf '%s' "$value" | tr -d ' ')"
  case ",$value," in *,all,*) value='process,stack' ;; esac
  printf 'core'
  case ",$value," in *,process,*) printf ', process' ;; esac
  case ",$value," in *,stack,*) printf ', stack' ;; esac
  printf '\n'
}

# skill_selected NAME: succeeds when NAME's group is selected; a skill missing from the file is
# treated as core, so a new skill is never dropped by accident.
skill_selected() {
  local name group='' skill rest
  # Plain bash: the installer and doctor also run where awk is not on the PATH.
  # IFS is set here: a caller may hold a different one (doctor's tool checks split on commas).
  while IFS=$' \t' read -r skill rest; do
    case "$skill" in '' | '#'*) continue ;; esac
    if [ "$skill" = "$1" ]; then name="$skill" group="${rest%% *}"; break; fi
  done < "$REPO/skill-groups.txt"
  [ -n "${name:-}" ] || group=core
  case "$group" in core) return 0 ;; esac
  case ", $(skill_groups_selected)," in *", $group,"*) return 0 ;; esac
  return 1
}
