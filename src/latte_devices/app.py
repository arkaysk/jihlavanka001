#!/usr/bin/env python3
"""latte-devices: Správca zariadení z príkazového riadka.

    latte-devices list [--json]                       všetok hardvér po skupinách
    latte-devices status [--json] [--all]             čo funguje a čo nie (ovládač, firmvér, balík)
    latte-devices base [--json] [--all]               stav metabalíka latteos-base na tomto stroji
    latte-devices display list                        monitory, ich režimy a nastavenie
    latte-devices display set VÝSTUP ROZLÍŠENIE[@Hz] [--scale 1.5] [--transform normal] [--save]
    latte-devices display apply                       použije uložené voľby (volá sa pri prihlásení)
    latte-devices display safe                        najvyššie bezpečné rozlíšenie (volá sa pred prihlasovacou obrazovkou)

Rovnaké funkcie používajú Nastavenia (Hardvér › Obrazovky) a Správca zdrojov v lište.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from latte_common import displays, hardware, hwbase, hwstatus, outputs  # noqa: E402


def cmd_list(args):
    inv = hardware.scan()
    if args.json:
        print(json.dumps({
            "groups": [{"id": gid, "title": title, "items": [
                {"key": i.key, "name": i.name, "detail": i.detail, "status": i.status, "settings": i.settings_uri}
                for i in items]} for gid, title, items in inv.groups()],
            "problems": inv.problems}, ensure_ascii=False, indent=2))
        return 0
    for gid, title, items in inv.groups():
        print("%s (%d)" % (title, len(items)))
        for item in items:
            print("  %-42s %s%s" % (item.name, item.detail, "  [%s]" % item.status if item.status else ""))
    for problem in inv.problems:
        print("! " + problem, file=sys.stderr)
    return 0


def cmd_status(args):
    """Bod H.2: stav každého zariadenia. Nič sa neinštaluje, len sa povie, čo chýba."""
    inv = hardware.scan()
    report = hwstatus.evaluate(inv)
    shown = report.statuses if args.all else report.faults
    if args.json:
        print(json.dumps({
            "summary": report.summary(),
            "devices": [{"group": s.group, "key": s.key, "name": s.name, "state": s.state,
                         "state_title": s.title, "reason": s.reason, "packages": list(s.packages),
                         "repo": s.repo, "unclaimed": s.unclaimed} for s in shown],
            "problems": report.problems + inv.problems}, ensure_ascii=False, indent=2))
        return 0
    print(report.summary())
    for status in sorted(shown, key=lambda s: (hwstatus.STATE_ORDER[s.state], s.group, s.name)):
        print("  %-21s %-38s %s" % (status.title, status.name, hardware.GROUPS[status.group][0]))
        if status.reason:
            print("        %s" % status.reason)
        if status.packages:
            print("        doplní: %s%s" % (" ".join(status.packages),
                                            "  (repozitár %s)" % status.repo if status.repo else ""))
    for problem in report.problems + inv.problems:
        print("! " + problem, file=sys.stderr)
    return 0


def cmd_base(args):
    """Bod H.1: zoznam latteos-base verzus skutočný stav stroja."""
    try:
        report = hwbase.check()
    except hwbase.BaseError as err:
        print("latte-devices:", err, file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps({
            "id": report.plan.id, "summary": report.summary(), "complete": report.complete,
            "groups": [{"id": g.id, "title": g.title, "why": g.why, "devices": list(g.devices),
                        "packages": [{"name": p.name, "required": p.required, "repo": p.repo,
                                      "state": report.state(p.name)} for p in g.packages]}
                       for g in report.plan.groups],
            "repos": [{"id": rid, "title": repo.title, "enabled": report.repo_enabled(rid),
                       "brings": list(report.repo_brings(rid)), "enable": repo.enable_command(),
                       "note": repo.note} for rid, repo in sorted(report.plan.repos.items())],
            "commands": report.install_commands(),
            "problems": report.problems}, ensure_ascii=False, indent=2))
        return 0
    print("%s — %s" % (report.plan.title or report.plan.id, report.summary()))
    for group in report.plan.groups:
        packages = group.packages if args.all else [
            p for p in group.packages if report.state(p.name) != "installed"]
        if not packages:
            continue
        print("\n%s" % group.title)
        if group.why and not args.all:
            print("  %s" % group.why)
        for package in packages:
            mark = "povinné" if package.required else "voliteľné"
            print("  %-34s %-24s %s" % (package.name, hwbase.STATE_TITLES[report.state(package.name)], mark))
    if report.plan.repos:
        print("\nCudzie repozitáre (LatteOS ich pozná, ale sám nezapína)")
        for rid, repo in sorted(report.plan.repos.items()):
            on = report.repo_enabled(rid)
            print("  %-22s %s" % (repo.title, "zapnutý" if on else "vypnutý"))
            print("        prinesie: %s" % ", ".join(report.repo_brings(rid) or ("nič zo zoznamu",)))
            if not on and repo.enable_command():
                print("        zapne sa: %s" % repo.enable_command())
    commands = report.install_commands()
    if commands:
        print("\nDoplnenie (spustí sa ručne, LatteOS nič neinštaluje samo):")
        for command in commands:
            print("  " + command)
    for problem in report.problems:
        print("! " + problem, file=sys.stderr)
    return 0


def cmd_display_list(_args):
    heads = outputs.read()
    for ident, head in displays.identify(heads).items():
        print("%s  (%s)  id: %s" % (displays.title(head), head.name, ident))
        print("  teraz: %s, otočenie %s" % (displays.summary(head), outputs.TRANSFORMS.get(head.transform, "?")))
        recommended = displays.recommended_resolution(head)
        for width, height in displays.resolutions(head):
            rates = ", ".join(displays.format_rate(r) for r in displays.rates(head, width, height))
            mark = "  (odporúčané)" if (width, height) == recommended else ""
            print("  %-12s %s%s" % (displays.format_resolution(width, height), rates, mark))
    return 0


def parse_mode(text):
    m = re.match(r"^(\d+)x(\d+)(?:@([\d.,]+))?$", text)
    if not m:
        raise ValueError("rozlíšenie má tvar 1920x1080 alebo 1920x1080@60")
    rate = int(round(float(m.group(3).replace(",", ".")) * 1000)) if m.group(3) else None
    return int(m.group(1)), int(m.group(2)), rate


def cmd_display_set(args):
    try:
        width, height, rate = parse_mode(args.mode)
    except ValueError as err:
        print("latte-devices:", err, file=sys.stderr)
        return 2
    with outputs.Client() as client:
        heads = {h.name: h for h in client.monitors()}
        head = heads.get(args.output)
        if head is None:
            print("latte-devices: monitor %s neexistuje (sú: %s)" % (args.output, ", ".join(sorted(heads))), file=sys.stderr)
            return 2
        if (width, height) not in displays.resolutions(head):
            print("latte-devices: %s nepodporuje %s" % (args.output, displays.format_resolution(width, height)), file=sys.stderr)
            return 2
        refresh = displays.pick_rate(head, width, height, rate if rate else (head.current.refresh if head.current else None))
        scale = args.scale if args.scale is not None else head.scale
        transform = args.transform or outputs.TRANSFORMS.get(head.transform, "normal")
        change = displays.change_for(head, width, height, refresh, scale, transform)
        error = client.apply({head.name: change}) if change else None
        ident = next(i for i, h in displays.identify(list(heads.values())).items() if h.name == head.name)
    if error:
        print("latte-devices:", error, file=sys.stderr)
        return 1
    print("%s: %s, %s, %s" % (args.output, displays.format_resolution(width, height), displays.format_rate(refresh),
                              displays.format_scale(scale)))
    if args.save:
        displays.save_monitor(ident, width, height, refresh, scale, transform)
        print("uložené do %s" % displays.config_path())
    return 0


def cmd_display_apply(_args):
    try:
        messages = displays.apply_saved()
    except outputs.OutputsError as err:
        print("latte-devices:", err, file=sys.stderr)
        return 1
    for message in messages:
        print("latte-devices:", message, file=sys.stderr)
    return 1 if messages else 0


def cmd_display_safe(_args):
    try:
        messages = displays.apply_safe()
    except outputs.OutputsError as err:
        print("latte-devices:", err, file=sys.stderr)
        return 1
    for message in messages:
        print("latte-devices:", message, file=sys.stderr)
    return 1 if messages else 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="latte-devices", description="Správca zariadení LatteOS")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("list", help="všetok hardvér po skupinách")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_list)
    p = sub.add_parser("status", help="čo funguje a čo nie")
    p.add_argument("--json", action="store_true")
    p.add_argument("--all", action="store_true", help="aj zariadenia, ktoré fungujú")
    p.set_defaults(fn=cmd_status)
    p = sub.add_parser("base", help="stav metabalíka latteos-base")
    p.add_argument("--json", action="store_true")
    p.add_argument("--all", action="store_true", help="aj balíky, ktoré sú nainštalované")
    p.set_defaults(fn=cmd_base)
    display = sub.add_parser("display", help="monitory").add_subparsers(dest="action", required=True)
    display.add_parser("list", help="monitory a ich režimy").set_defaults(fn=cmd_display_list)
    p = display.add_parser("set", help="zmení režim monitora")
    p.add_argument("output")
    p.add_argument("mode", help="napr. 1920x1080 alebo 1920x1080@60")
    p.add_argument("--scale", type=float)
    p.add_argument("--transform", choices=displays.TRANSFORMS)
    p.add_argument("--save", action="store_true", help="uloží voľbu, aby sa použila aj pri ďalšom prihlásení")
    p.set_defaults(fn=cmd_display_set)
    display.add_parser("apply", help="použije uložené voľby").set_defaults(fn=cmd_display_apply)
    display.add_parser("safe", help="nastaví najvyššie bezpečné rozlíšenie (prihlasovacia obrazovka)") \
        .set_defaults(fn=cmd_display_safe)
    args = parser.parse_args(argv)
    try:
        return args.fn(args)
    except outputs.OutputsError as err:
        print("latte-devices:", err, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
