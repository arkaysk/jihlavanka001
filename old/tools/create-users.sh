#!/bin/sh
# Vytvorí používateľov LatteOS arkay a kenshi. Sú to bežné účty bez práv správcu; každý má súkromný domov
# (len vlastník, 0700) a v ňom vlastný Kôš. Spúšťa sa ako root:
#   su -c 'sh tools/create-users.sh'
# Existujúci účet sa nemení. Na konci sa pýta heslo (bez neho sa nikto nedá prihlásiť). Iný zoznam
# (meno:celé meno, oddelené čiarkou):
#   USERS="anna:Anna Nováková,peter:Peter" sh tools/create-users.sh
# Po vytvorení sa používatelia objavia na prihlasovacej obrazovke (latte-greeter berie účty s UID od 1000).
set -e
[ "$(id -u)" = 0 ] || { echo "Spusti ako root." >&2; exit 1; }
USERS=${USERS:-"arkay:Arkay,kenshi:Kenshi"}

# meno:celé meno; položky sú oddelené čiarkou, aby celé meno mohlo mať medzeru
echo "$USERS" | tr ',' '\n' | while read -r entry; do
    [ -n "$entry" ] || continue
    name=${entry%%:*}
    real=${entry#*:}
    [ "$real" != "$entry" ] || real=$name

    if id "$name" >/dev/null 2>&1; then
        echo "$name: účet už existuje, nechávam ho tak"
    else
        useradd --create-home --shell /bin/bash --comment "$real" "$name"
        echo "$name: účet vytvorený"
    fi

    home=$(getent passwd "$name" | cut -d: -f6)
    # súkromný priestor: iný účet doň nevidí
    chmod 0700 "$home"
    # Kôš používateľa (freedesktop: ~/.local/share/Trash/{files,info}); v Správcovi súborov je to zložka „Kôš“ v jeho priestore
    for dir in .local .local/share .local/share/Trash .local/share/Trash/files .local/share/Trash/info; do
        install -d -m 0700 -o "$name" -g "$name" "$home/$dir"
    done
    command -v restorecon >/dev/null 2>&1 && restorecon -RF "$home"

    state=$(passwd -S "$name" 2>/dev/null | awk '{print $2}')
    case "$state" in
        L|LK)
            if [ -t 0 ]; then
                echo "Nastav heslo pre $name:"
                passwd "$name" || echo "$name: heslo sa nenastavilo, urob to neskôr: passwd $name"
            else
                echo "$name: nemá heslo, nastav ho: passwd $name"
            fi
            ;;
    esac
done
echo "Hotovo. Účty: $(getent passwd | awk -F: '$3 >= 1000 && $3 < 60000 {printf "%s ", $1}')"
