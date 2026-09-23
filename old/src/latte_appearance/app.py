#!/usr/bin/env python3
"""latte-appearance: vzhľad LatteOS z jedného miesta (služba a príkazový riadok).

    latte-appearance serve                služba: vynucuje vzhľad a obsluhuje portál
    latte-appearance apply                jednorazovo zapíše všetky vrstvy
    latte-appearance status               stav vrstiev, motív, problémy
    latte-appearance show                 účinné hodnoty a odkiaľ sú
    latte-appearance set KĽÚČ HODNOTA     zmení nastavenie (overí ho podľa schémy)
    latte-appearance reset [KĽÚČ...]      vráti predvolené (bez kľúčov všetko)
    latte-appearance themes               nainštalované motívy
    latte-appearance profiles [APP_ID]    na akej úrovni sa vzhľad vynúti pre nástroje a aplikácie
    latte-appearance release              odstráni všetko, čo LatteOS spravuje mimo svojich súborov
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from latte_common import appearance, appprofiles, settings  # noqa: E402

LEVEL_TEXT = {"enforced": "vynútené", "aligned": "zosúladené", "recommended": "odporúčané", "planned": "plánované"}
STATE_TEXT = {"ok": "v poriadku", "missing": "chýba", "drift": "zmenené mimo Nastavení"}


def parse_value(key, text):
    """Text z príkazového riadku na hodnotu podľa typu kľúča."""
    if key.type == "bool":
        lowered = text.strip().lower()
        if lowered in ("1", "true", "yes", "ano", "áno", "zap", "on"):
            return True
        if lowered in ("0", "false", "no", "nie", "vyp", "off"):
            return False
        raise settings.SettingsError("%s: očakáva sa áno/nie" % key.id)
    if key.type == "int":
        try:
            return int(text)
        except ValueError:
            raise settings.SettingsError("%s: očakáva sa celé číslo" % key.id) from None
    if key.type == "float":
        try:
            return float(text.replace(",", "."))
        except ValueError:
            raise settings.SettingsError("%s: očakáva sa číslo" % key.id) from None
    return text


def cmd_show(store):
    domain = store.domain
    for section, title, keys in domain.grouped():
        print("[%s]" % title)
        for key in keys:
            value = store.get(key.id)
            print("  %-24s %-22s %s%s" % (key.id, "\"%s\"" % value if isinstance(value, str) else value,
                                          {"default": "", "user": "(nastavené)", "admin": "(správca)"}[store.source(key.id)],
                                          "   " + key.label if key.label else ""))
    for problem in store.problems:
        print("PROBLÉM:", problem)


def cmd_status(store):
    tokens = appearance.resolve(store.values())
    tokens.problems = list(store.problems) + tokens.problems
    print("Motív: %s, režim %s, akcent %s%s" % (tokens.theme_id, tokens.scheme, tokens.accent,
                                              " (vlastný)" if store.get("color.accent") else ""))
    print()
    actions = appearance.plan(tokens)
    states = {}
    for adapter, path, state in appearance.check(actions):
        states.setdefault(adapter, []).append((path, state))
    for adapter in appearance.ADAPTERS:
        rows = states.get(adapter.name)
        if adapter.level == "planned":
            detail = "zatiaľ nie je"
        elif rows:
            worst = "ok" if all(s == "ok" for _p, s in rows) else ("drift" if any(s == "drift" for _p, s in rows) else "missing")
            detail = STATE_TEXT[worst]
        else:
            detail = "riadi služba za behu"
        print("  %-12s %-12s %-22s %s" % (adapter.name, LEVEL_TEXT[adapter.level], detail, adapter.covers))
        for path, state in rows or []:
            if state != "ok":
                print("      %s: %s" % (STATE_TEXT[state], path))
    for problem in tokens.problems:
        print("\nPROBLÉM:", problem)
    return 0 if all(s == "ok" for rows in states.values() for _p, s in rows) and not tokens.problems else 1


def cmd_profiles(app_id):
    profiles = appprofiles.load()
    if app_id:
        profile = profiles.for_app(app_id)
        rows = [profile]
    else:
        rows = list(profiles.toolkits.values()) + profiles.apps
    for profile in rows:
        kind = "aplikácia" if profile.match else "nástroj"
        badge = "  [%s]" % profile.badge if profile.badge else ""
        print("%-10s %-30s %-11s %s%s" % (kind, profile.name, appprofiles.LEVEL_TITLES[profile.level],
                                          "+".join(profile.fallback) or "-", badge))
        if app_id and profile.note:
            print("           %s" % profile.note)
    for problem in profiles.problems:
        print("PROBLÉM:", problem, file=sys.stderr)
    return 1 if profiles.problems else 0


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, args = argv[0], argv[1:]
    registry = settings.Registry()
    store = registry.store("appearance")

    if cmd == "serve":
        from latte_appearance.service import Service
        Service().run()
        return 0
    if cmd == "apply":
        tokens = appearance.current_tokens(store)
        for problem in tokens.problems:
            print("PROBLÉM:", problem, file=sys.stderr)
        changed = appearance.apply(appearance.plan(tokens))
        print("Zapísané: %s" % (", ".join(changed) if changed else "nič, všetko už zodpovedá nastaveniam"))
        return 0
    if cmd == "status":
        return cmd_status(store)
    if cmd == "show":
        cmd_show(store)
        return 0
    if cmd == "set" and len(args) == 2:
        key = store.domain.key(args[0])
        store.set(args[0], parse_value(key, args[1]))
        print("%s = %r" % (args[0], store.get(args[0])))
        return 0
    if cmd == "reset":
        store.reset(*(args or list(store.domain.keys)))
        print("Vrátené na predvolené:", ", ".join(args) if args else "všetko")
        return 0
    if cmd == "themes":
        themes, problems = appearance.list_themes()
        for theme in themes:
            print("%-14s %-16s %s  [%s]" % (theme.id, theme.name, theme.description, ", ".join(theme.variants)))
        for problem in problems:
            print("PROBLÉM:", problem, file=sys.stderr)
        return 0
    if cmd == "profiles":
        return cmd_profiles(args[0] if args else None)
    if cmd == "release":
        tokens = appearance.current_tokens(store)
        changed = appearance.release(appearance.plan(tokens))
        print("Odstránené alebo upravené: %s" % (", ".join(changed) if changed else "nič"))
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except settings.SettingsError as err:
        print("latte-appearance:", err, file=sys.stderr)
        sys.exit(1)
