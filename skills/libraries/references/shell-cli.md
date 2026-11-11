# Shell scripts and command-line tools

A script that others run depends only on what their machines have: POSIX tools and the shell. Each tool below is a dependency to declare and to check for at the start of the script. These are programs installed with the system's package manager; none was checked in a registry.

## In and around shell scripts
| Need | Default | Alternatives | Notes |
| --- | --- | --- | --- |
| Static analysis | ShellCheck | | |
| Formatting | shfmt | | |
| Tests | Bats | | With bats-support and bats-assert |
| JSON | jq | | |
| YAML, TOML, XML | yq | | Two different programs share this name: check which one is installed |
| Searching text | ripgrep | `grep` | `grep` in scripts others run |
| Finding files | fd | `find` | `find` in scripts others run |
| Interactive selection | fzf | | |
| Prompts and styled output | gum | | |
| Running in parallel | `xargs -P` | GNU parallel | |
| Benchmarks | hyperfine | | |
| Task runner | just | `make` | |

## Building a command-line program
Past a few hundred lines, or with nested data, write it in a language with tests and types. The argument parser for each is in that language's file: `python.md` (Typer), `go.md` (Cobra), `rust.md` (clap), `js-backend.md` (commander, Clack, Ink), `dotnet.md` (`System.CommandLine`, Spectre.Console).
