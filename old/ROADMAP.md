# LatteOS Gamer Distro — Roadmap

22. 9. 2026 · @Arkay

Nadväzuje na [README.md](README.md) (premisa, bezpečnostný a aplikačný model, tech stack).
Nahrádza pôvodný plán pre Jihlavanku 0.1 (uložený ako [oldROADMAP.md](oldROADMAP.md)) — nie preto,
že by bol zlý, ale preto, že stojí na inom kompozitore (labwc) a inom jazyku (Python/GTK4), zatiaľ čo
gamerdistro smer stavia na forku Hyprlandu a Rust/Slint od prvého riadku kódu.

## Rozhodnutia, z ktorých táto roadmapa vychádza

| Rozhodnutie | Voľba | Dôvod |
|---|---|---|
| Distribučná báza | **Fedora Atomic** (Bazzite štýl, rpm-ostree) | Najmenej trenia s tým, čo už existuje (`data/hardware/base.toml` je overené proti Fedore 44, vývojové VM je Fedora Server) |
| Naloženie so starým Python/GTK kódom | **Úplný prepis**, nie adaptácia na Hyprland | Fluidita (bezier animácie, GPU efekty priamo v kompozícii — referenčná kvalita [r/unixporn: Hyprland as fluid as it gets](https://www.reddit.com/r/unixporn/comments/1s84jik/hyprland_as_fluid_as_it_gets/)) sa nedá dobre dolepiť na GTK4 widget strom dodatočne. Musí byť súčasťou architektúry od Etapy C, nie doplnok na konci. |
| Písať od nuly vs. prebrať z ekosystému | **Prepis od nuly len pre skutočné odlišovacie prvky** (fork Hyprlandu, trusted/untrusted model). Pre commodity UI chrome (panel, kontextové menu, launcher, súborový manažér, gaming session) sa **forkujú a prispôsobujú overené open-source projekty** namiesto písania od nuly | Kontextové menu na ploche alebo Proton prefix manager už niekto vyriešil overeným spôsobom v Hyprland/SteamOS ekosystéme — netreba objavovať to isté znova. Licencie overené, pozri tabuľku nižšie |

## Prebraté komponenty namiesto písania od nuly

Licencie overené (22. 9. 2026, priamo z repozitárov). Žiadny z nich nebráni forku okrem
cosmic-files/cosmic-panel, kde platí GPL-3.0 copyleft — akceptovateľné pre open-source OS distro,
prehodnotiť len ak by niektorý z týchto modulov mal byť niekedy uzavretý/komerčný.

| Oblasť | Projekt | Licencia | Ako sa použije |
|---|---|---|---|
| Kompozitor | [Hyprland](https://github.com/hyprwm/Hyprland) | BSD-3-Clause | fork, žiadne obmedzenia (Etapa C) |
| UI toolkit pre vlastné appky | [Slint](https://slint.dev/) | Royalty-free pre desktop (zadarmo) / GPLv3 / komerčná | desktop použitie zadarmo, zdrojáky môžu zostať vlastné |
| Panel, launcher, kontextové menu, notifikácie | [HyprPanel](https://github.com/Jas-SinghFSU/HyprPanel) (Astal/GTK) | MIT | fork ako štart pre Etapu U, voľne premenovateľné a upraviteľné |
| Alternatíva k HyprPanel | [Quickshell](https://github.com/quickshell-mirror/quickshell) (QtQuick) | LGPL-3.0 | ak sa ukáže flexibilnejší pre fluiditu; zmeny v Quickshell samotnom treba zdieľať späť |
| Súborový manažér | [cosmic-files](https://github.com/pop-os/cosmic-files) (Rust) | **GPL-3.0-only** | fork ako štart pre Etapu D (udisks2, trash, view modes už hotové) |
| Panel scaffolding (Rust alternatíva) | [cosmic-panel](https://github.com/pop-os/cosmic-panel) | **GPL-3.0-only** | záložná možnosť k HyprPanel, ak sa uprednostní Rust nad Astal/GTK |
| Gaming session (fullscreen, HDR, FSR scaling) | [gamescope](https://github.com/ValveSoftware/gamescope) (Valve) | BSD-2-Clause | použiť ako je, nepísať vlastný (Etapa G) |
| Proton/Wine prefix management | [umu-launcher](https://github.com/Open-Wine-Components/umu-launcher) | GPL-3.0 | externý proces (rovnako ako Bazzite/Lutris/Heroic), nešíri GPL na zvyšok systému |
| Build/image pipeline | Bazzite/ublue-os Containerfile+justfile | rôzne, overiť pri fork-ovaní | referencia/fork pre Etapu 0/9 namiesto vlastného rpm-ostree pipeline |

## Čo sa deje s Jihlavankou 0.1

Kód v `src/` a `session/` (17-tisíc riadkov Python/GTK4 + labwc konfigurácia) **prestáva byť runtime**
tohto smeru. Nemaže sa — slúži ako:

1. **Funkčná špecifikácia.** Každý modul (`latte_files`, `latte_process`, `latte_devices`,
   `latte_settings`, `latte_shell`, greeter) už raz vyriešil, čo presne má daná časť robiť, vrátane
   hraničných prípadov, ktoré `oldROADMAP.md` a `oldCoreAPImanifest.md` zdokumentovali (napr. tri režimy
   zobrazenia v Data Manageri, presné hranice medzi Process Manager a Device Manager). Etapy nižšie sa na
   tieto čísla odkazujú, aby sa pri prepise neopakovalo objavovanie tých istých rozhodnutí.
2. **Dáta, nie kód, prežívajú priamo.** `data/hardware/base.toml`, `data/hardware/pci.ids`,
   `data/settings/*.schema.toml`, `data/polkit/*` a wallpapre sú jazykovo neutrálne — Rust vrstva ich
   môže čítať bez zmeny formátu. Netreba ich prepisovať, len napojiť.
3. **Session bootstrap ostáva ako koncept, nie ako súbory.** Systemd user jednotky, greetd a `latte-session.target`
   ako vzor prežívajú; `session/labwc/rc.xml` a `environment` sú labwc-špecifické a nahradí ich
   Hyprland konfigurácia z Etapy C.

Čo sa **neprenáša vôbec**: GTK4/libadwaita vzhľadová vrstva (Etapa 3 v starom pláne), pretože fluidný
Slint UI runtime ju robí od nuly inak.

---

## Poradie a závislosti

    Etapa 0 (Báza a vývojové prostredie) ⬜
       ↓
    Etapa H (Hardvér a 3D akcelerácia — DEŇ 1, nie uprostred) ⬜
       ↓
    Etapa C (Fork Hyprlandu — fluidný kompozitor) ⬜
       ↓
    Etapa U (Rust/Slint UI jadro — shell, popupy, plocha) ⬜
       ↓
    ┌──────────────┬──────────────┬──────────────┐
    ↓              ↓              ↓              ↓
 Etapa S       Etapa D        Etapa P        Etapa W
 (Bezpeč./     (fork          (Process &     (Wizard,
  App model,    cosmic-files)  Device Mgr)    Session Mgr, Text Bar)
  vlastné)
    └──────────────┴──────────────┴──────────────┘
                          ↓
                   Etapa G (Steam, Proton, anti-cheat)
                          ↓
                   ══ M1: overenie na reálnych strojoch ══
                          ↓
                   Etapa A (Android — Lepton/Waydroid)
                          ↓
                   Etapa 9 (Vydanie: ISO/kickstart)

Kľúčový rozdiel oproti starému plánu: **hardvér a 3D akcelerácia (Etapa H) idú hneď po založení
vývojového prostredia, nie až v polovici cesty.** Celá premisa gamerdistra (fluidný Hyprland fork,
GPU-akcelerované efekty) je na nich postavená — bez overenej 3D akcelerácie sa Etapa C ani nedá
zmysluplne začať.

---

## Etapa 0 — Báza a vývojové prostredie ⬜

| | Úloha | Stav |
|---|---|---|
| 0.1 | Čistý git branch `gamerdistro`, oddelený od Jihlavanky (README/manifest presun už hotový) | 🔸 |
| 0.2 | Nový VM image: Fedora Atomic (rpm-ostree), nie Fedora Server ako doteraz | ⬜ |
| 0.3 | Rust toolchain, Slint (crate + LSP/preview nástroje), Vulkan SDK/hlavičky vo vývojovom obraze | ⬜ |
| 0.4 | Voľba forkovacieho bodu Hyprlandu (verzia/tag) a build pipeline preň v Atomic prostredí (layered package alebo Distrobox/toolbox pre vývoj) | ⬜ |
| 0.5 | Repozitár: rozhodnúť štruktúru workspace (jeden Cargo workspace pre kompozitor-doplnky + shell + nástroje, alebo oddelené repá) | ⬜ |

**Výsledok:** vývojár vie na čistom Fedora Atomic stroji skompilovať fork Hyprlandu aj Rust/Slint časti.

---

## Etapa H — Hardvér a 3D akcelerácia ⬜

Presunuté z pôvodnej strednej pozície na začiatok. Obsah je väčšinou prevzatý z `oldROADMAP.md`
(Etapa H, H.1–H.9) — toto je systémová vrstva nezávislá od kompozitora aj jazyka, netreba ju
vymýšľať odznova, len overiť skôr.

| | Úloha | Stav |
|---|---|---|
| H.1 | `data/hardware/base.toml` (12 skupín, 88 balíkov) preniesť do rpm-ostree/kickstart podoby pre Atomic | 🔸 dáta existujú, formát treba overiť proti rpm-ostree |
| H.2 | Grafika a 3D: Mesa (Radeon/Intel), proprietárny NVIDIA (akmod, RPM Fusion nonfree), Vulkan runtime a validačné vrstvy, 32-bitové ovládače pre Steam | ⬜ |
| H.3 | Secure Boot a podpis modulu (MOK) pre akmod-nvidia na Atomic | ⬜ |
| H.4 | Overenie GPU-akcelerovanej kompozície *pred* Etapou C: `vulkaninfo`, `glxinfo`/`vkcube` na skutočnej aj virtuálnej grafike — vo VM (virtio) sa 3D akcelerácia poriadne overiť nedá, treba aspoň jeden reálny stroj skôr, než sa začne s Etapou C | ⬜ |
| H.5 | Zvuk (PipeWire/WirePlumber), vstup (libinput, gamepady, `libwacom`), firmvér (`fwupd`) | ⬜ |
| H.6 | Hardvérový report (`latteos-diag` ekvivalent) — prevziať logiku z `oldROADMAP.md` H.8 | ⬜ |

**Výsledok:** na aspoň jednom reálnom stroji beží overená GPU-akcelerovaná Vulkan grafika, na ktorej
má zmysel stavať Hyprland fork. Toto je **blokujúca podmienka** pre Etapu C, nie paralelná úloha.

---

## Etapa C — Fork Hyprlandu: fluidný kompozitor ⬜

Jadro odlišovacieho zážitku (README, sekcia "Compositor a UI vrstva"). Referenčná úroveň kvality:
[r/unixporn — Hyprland as fluid as it gets](https://www.reddit.com/r/unixporn/comments/1s84jik/hyprland_as_fluid_as_it_gets/).

| | Úloha | Stav |
|---|---|---|
| C.1 | Stock Hyprland beží v session (greetd + systemd user jednotky, koncept prevzatý z `session/`) | ⬜ |
| C.2 | Rozsah forku: rozhodnúť, čo sa mení hneď (animačná krivka, efekty kompozície) a čo zostáva stock (README otvorená otázka č. 2) | ⬜ |
| C.3 | Bezier animácie a GPU-akcelerované efekty ladené na referenčnú fluiditu — toto je vizitka projektu, dostáva vlastný časový priestor, nie "urobí sa poslednú hodinu" | ⬜ |
| C.4 | Wayland vrstva: rozhodnúť, či a kde sa oplatí Smithay (README: "nie nutne v jadre kompozitora") — predpoklad je nie pre v0, prehodnotiť po C.3 | ⬜ |
| C.5 | Protokoly potrebné pre vyššie etapy: layer-shell (panel), wlr-foreign-toplevel (taskbar), screencopy (náhľady okien) — fork Hyprlandu ich má, overiť že sa nezlomili pri C.2/C.3 | ⬜ |

**Výsledok:** prihlásenie spustí forknutý Hyprland s animáciami porovnateľnými s referenčným videom,
na reálnom hardvéri z Etapy H.

---

## Etapa U — Shell: panel, launcher, kontextové menu, notifikácie ⬜

Namiesto písania `latte_shell` ekvivalentu (3895 riadkov Python) od nuly sa forkuje **HyprPanel**
(MIT, Astal/GTK) ako bežiaci základ a prispôsobuje sa LatteOS téme a správaniu. Layout a UX rozhodnutia
z `oldROADMAP.md` Etapa 2/2b/3 (tvar L popupov, rohové dlaždice, kontextové menu ako systémové pravidlo)
ostávajú platná špecifikácia pre to, čo sa vo forku mení.

| | Úloha | Stav |
|---|---|---|
| U.1 | Fork HyprPanelu, beží nad Etapou C fork Hyprlandu, overiť Hyprland IPC hooky | ⬜ |
| U.2 | Retheme na LatteOS vizuál (paleta, polomery, animácie zladené s fluiditou Etapy C) | ⬜ |
| U.3 | Kontextové menu ako systémové pravidlo — dotiahnuť to, čo ani stará Python verzia nedokončila (plocha, taskbar), teraz už na hotovom HyprPanel základe namiesto vlastnej layer-shell implementácie | ⬜ |
| U.4 | Taskbar nad wlr-foreign-toplevel (HyprPanel to rieši natívne pre Hyprland — overiť len po forku C) | ⬜ |
| U.5 | Oznámenia (`org.freedesktop.Notifications`) — HyprPanel má vlastné, overiť/prispôsobiť | ⬜ |
| U.6 | Text Bar: hľadanie appiek/funkcií/súborov + prepnutie na AI prompter (README) — toto **je** LatteOS-špecifické, staviať nad HyprPanel launcher modulom alebo ako vlastný Slint doplnok, nie preberať 1:1 | ⬜ |
| U.7 | Plocha: tapeta, ikony, Kôš | ⬜ |
| U.8 | Clipboard manager — `nwg-clipman`/`cliphist` ako backend namiesto vlastného `latte-clipd` | ⬜ |

**Výsledok:** deň sa dá prežiť v prostredí bez cudzieho desktopu, s fluiditou z Etapy C viditeľnou
vo všetkých UI prvkoch. Vlastná práca sa sústredí na U.2, U.3 a U.6 (branding, chýbajúce kontextové
menu, Text Bar) — nie na písanie panelu od nuly.

---

## Etapa S — Bezpečnostný a aplikačný model ⬜

Druhý odlišovací prvok podľa README ("nie hlavný vzhľad, ale bezpečnostný/aplikačný model").

| | Úloha | Stav |
|---|---|---|
| S.1 | Prekladač ("weapon"/"radio") — manifest za aplikáciu píše LatteOS, nie appka sama | ⬜ |
| S.2 | Trusted/untrusted profily: Steam ako trusted celok, anti-cheat hry (BattlEye/EAC) trusted beh vs. Flatpak sandbox pre ostatné — presné pravidlá sú stále otvorené (README, posledná sekcia) | ⬜ |
| S.3 | NET tlačidlo na aplikáciu (vrátane Proton appiek) | ⬜ |
| S.4 | App Manager: zoznam, inštalácia/odstránenie Flatpaku, aktualizácie (systém + Flatpak na jednom mieste) | ⬜ |
| S.5 | App Registry ako dátový model (koncept `oldROADMAP.md` J.1 — AppID, runtime, pôvod, stav), teraz v Rust namiesto nad `Gio.DesktopAppInfo` | ⬜ |

**Výsledok:** aplikácia sa nainštaluje, spustí a obmedzí bez terminálu; anti-cheat hry fungujú bez
kompromisu na bezpečnosti ostatných appiek.

---

## Etapa D — Data Manager (súborový manažér) ⬜

Namiesto písania od nuly sa forkuje **cosmic-files** (Rust, GPL-3.0-only) — udisks2 integrácia,
Kôš, tri režimy zobrazenia a viacnásobný výber už fungujú. `oldROADMAP.md` Etapa 1 (takmer celá ✅
v Pythone) ostáva referencia pre to, čo sa má správať inak než v COSMIC verzii.

| | Úloha | Stav |
|---|---|---|
| D.1 | Fork cosmic-files, build proti Etape 0 toolchainu, overiť že GPL-3.0 je pre tento modul akceptovateľné (viď licenčná tabuľka vyššie) | ⬜ |
| D.2 | "Tento počítač" koreň — retheme z pôvodného COSMIC zobrazenia zväzkov na Windows-like "Tento počítač" (README: "neprepisuje linux, nezakrýva ju") | ⬜ |
| D.3 | Rozlíšenie FHS/Flatpak/AppImage v zobrazení — COSMIC toto nerieši, vlastná práca nad ich udisks2/VFS vrstvou | ⬜ |
| D.4 | Kontextové menu ako systémové pravidlo (staré 2.12–2.14) — cosmic-files má vlastné kontextové menu, overiť pokrytie oproti starej špecifikácii a doplniť chýbajúce položky | ⬜ |
| D.5 | Vizuálne zladenie s Etapou U (rovnaká paleta/fluidita naprieč GTK-based panelom a Rust-based file managerom — dva rôzne toolkity, jeden vzhľad cez tému/CSS) | ⬜ |

**Výsledok:** súborový manažér použiteľný na bežnú prácu bez terminálu, v štýle Forklift/Total Commander.
Vlastná práca sa sústredí na D.2–D.5 (branding, Windows-like projekcia, zladenie vzhľadu) — nie na
udisks2/trash/view-mode logiku, tú už rieši fork.

---

## Etapa P — Process a Device Manager ⬜

| | Úloha | Stav |
|---|---|---|
| P.1 | Process Manager: strom procesov, ekvivalent ctrl-alt-del s pridanou hodnotou (autoruns, hwinfo, CPU-Z štýl) | ⬜ |
| P.2 | Device Manager nad hardvérovým stavom z Etapy H | ⬜ |
| P.3 | Prepojenie proces → aplikácia → zariadenie (teplota, spotreba) — v starom pláne odložené (J.4/P.7), tu sa dá riešiť skôr, keďže App Registry (S.5) a Process Manager vznikajú v rovnakom jazyku súčasne | ⬜ |

---

## Etapa W — Wizard, Session Manager, doplnkové nástroje ⬜

| | Úloha | Stav |
|---|---|---|
| W.1 | Wizzard: offline tabuľka závislostí + online/offline AI návrh appiek a balíkov | ⬜ |
| W.2 | Session Manager: mobilná appka ako prenášač účtov, bezpečné prihlásenie s overením, načítanie profilu z internetu/USB | ⬜ |
| W.3 | AI prompter v Text Bar (U.5): voľba lokálneho/offline modelu vs. API/chat modul, správa tokenov | ⬜ |

---

## Etapa G — Hry, Steam, Proton ⬜

Vytiahnuté pred M1, rovnako ako v starom pláne — Steam si Proton nesie sám, netreba naň vlastnú
správu prefixov na to, aby sa dalo overiť, že hry vôbec bežia.

| | Úloha | Stav |
|---|---|---|
| G.1 | Steam predinštalovaný ako trusted profil (S.2) | ⬜ |
| G.2 | Proton dostupný cez **umu-launcher** (GPL-3.0, externý proces ako v Bazzite/Lutris) namiesto vlastnej správy prefixov | ⬜ |
| G.3 | Fullscreen gaming session cez **gamescope** (BSD-2-Clause, Valve) — HDR, FSR scaling, frame limit hotové, netreba riešiť vlastné "shell nekradne fokus" na úrovni Etapy U | ⬜ |
| G.4 | Anti-cheat: overiť BattlEye/EAC trusted beh z S.2 na reálnej hre | ⬜ |

---

## M1 — Overenie na reálnych strojoch ⬜

Rovnaký princíp ako v starom pláne: dovtedy práca hlavne vo VM (virtio negarantuje 3D), od M1 sa
každá ďalšia etapa overuje na skutočnom hardvéri. Predpoklad: Etapy H, C, U, S, D, G hotové aspoň
v základnej podobe.

| | Úloha | Stav |
|---|---|---|
| M1.1 | Aspoň tri odlišné stroje: AMD, NVIDIA, notebook s integrovanou grafikou | ⬜ |
| M1.2 | Fluidita kompozitora (Etapa C) porovnateľná s referenčným videom na reálnom GPU, nie len vo VM | ⬜ |
| M1.3 | Hry: natívna, Proton DX11, Proton DX12/Vulkan — obraz, zvuk, gamepad, plynulosť | ⬜ |
| M1.4 | Kompatibilná tabuľka stroj × ovládač × appka, vrátane príčiny zlyhania | ⬜ |

**Výsledok:** gamerdistro je overené prostredie na skutočných počítačoch, nie prototyp vo VM.

---

## Etapa A — Android (Lepton/Waydroid) ⬜

Prevziať scope zo starého plánu (Etapa 6): inštalácia, appka ako okno, zoznam appiek so štítkom,
zdieľaný priečinok, schránka naprieč systémami. Implementácia integrácie je nová (napojenie na
Etapu U/S), samotný Waydroid beží nezmenený.

---

## Etapa 9 — Vydanie ⬜

| | Úloha |
|---|---|
| 9.1 | Kickstart/rpm-ostree obraz pre Fedora Atomic vrátane `latteos-base` (H.1) |
| 9.2 | Test na čistom stroji podľa kritérií z README |
| 9.3 | Dokumentácia pre používateľa |

---

## Čo zostáva otvorené (z README, neriešiť teraz)

- Presný rozsah forku Hyprlandu (C.2) — koľko meniť hneď, koľko nechať stock.
- Presné pravidlá trusted/untrusted nad rámec Steamu a anti-cheat hier (S.2).
- Verziovacie/kódové meno pre gamerdistro smer (staré malo "Jihlavanka"/"Arabica") — nie je
  blokujúce, môže počkať do prvého bežiaceho kompozitora (Etapa C).

## Najbližšie tri kroky

1. **Etapa 0.2–0.4** — nový Fedora Atomic VM image, Rust/Slint/Vulkan toolchain, voľba forkovacieho
   bodu Hyprlandu.
2. **Etapa H.2–H.4** — overiť GPU-akcelerovanú Vulkan grafiku na aspoň jednom reálnom stroji. Bez
   tohto kroku nemá zmysel začínať Etapu C.
3. **Etapa C.1–C.3** — stock Hyprland v session, potom ladenie fluidity ako prvá viditeľná vec, ktorú
   má zmysel ukázať.

## Poznámka k stratégii "fork, nie od nuly"

Platí len tam, kde už niekto vyriešil presne ten istý problém v porovnateľnom stacku (Hyprland
ekosystém, SteamOS/Bazzite gaming vrstva). Neplatí pre Etapu C (fork Hyprlandu je sám o sebe cieľ)
a Etapu S (trusted/untrusted model a "weapon/radio" prekladač nemá cudzí ekvivalent). Ak sa pri ďalších
etapách (P, W) nájde podobne vhodný kandidát na fork, doplní sa do tabuľky "Prebraté komponenty" pri
plánovaní danej etapy, nie retroaktívne.
