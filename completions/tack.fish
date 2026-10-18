# Dynamic candidates, with file completion disabled in every context.
function __tack_candidates
    set -l words (commandline -opc)
    set -l kind
    set -l extra
    set -l args
    if test (count $words) -eq 1
        set kind commands
    else
        for word in $words[3..-1]
            switch "$words[2]:$word"
                case 'config:--get' 'config:--unset' 'config:--global' 'set:--global'
                    continue
            end
            set -a args $word
        end
        switch "$words[2]:"(count $args)
            case set:0
                set kind set-commands
            case set:1
                switch $args[1]
                    case use
                        set kind sets-inactive
                        set extra --global
                    case drop
                        set kind sets-active
                        set extra --global
                    case show skip
                        set kind sets-all
                    case agent
                        set kind roles
                end
            case config:0
                set kind features
                set extra --get --unset --global
            case config:1
                set kind feature-values
                set extra --get --unset --global
            case mode:0
                set kind modes
            case models:0
                set kind tiers
            case usage:0
                set extra set get record statusline threshold hint
            case usage:1
                if contains -- $args[1] set get record statusline threshold hint
                    set kind usage-kinds
                end
            case branches:0
                set extra --apply
            case completion:0
                set extra bash zsh fish
        end
    end
    if test (count $kind) -gt 0
        command tack __complete $kind $args[1] 2>/dev/null
    end
    if test (count $extra) -gt 0
        printf '%s\n' $extra
    end
end
complete -c tack -f -a '(__tack_candidates)'
