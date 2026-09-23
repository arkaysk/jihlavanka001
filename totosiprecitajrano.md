# Toto si prečítaj ráno ☕

Denník práce, kým si spal. Najnovšie hore. Na konci sú **veci, ktoré čakajú na tvoje rozhodnutie**.

---

## Odpovede na tvoje otázky

### Dá sa napísať vlastný greeter alebo prerobiť iný do nášho vzhľadu?

Áno, obe cesty sú reálne:

| Cesta | Čo to znamená | Riziko |
|---|---|---|
| **A. Vlastný greeter v Quickshelli** (zvolené) | Quickshell má priamo modul `Quickshell.Services.Greetd` (prihlásenie cez greetd). Obrazovka prihlásenia je potom jeden QML súbor v štýle Latte a beží pod labwc s pixmanom, teda na overenej kombinácii bez GPU, ktorá pamäť neprepúšťa. | nízke: iba QML, kompozitor je overený |
| B. Opraviť Noctalia Greeter (MIT) | nájsť únik pamäte jadra v jeho kompozitore | neznáme; je to cudzí C++ kód |
| C. Prefarbiť tuigreet | iba farby textového greetera | žiadne, ale je to stále text |

Robím **A** a C nechávam ako zálohu. Stav nájdeš nižšie v denníku.

### Nemám Fedora účet

To nevadí. COPR je iba pohodlnejšia distribúcia balíka `hyprland-latte`. Dovtedy funguje lokálny
repozitár `latteos-local` (`/var/lib/latteos/repo`) a COPR má vylúčené `hyprland*`, takže `dnf upgrade`
patchovaný Hyprland neprepíše. Keď budeme balíky rozdávať iným PC, možnosti sú tieto (rozhodnutie je
nižšie):
- založiť bezplatný Fedora účet (FAS) a COPR `latteos`,
- balíky stavať cez GitHub Actions do GitHub Releases alebo vlastného dnf repozitára na GitHub Pages
  (bez Fedora účtu),
- neskôr pri Fedora Atomic balíky zapiecť priamo do obrazu (bootc), vtedy COPR netreba vôbec.

---

## Denník

### 23. 9. 2026, 21:10: téma Latte pre Noctaliu ✅
- `session/noctalia/`: paleta **Latte** (`palettes/Latte.json`, tmavá aj svetlá) a `config.toml`.
  Lišta je dole a pozostáva z **ostrovov** (capsule groups): Aplikácie · Čas+notifikácie ·
  Šálka (riadiace centrum)+páska (plochy) · Hľadanie („Hľadaj, pýtaj sa, spúšťaj…“) · Schránka ·
  Súbory+sieť+zvuk+vypnutie.
- Písma Manrope a Fraunces (OFL, z google/fonts) sú v `session/fonts`. Tapety sú tvoje z
  `old/data/wallpapers` (skopírované ako obrázky, nie kód), predvolená je kávové zrno.
- `latte-session` nastaví `NOCTALIA_CONFIG_HOME=/usr/share/latteos`, ak nemáš vlastný
  `~/.config/noctalia/config.toml`, a preskočí uvítacieho sprievodcu Noctalie.
- Z tvojho `~/.local/state/noctalia/settings.toml` som vymazal tapetu sovy, ktorú si Noctalia uložila
  sama pri teste. Záloha je v `settings.toml.bak-pred-latte`.
- Chyba, ktorú som našiel: ak paleta obsahuje variant `light`, musí mať aj blok `terminal`, inak ju
  Noctalia potichu zahodí.
- Screenshot: `setup/f1/results/hyprland-swgl-210826/screen.png` (netrackované).

### ⚠️ 21:06: tvoja relácia Hyprland spadla (moja vina)
- Pri teste témy som niekoľkokrát natvrdo reštartoval Noctaliu v tvojej bežiacej relácii. Hyprland
  potom spadol v softvérovom rasterizéri (`lp_rast_shade_tile` v llvmpipe). Relácia sa vrátila na
  prihlasovaciu obrazovku, teda správne, lebo pád po viac ako 60 s nie je pád štartu.
- Poučenie: shell sa nesmie zabíjať pod bežiacou reláciou. Na testy používam `probe.sh`.
- Pád `hyprland-welcome` (z COPR, beží pri prvom štarte štandardnej relácie) je teraz v našej
  konfigurácii vypnutý (`ecosystem { no_update_news, no_donation_nag }`).

### 23. 9. 2026, večer: štart práce
- Rozbalil som `inspo/LatteOS – návrh plochy.html` (16 obrazoviek: lišta, páska, dlaždice, Text Bar,
  čas, schránka, systémové menu, Device Manager, AI panel, inštalácia, témy materiálov, drahokamy).
- Paleta z návrhu: pozadie `#1B1410`, panel `rgba(34,26,21,.94)`, ostrovy lišty `rgba(38,29,23,sklo)`
  s rozmazaním 22 px, text `#F3EBDD`, tlmený text `#CDBCA6`, akcent `#E4B283` a `#D8A06A`, odznaky
  `#E9C58F`, okraj `rgba(243,235,221,.12)`. Rohy: okno 14 px, ostrov 16 px, tlačidlo 12 px.
  Písma: **Manrope** (UI), **Fraunces** (nadpisy), **JetBrains Mono**.
- Poradie práce: (1) téma Latte pre Noctaliu, (2) vlastný greeter v Quickshelli, (3) F2 Lua modul
  Hyprlandu, (4) F3 prvky shellu podľa návrhu.

---

## Čaká na tvoje rozhodnutie

1. **Distribúcia balíkov bez Fedora účtu:** FAS + COPR, GitHub Actions a vlastný repozitár, alebo
   počkať na Atomic (bootc)? Zatiaľ nič netreba, lokálny repozitár stačí.
