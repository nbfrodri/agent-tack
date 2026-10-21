#!/usr/bin/env bash
# Opt-in developer tool: Claude uses the existing HOME for login, installed
# configuration and session files. XDG directories are isolated per repetition.
set -u

usage() {
  printf 'Usage: run-trials.sh SCENARIO [N] [--keep]\n' >&2
  printf 'Scenarios: catalog, asks, usage, delegate, roles, delegate-fails, delegate-off\n' >&2
}

scenario=${1-}
if [[ -z $scenario ]]; then usage; exit 2; fi
case $scenario in
  catalog|asks|usage|delegate|roles|delegate-fails|delegate-off) ;;
  *) usage; exit 2 ;;
esac
shift

count=5
count_set=false
keep=false
for arg in "$@"; do
  if [[ $arg == --keep ]]; then
    keep=true
  elif [[ $arg =~ ^[1-9][0-9]*$ ]] && [[ $count_set == false ]]; then
    count=$arg
    count_set=true
  else
    usage
    exit 2
  fi
done

if ! command -v claude >/dev/null 2>&1; then
  printf 'run-trials.sh requires claude\n' >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  printf 'run-trials.sh requires jq\n' >&2
  exit 1
fi

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd) || exit 1
tack_bin=${TRIAL_TACK:-$script_dir/../../bin/tack}
if [[ ! -x $tack_bin ]]; then
  printf 'tack executable not found: %s\n' "$tack_bin" >&2
  exit 1
fi

tmp_root=$(mktemp -d "${TMPDIR:-/tmp}/tack-trials.XXXXXX") || exit 1
cleanup() {
  if [[ $keep == true ]]; then
    printf 'Kept trial files: %s\n' "$tmp_root"
  else
    rm -rf "$tmp_root"
  fi
}
trap cleanup EXIT HUP INT TERM

passed=0
for ((i = 1; i <= count; i++)); do
  run_dir=$tmp_root/$scenario-$i
  repo=$run_dir/repo
  mkdir -p "$repo" "$run_dir/state" "$run_dir/config" "$run_dir/data" "$run_dir/cache" || exit 1
  export XDG_STATE_HOME="$run_dir/state"
  export XDG_CONFIG_HOME="$run_dir/config"
  export XDG_DATA_HOME="$run_dir/data"
  export XDG_CACHE_HOME="$run_dir/cache"
  export GIT_CONFIG_NOSYSTEM=1
  (
    cd "$repo" || exit 1
    git init -q
    git config user.name 'Trial Runner'
    git config user.email 'trial@example.invalid'
    printf '# Trial repository\n' > README.md
    git add README.md
    git commit -qm 'test: initialize trial repository'
    "$tack_bin" enable >/dev/null
  ) || { printf '%s %s: miss (repo setup failed)\n' "$i" "$scenario"; continue; }

  case $scenario in
    catalog|asks)
      cat > "$repo/checkout.py" <<'EOF'
def checkout(cart, inventory):
    for item in cart:
        if inventory.get(item["sku"], 0) < item["quantity"]:
            return False
    return True
EOF
      ;;
    roles)
      printf 'def total(items):\n    return sum(items)\n' > "$repo/review_target.py"
      (cd "$repo" && git add review_target.py && git commit -qm 'test: add review target' && "$tack_bin" mode strict) || {
        printf '%s roles: miss (strict mode setup failed)\n' "$i"; continue;
      }
      ;;
    delegate|delegate-fails|delegate-off)
      for file_index in 1 2 3 4 5 6; do
        cat > "$repo/module$file_index.py" <<EOF
def calculate_$file_index(value):
    if value < 0:
        return 0
    return value * $file_index

def lookup_$file_index(items, key):
    for item in items:
        if item.get("id") == key:
            return item
    return None

def average_$file_index(values):
    return sum(values) / len(values)
