# resources/ — prebraté zdroje

Lokálne, needitované kópie projektov z [ROADMAP.md](../ROADMAP.md) (sekcia
"Prebraté komponenty namiesto písania od nuly"), stiahnuté cez [fetch.sh](fetch.sh).
Slúžia na čítanie/experimentovanie a ako štartovací bod pre skutočný fork (ten vznikne
neskôr ako samostatný GitHub repozitár pod arkaysk, nie priamo v tomto priečinku).

**Netrackované v git-e** (`.gitignore`: `resources/*/`) — sú to cudzie repozitáre s vlastnou
históriou, netreba ich duplikovať v histórii `jihlavanka001`. Spusti `./fetch.sh` na stiahnutie,
zmaž priečinok konkrétneho projektu a spusti znova na refresh k najnovšiemu commitu.

| Priečinok | Projekt | Licencia | Etapa | Účel |
|---|---|---|---|---|
| `hyprland/` | [Hyprland](https://github.com/hyprwm/Hyprland) | BSD-3-Clause | C | skutočný fork point kompozitora |
| `hyprpanel/` | [HyprPanel](https://github.com/Jas-SinghFSU/HyprPanel) | MIT | U | fork ako štart pre panel/launcher/kontextové menu/notifikácie |
| `quickshell/` | [Quickshell](https://github.com/quickshell-mirror/quickshell) | LGPL-3.0 | U | záložná alternatíva k HyprPanel (QtQuick namiesto Astal/GTK) |
| `nwg-shell/` | [nwg-shell](https://github.com/nwg-piotr/nwg-shell) | MIT | U | ďalšia referencia pre panel/launcher UX (GTK3) |
| `cosmic-files/` | [cosmic-files](https://github.com/pop-os/cosmic-files) | **GPL-3.0-only** | D | fork point Data Manageru (Rust, udisks2, trash, view modes) |
| `cosmic-panel/` | [cosmic-panel](https://github.com/pop-os/cosmic-panel) | **GPL-3.0-only** | U (záloha) | Rust alternatíva k HyprPanel, ak sa uprednostní Rust nad Astal/GTK |
| `libcosmic/` | [libcosmic](https://github.com/pop-os/libcosmic) | MPL-2.0 | D | toolkit, od ktorého cosmic-files/cosmic-panel závisia |
| `gamescope/` | [gamescope](https://github.com/ValveSoftware/gamescope) | BSD-2-Clause | G | použiť ako je, nefork-ovať — fullscreen gaming session |
| `umu-launcher/` | [umu-launcher](https://github.com/Open-Wine-Components/umu-launcher) | GPL-3.0 | G | použiť ako externý proces, nefork-ovať |
| `bazzite/` | [Bazzite](https://github.com/ublue-os/bazzite) | zmiešané, overiť per súbor | 0, 9 | referencia pre Containerfile/justfile image pipeline |

## Ako s tým narábať ďalej

- **Referencia (čítať, neforkovat):** gamescope, umu-launcher, bazzite. Používajú sa ako externé
  nástroje/procesy alebo ako inšpirácia pre build pipeline, nie ako kód na úpravu.
- **Fork point (bude mať vlastný repo):** hyprland, hyprpanel (alebo quickshell/nwg-shell ako
  alternatíva), cosmic-files (alebo cosmic-panel ako alternatíva k hyprpanel).
- Pri GPL-3.0 projektoch (cosmic-files, cosmic-panel) platí: ak sa z nich stavia LatteOS modul,
  ten modul musí zostať GPL-3.0. Podrobnejšie odôvodnenie je v ROADMAP.md.
- `quickshell/`, `nwg-shell/`, `cosmic-panel/`, `libcosmic/` sú tu ako **porovnávacie alternatívy**
  k hlavnej voľbe (hyprpanel, cosmic-files) — neznamená to duplicitnú prácu, len rozhodovací podklad
  predtým, než sa v Etape U/D commitne k jednému základu.
