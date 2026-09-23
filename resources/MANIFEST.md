# resources/ — prebraté zdroje z technologického radaru

Zdroj výberu: [inspo/LatteOS – technologický radar 2026.md](../inspo/LatteOS%20–%20technologický%20radar%202026.md).
Stiahnuté sú iba projekty s verdiktom **Základ / Prebrať / forknúť** a projekty zo stĺpca
„Prebrať z“. Verdikty **Inšpirácia / Sledovať / Konkurencia** (macOS 27, Windows 11,
Barney, Aluminium OS, CachyOS, niri) sa nesťahujú.

```
resources/
  fetch.sh      stiahne všetko (./fetch.sh) alebo vybrané (./fetch.sh hyprland labwc)
  MANIFEST.md   tento súbor
  patches/      naše patche nad upstreamom (trackované v gite)
  upstream/     plytké git klony (NEtrackované), commity v upstream/COMMITS.txt
  docs/         uložené články z radaru (NEtrackované)
```

Stav k 23. 9. 2026: stiahnutých 31 repozitárov (~1,1 GB) a 10 článkov.

## Repozitáre (`upstream/`)

| Priečinok | Projekt | Licencia | Radar | Použitie v LatteOS |
|---|---|---|---|---|
| `hyprland` | [Hyprland](https://github.com/hyprwm/Hyprland) `main` (+ tag v0.56.2) | BSD-3 | Základ | kompozitor NORMAL režimu, **bez forku**, len [patch](patches/README.md) + Lua modul |
| `aquamarine` | [aquamarine](https://github.com/hyprwm/aquamarine) | BSD-3 | Základ | DRM/KMS backend Hyprlandu (miesto pre prípadné VM opravy) |
| `xdg-desktop-portal-hyprland` | [xdph](https://github.com/hyprwm/xdg-desktop-portal-hyprland) | BSD-3 | Prebrať | zdieľanie obrazovky (Discord, OBS) |
| `hyprlock` | [hyprlock](https://github.com/hyprwm/hyprlock) | BSD-3 | Prebrať z | zamknutie obrazovky |
| `hypr-darkwindow` | [Hypr-DarkWindow](https://github.com/micha4w/Hypr-DarkWindow) | MIT | Prebrať z | vzor pre shadery okien (témy) |
| `hyprwindowshade` | [HyprWindowShade](https://github.com/ManofJELLO/HyprWindowShade) | MIT | Prebrať z | vzor pre shadery okien (témy) |
| `labwc` | [labwc](https://github.com/labwc/labwc) 0.20.2 | GPL-2.0 | núdzový režim | kompozitor **SAFE režimu** (pixman, bez GPU); vo Fedore 44 ako balík |
| `wlroots` | [wlroots](https://gitlab.freedesktop.org/wlroots/wlroots) 0.21-dev | MIT | — | knižnica pod labwc; vmwgfx patch pre SAFE s GL |
| `dankmaterialshell` | [DankMaterialShell](https://github.com/AvengeMedia/DankMaterialShell) | MIT | záloha | náhradný shell, ak by alfa Noctalie zlyhávala (Quickshell + Go), vo Fedore 44 ako balík |
| `quickshell` | [Quickshell](https://github.com/quickshell-mirror/quickshell) | LGPL-3.0 | Prebrať | QML runtime pod DMS/Caelestia |
| `caelestia-shell` | [Caelestia shell](https://github.com/caelestia-dots/shell) 2.3 | GPL-3.0 | **zdroj prvkov** | prvky pre silnejšie PC (stupeň Plný): dashboard, `background/Visualiser`, výkonové krúžky, animácie (`assets/bongocat.gif`, `kurukuru.gif`), morfujúce panely |
| `caelestia-dotfiles` | [Caelestia dotfiles](https://github.com/caelestia-dots/caelestia) | — (overiť) | zdroj prvkov | Hyprland konfigurácia, témy aplikácií (foot, btop, fish…) |
| `caelestia-cli` | [caelestia-cli](https://github.com/caelestia-dots/cli) | GPL-3.0 | zdroj prvkov | ovládací skript: témy, tapety, nahrávanie |
| `matugen` | [matugen](https://github.com/InioX/matugen) | GPL-2.0 | Prebrať | farby z tapety; vo Fedore 44 ako balík |
| `noctalia-shell` | [Noctalia v5](https://github.com/noctalia-dev/noctalia-shell) 5.1.0 | MIT | **zvolený shell (F3)** | natívny shell (C++/GLES, bez Qt), backendy Hyprland aj labwc |
| `noctalia-greeter` | [Noctalia Greeter](https://github.com/noctalia-dev/noctalia-greeter) 1.5.0 | MIT | kandidát F1 | obrazovka prihlásenia pre greetd, vlastný wlroots kompozitor |
| `noctalia-plugins` | [noctalia-plugins](https://github.com/noctalia-dev/noctalia-plugins) | MIT | vzor | 138 pluginov (widgety, panely, launcher providery) |
| `end4-dots-hyprland` | [end-4 dots](https://github.com/end-4/dots-hyprland) | GPL-3.0 | Prebrať z | vzor: prehľad okien, AI sidebar |
| `ml4w-dotfiles` | [ML4W](https://github.com/mylinuxforwork/dotfiles) | GPL-3.0 | Prebrať z | vzor: Settings App (všetko prepínačmi) |
| `proton` | [Proton](https://github.com/ValveSoftware/Proton) `proton-11.0-1` | BSD-3 + zmiešané | Prebrať | predvolený Proton (bez submodulov, len referencia) |
| `umu-launcher` | [umu-launcher](https://github.com/Open-Wine-Components/umu-launcher) | GPL-3.0 | Prebrať | spúšťanie ne-Steam hier cez Proton |
| `gamescope` | [gamescope](https://github.com/ValveSoftware/gamescope) | BSD-2 | Prebrať | herná relácia (**až na reálnom HW**, potrebuje Vulkan) |
| `mangohud` | [MangoHud](https://github.com/flightlessmango/MangoHud) | MIT | Prebrať z | herný overlay |
| `lepton` | [Valve Lepton](https://gitlab.steamos.cloud/frame-public/lepton) | MIT + GPL-3.0 (image) | Prebrať | Android hry (**až na reálnom HW**) |
| `waydroid` | [Waydroid](https://github.com/waydroid/waydroid) | GPL-3.0+ | základ Leptonu | referencia |
| `ubuntu-settings` | [ubuntu-settings](https://git.launchpad.net/~ubuntu-desktop/ubuntu/+source/ubuntu-settings) 26.10.1 | GPL-2.0+ | Prebrať | adresár `oom/`: 40× `OOMScoreAdjust=-500`, `ManagedOOMMemoryPressure=auto` → port do Fedory |
| `cosmic-files` | [cosmic-files](https://github.com/pop-os/cosmic-files) | GPL-3.0 | vzor | Data Manager (udisks2, pohľady) |
| `mission-center` | [Mission Center](https://gitlab.com/mission-center-devs/mission-center) | GPL-3.0 | vzor | Process Manager |
| `ollama` | [Ollama](https://github.com/ollama/ollama) | MIT | Prebrať | runtime lokálneho AI |
| `nvidia-fedora-guide` | [Nvidia Fedora Guide](https://github.com/fady-saied/Nvidia-Fedora-Guide) | — (overiť) | referencia | vetvy 580/595, akmod (fáza HW) |
| `bazzite` | [Bazzite](https://github.com/ublue-os/bazzite) | Apache-2.0 | vzor | image pipeline (fáza Atomic) |

## Balíky pre Fedoru 44

Hyprland a jeho knižnice nie sú v oficiálnych repozitároch Fedory 44 (tam je len stará
hyprutils/hyprlang). Celú sadu má COPR **[lionheartp/Hyprland](https://copr.fedorainfracloud.org/coprs/lionheartp/Hyprland)**
(fork solopasha/hyprland) pre fedora-44/45/rawhide: hyprland 0.56.2, aquamarine 0.15.1,
hyprutils 0.14.2, hyprlang 0.6.8, quickshell 0.3.1 (git 20260921), xdg-desktop-portal-hyprland
1.4.1, hyprlock 0.9.6, hypridle, hyprpolkitagent, uwsm, matugen 4.2.0, noctalia-shell.
Z oficiálnej Fedory 44: labwc 0.9.6, greetd 0.10.3, foot, fuzzel, gamescope 3.16.29, Mesa 26.2.3.

## Články (`docs/`)

Uložené: Ubuntu 26.10 OOM, Valve Lepton, Hyprland 0.56, Proton 11 release, NVIDIA 595,
NVIDIA 580 (posledná pre Maxwell/Pascal), NVK na Maxwell, Hyprland diskusia #12966 (vmwgfx
patch), Omarchy vo VirtualBoxe a karta modelu Qwen3-14B-sk (`.md`).

**Nestiahnuté (web blokuje roboty, 403/466):** AlternativeTo (Hyprland 0.55/0.56),
LinuxCapable (NVIDIA na Fedore), Veda.sk (Qwen3-14B-sk). V prípade potreby ich treba uložiť ručne z prehliadača.

## Zámerne nestiahnuté

- **Váhy Qwen3-14B-sk** ([slovak-nlp/Qwen3-14B-sk](https://huggingface.co/slovak-nlp/Qwen3-14B-sk),
  GGUF Q6_K [tomg42](https://huggingface.co/tomg42/Qwen3-14B-sk-Q6_K.gguf)): majú 12–29 GB, VM má
  11 GB RAM a 11 GB voľného disku. Stiahnu sa až na reálnom HW cez `ollama pull`.
- **Proton submoduly** (wine, dxvk, vkd3d…): desiatky GB, pre integráciu stačí hotový build.
- **NVIDIA ovládače 580/595**: balíky z RPM Fusion (`akmod-nvidia`, `akmod-nvidia-580xx`), nie zdroje.

## Licencie — pozor pri forku

- GPL (Caelestia: prvky sa **prepisujú** do Noctalie, nekopírujú; skopírovaný kód by musel ostať GPL, cosmic-files, Mission Center, umu, labwc, end-4, ML4W): odvodený kód musí ostať GPL.
- Session služba (platená) musí byť **samostatný program** a nesmie linkovať GPL kód.
- DMS, Noctalia, Hyprland, wlroots, Ollama, MangoHud: MIT/BSD, bez tejto povinnosti.