EOF
      done
      if [[ $scenario != delegate-off ]]; then
        (cd "$repo" && "$tack_bin" mode strict) >/dev/null || {
          printf '%s %s: miss (strict mode setup failed)\n' "$i" "$scenario"; continue;
        }
      else
        (cd "$repo" && git config tack.crossDelegation off) || {
          printf '%s delegate-off: miss (config setup failed)\n' "$i"; continue;
        }
      fi
      ;;
  esac

  out=$run_dir/out.jsonl
  err=$run_dir/err.log
  case $scenario in
    catalog|asks)
      prompt='Make the checkout page load faster; I do not know what to use for that.'
      default_model=haiku
      ;;
    usage)
      # A reset five hours ahead, so the window is still open whenever the scenario runs.
      reset_at=$(date -u -d '+5 hours' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v+5H +%Y-%m-%dT%H:%M:%SZ)
      XDG_STATE_HOME=$run_dir/state "$tack_bin" usage set five_hour 70 "$reset_at" >/dev/null || {
        printf '%s usage: miss (usage setup failed)\n' "$i"; continue;
      }
      prompt='Add a README.md with one line describing this repo.'
      default_model=haiku
      ;;
    delegate|delegate-off)
      prompt='Review these files for bugs and write a one-paragraph summary of the riskiest function in each. Do not edit anything.'
      default_model=sonnet
      ;;
    roles)
      prompt='Use the code-reviewer agent to review my last commit before I push.'
      default_model=sonnet
      ;;
    delegate-fails)
      prompt='Delegate reading these six files to Codex and bring back a one-paragraph summary of the riskiest function in each.'
      default_model=sonnet
      ;;
  esac
  model=${TRIAL_MODEL:-$default_model}
  allow_args=()
  case $scenario in delegate|delegate-fails) allow_args=(--allowedTools "Bash(tack:*)" "Bash(codex:*)" "Bash(command:*)" "Bash(ls:*)" "Bash(cat:*)" "Bash(git:*)" "Bash(wc:*)") ;; esac

  if [[ $scenario == delegate-fails ]]; then
    fake_bin=$run_dir/fake-bin
    mkdir -p "$fake_bin"
    calls_log=$run_dir/codex-calls.log
    : > "$calls_log"
    cat > "$fake_bin/codex" <<'EOF'
#!/usr/bin/env bash
if [[ ${1-} == exec ]]; then
  printf '%s\n' "$*" >> "$CODEX_CALLS_LOG"
  printf '%s\n' '{"type":"thread.started","thread_id":"fake-session-1"}'
  printf '%s\n' '{"type":"error","message":"You have hit your usage limit. Try again later."}'
  printf '%s\n' '{"type":"turn.failed","error":{"message":"usage limit reached"}}'
  exit 1
