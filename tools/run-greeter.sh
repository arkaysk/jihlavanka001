#!/bin/bash
# Vývoj prihlasovacej obrazovky bez inštalácie a bez reštartu: latte-greeter v okne
# proti simulovanému greetd (účty test/kava a guest bez hesla, viď fake_greetd.py).
# Spustenie relácie sa len vypíše. Stav greetera ide do dočasného súboru.
DIR=$(dirname "$(readlink -f "$0")")
RUN=${XDG_RUNTIME_DIR:-/tmp}
SOCK=$RUN/latte-fake-greetd.sock
python3 "$DIR/fake_greetd.py" "$SOCK" &
FAKE=$!
trap 'kill $FAKE 2>/dev/null; rm -f "$SOCK"' EXIT
sleep 0.3
GREETD_SOCK=$SOCK LATTE_GREETER_WINDOWED=1 LATTEOS_GREETER_STATE=$RUN/latte-greeter-dev.json \
    GSK_RENDERER=cairo python3 "$DIR/../src/latte_greeter/app.py"
