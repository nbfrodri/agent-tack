#!/usr/bin/env bash
# Guard rules for infrastructure and devices: kubectl delete, terraform destroy, dd to a device.
# Sourced by guard-bash.sh, which defines ask and resolve_path (guard-files.sh).

# kubectl delete, after any global flags such as -n or --context.
check_kubectl() {
  local skip=0 a
  for a in "$@"; do
    if [ "$skip" -eq 1 ]; then skip=0; continue; fi
    case "$a" in
      -n | --namespace | --context | --kubeconfig | --cluster | --user | -s | --server | --token | --as | --as-group | --request-timeout) skip=1 ;;
      -*) ;;
      delete) ask "kubectl delete removes cluster resources. Confirm the context and namespace."; return ;;
      *) return ;;
    esac
  done
}

# terraform or tofu destroy, also after -chdir, and apply -destroy.
check_terraform() {
  local name="$1" a sub=''
  shift
  for a in "$@"; do
    case "$a" in
      -*) [ -z "$sub" ] || case "$a" in -destroy) [ "$sub" != apply ] || ask "$name apply -destroy deletes infrastructure. Confirm the workspace and environment." ;; esac ;;
      *)
        [ -z "$sub" ] || continue
        sub="$a"
        [ "$sub" != destroy ] || ask "$name destroy deletes infrastructure. Confirm the workspace and environment." ;;
    esac
  done
}

# dd writing to a device; the null, zero and standard streams are not devices to protect.
check_dd() {
  local a target
  for a in "$@"; do
    case "$a" in
      of=*)
        target="$(resolve_path "${a#of=}")"
        case "$target" in
          /dev/null | /dev/zero | /dev/stdout | /dev/stderr | /dev/fd/*) ;;
          /dev/*) ask "dd writing to $target overwrites the device. Confirm it." ;;
        esac ;;
    esac
  done
}