fi
exit 0
EOF
    chmod +x "$fake_bin/codex"
    export CODEX_CALLS_LOG=$calls_log
    claude_path=$fake_bin:$PATH
  else
    claude_path=$PATH
  fi

  if ! (cd "$repo" && PATH="$claude_path" timeout 300 claude -p "$prompt" --model "$model" ${allow_args[@]+"${allow_args[@]}"} --output-format stream-json --verbose --permission-mode acceptEdits --max-turns 12 < /dev/null > "$out" 2> "$err"); then
    if [[ $scenario != delegate-fails ]]; then
      printf '%s %s: miss (Claude run failed)\n' "$i" "$scenario"
      continue
    fi
  fi

  blocks_jq='[.message.content[]?, .content[]?] | map(select(.type == "tool_use") | {name: .name, input: .input})'
  all_blocks=$(jq -c "$blocks_jq" "$out" 2>/dev/null | jq -s 'add // []' 2>/dev/null || printf '[]')
  commands=$(printf '%s\n' "$all_blocks" | jq -r '.[] | select(.name == "Bash") | .input.command // empty' 2>/dev/null)
  all_text=$(jq -r 'select(.type == "assistant") | [.message.content[]?, .content[]?] | map(select(.type == "text") | .text) | select(length > 0) | join("\\n")' "$out" 2>/dev/null)

  case $scenario in
    catalog)
      # Pass: it runs catalog discovery, showing it followed the set index.
      if printf '%s\n' "$commands" | grep -Fq 'tack set list'; then
        printf '%s catalog: ok (ran tack set list)\n' "$i"; passed=$((passed + 1))
      else
        printf '%s catalog: miss (no tack set list command)\n' "$i"
      fi
      ;;
    asks)
      # Pass: it suggests performance and activation for the vague request.
      if printf '%s' "$all_text" | grep -Eiq 'performance' && printf '%s' "$all_text" | grep -Fq 'tack set use'; then
        printf '%s asks: ok (mentioned performance and tack set use)\n' "$i"; passed=$((passed + 1))
      else
        printf '%s asks: miss (assistant text missing performance or tack set use)\n' "$i"
      fi
      ;;
    usage)
      # Pass: high usage triggers one Codex offer without repeating it on resume.
      first_offer=false
      if printf '%s' "$all_text" | grep -Eiq 'codex' && printf '%s' "$all_text" | grep -Eiq 'delegat|codex.*(could|can|use|help|ask)|offer'; then first_offer=true; fi
      session_id=$(jq -r 'select(.type == "result") | .session_id // empty' "$out" 2>/dev/null | tail -n 1)
      if [[ -z $session_id ]]; then
        printf '%s usage: miss (no session id; first offer=%s)\n' "$i" "$first_offer"
        continue
      fi
      out2=$run_dir/resume.jsonl
      err2=$run_dir/resume.err
      if ! (cd "$repo" && PATH="$claude_path" timeout 300 claude -p --resume "$session_id" 'Add a LICENSE file saying MIT.' --model "$model" --output-format stream-json --verbose --permission-mode acceptEdits --max-turns 12 < /dev/null > "$out2" 2> "$err2"); then
        printf '%s usage: miss (first offer=%s; resume failed)\n' "$i" "$first_offer"
        continue
      fi
      second_text=$(jq -r 'select(.type == "assistant") | [.message.content[]?, .content[]?] | map(select(.type == "text") | .text) | select(length > 0) | join("\\n")' "$out2" 2>/dev/null)
      second_offer=false
      if printf '%s' "$second_text" | grep -Eiq 'codex' && printf '%s' "$second_text" | grep -Eiq 'delegat|codex.*(could|can|use|help|ask)|offer'; then second_offer=true; fi
      printf '%s usage first: %s (Codex offer=%s)\n' "$i" "$([[ $first_offer == true ]] && printf ok || printf miss)" "$first_offer"
      printf '%s usage resume: %s (Codex offer=%s)\n' "$i" "$([[ $second_offer == false ]] && printf ok || printf miss)" "$second_offer"
      if [[ $first_offer == true && $second_offer == false ]]; then passed=$((passed + 1)); fi
      ;;
    delegate)
      # Pass: strict review invokes cross-delegate or Codex for bounded reading.
      if printf '%s\n' "$all_blocks" | jq -e 'any(.[]; .name == "Skill" and ((.input.skill // .input.name // .input) | tostring | test("cross-delegate"; "i")))' >/dev/null 2>&1; then
        printf '%s delegate: ok (used cross-delegate Skill)\n' "$i"; passed=$((passed + 1))
      elif printf '%s\n' "$commands" | grep -Fq 'codex exec'; then
        printf '%s delegate: ok (ran codex exec)\n' "$i"; passed=$((passed + 1))
      else
        printf '%s delegate: miss (no cross-delegate Skill or codex exec)\n' "$i"
      fi
      ;;
    roles)
      # Pass: it checks role availability or suggests the set providing the role.
      routed=false
      if printf '%s\n' "$commands" | grep -Fq 'tack set agent' || printf '%s' "$all_text" | grep -Fq 'tack set use review'; then routed=true; fi
      general_agent=false
      if printf '%s\n' "$all_blocks" | jq -e 'any(.[]; .name == "Agent" and .input.subagent_type == "general-purpose")' >/dev/null 2>&1; then general_agent=true; fi
      printf '%s roles: %s (set routing=%s; general-purpose Agent=%s)\n' "$i" "$([[ $routed == true ]] && printf ok || printf miss)" "$routed" "$general_agent"
      if [[ $routed == true ]]; then passed=$((passed + 1)); fi
      ;;
    delegate-fails)
      # Pass: one failed exec leads to a limit explanation and recovery choices.
      calls=0
      if [[ -f $calls_log ]]; then calls=$(awk '$1 == "exec" { n++ } END { print n + 0 }' "$calls_log"); fi
      limit=false
      if printf '%s' "$all_text" | grep -Eiq 'limit|codex stopped'; then limit=true; fi
      alternatives=0
      printf '%s' "$all_text" | grep -Eiq 'finish|myself' && alternatives=$((alternatives + 1))
      printf '%s' "$all_text" | grep -Eiq 'wait' && alternatives=$((alternatives + 1))
      printf '%s' "$all_text" | grep -Eiq 'resume' && alternatives=$((alternatives + 1))
      printf '%s' "$all_text" | grep -Eiq 'discard|drop' && alternatives=$((alternatives + 1))
      call_ok=false
      [[ $calls -eq 1 ]] && call_ok=true
      response_ok=false
      [[ $limit == true && $alternatives -ge 2 ]] && response_ok=true
      if [[ $call_ok == true && $response_ok == true ]]; then
        printf '%s delegate-fails: ok (one exec; limit response with %s alternatives)\n' "$i" "$alternatives"
        passed=$((passed + 1))
      else
        printf '%s delegate-fails: miss (%s; %s)\n' "$i" "$([[ $call_ok == true ]] && printf 'one exec call' || printf 'exec call count was not one')" "$([[ $response_ok == true ]] && printf 'limit response and alternatives present' || printf 'limit response or two alternatives missing')"
      fi
      ;;
    delegate-off)
      # Pass: disabled cross-delegation prevents any codex exec command.
      if printf '%s\n' "$commands" | grep -Fq 'codex exec'; then
        printf '%s delegate-off: miss (ran codex exec)\n' "$i"
      else
        printf '%s delegate-off: ok (no codex exec command)\n' "$i"; passed=$((passed + 1))
      fi
      ;;
  esac
done

printf 'Scenario %s: %s of %s\n' "$scenario" "$passed" "$count"
