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

Robím **A** a C nechávam ako zálohu. **Hotové a predvolené**, pozri denník.

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

### 23. 9. 2026, 21:32: F3, Text Bar (plugin) ✅
- `session/noctalia/plugins/textbar/`: pole „Hľadaj, pýtaj sa, spúšťaj…“ na lište so **štyrmi režimami**
  (ikona = režim; **pravý klik alebo koliesko** prepína, klik otvorí spúšťač v danom režime):
  - **Lokálne:** aplikácie Noctalie a k tomu nastavenia a akcie LatteOS (stupne výkonu, režimy okien,
    SAFE, tapeta, sieť, procesy…). Hľadá aj bez diakritiky („stupen“).
  - **Linux príkaz** (`/cmd`): náhľad a beh v termináli. **Deštruktívne príkazy** (rm -rf, dd, mkfs,
    sudo…) ukážu „⚠ Pozor“ a treba ich vybrať druhýkrát.
  - **Web** (`/web`): DuckDuckGo, Wikipédia sk, ProtonDB. Iba na výslovnú žiadosť.
  - **AI** (`/ai`): lokálne AI cez Ollamu. Bez modelu povie, čo chýba (rozhodnutie nižšie).
- Screenshoty: `setup/f1/results/f3-textbar-*.png`.

### 23. 9. 2026, 21:30: F3, systémové menu LatteOS (plugin Noctalie) ✅
- Pluginy Noctalie v5 sa píšu v **Luau** (izolovane, s deklaratívnym UI). Stiahol som
  `noctalia-official-plugins` ako vzor. Mimochodom obsahuje aj **bongocat** 🐱.
- `session/noctalia/plugins/system/`: **šálka na lište** otvára **systémové menu** podľa návrhu:
  - **Relácia:** Zamknúť, Odhlásiť, Mobilný účet (pripravujeme),
  - **Systém:** Nastavenia, Správca procesov,
  - **LatteOS:** režim, renderer, stupeň, dôvod; výber stupňa výkonu (Automaticky/Plný/…/Softvér)
    zapíše `~/.config/latteos/tier` a reloadne Hyprland; výber režimu okien; prepínač „Nabudúce SAFE“,
  - **Napájanie:** Uspať, Reštartovať, Vypnúť, všetko s **potvrdením druhým kliknutím** („nič
    nevypne priamo“ z radaru).
- Zdroj pluginov `latteos` (`kind = "path"`) je v `config.toml`. Noctalia načíta zmeny za behu.
- Screenshot: `setup/f1/results/f3-system-menu.png`.

### 23. 9. 2026, 21:25: F2, Lua modul Hyprlandu ✅
- `session/hypr/hyprland.lua` + `latte/mode.lua`, `tiers.lua`, `windows.lua`. `latte-session` ho
  používa namiesto starého `hyprland.conf` (ten ostáva ako záloha).
- **Stupne výkonu** podľa radaru: Plný, Štandard, Úsporný, Minimálny a Softvér (VM). Riadi ich
  `latte-boot` a dajú sa vynútiť v `~/.config/latteos/tier`, napr. `plny`.
- **Režimy okien:** nekonečná páska, dlaždice a plávajúce. Prepína ich **Super+W** a voľba sa pamätá.
  Overené: tri okná prešli všetkými tromi režimami.
- **Skratky** podľa radaru (Super+Tab prehľad, Super+D plocha, Super+Shift+šípka iný monitor…).
- Nájdené a opravené:
  - `scale = "auto"` vo VM zvolil mierku 2, preto je teraz pevne 1.
  - `hyprctl dispatch exec …` v Lua režime nefunguje, treba `hyprctl eval 'hl.exec_cmd("…")'`.
- Testovacie poznámky: `wtype` nevie poslať Super ako modifikátor pre skratky, preto skratky
  testujem cez `hyprctl eval`. Medzi stĺpcami pásky je malý biely artefakt (sw-gl).
- ⚠️ Kvôli testom som sa do VM prihlásil ako `user` cez nový greeter (heslo zadal `wtype`). Na konci
  práce sa odhlásim.

### 23. 9. 2026, 21:15: vlastný greeter LatteOS ✅ (je predvolený)
- `session/greeter/shell.qml`: obrazovka prihlásenia v Quickshelli (modul `Quickshell.Services.Greetd`)
  v štýle Latte. Obsahuje tapetu, veľké hodiny (Fraunces), sklenenú kartu so šálkou, meno a heslo,
  výber relácie **LatteOS / LatteOS SAFE** (predvolená podľa režimu z `latte-boot`), dôvod režimu
  vľavo dole a tlačidlá Reštartovať a Vypnúť.
- Beží pod **labwc + pixman + Qt software**, teda bez GL a GPU, na kombinácii overenej v F1.
- Otestované naostro: greetd → greeter → prihlásenie (heslo napísal automaticky `wtype`) → relácia
  LatteOS s témou Latte. Pamäť stabilná, CPU v pokoji 0 %, greeter ~90 MB + labwc ~50 MB.
- `/etc/latteos/boot.toml`: `greeter = "latte"`. Ak greeter do 10 s spadne, nasleduje `tuigreet`.
  Návrat na textový: `greeter = "tui"`.
- Naposledy prihlásené meno si pamätá v `/var/lib/greetd/latte-last-user`.
- Screenshoty: `setup/f1/results/latte-greeter-live.png`, `latteos-session-latte.png`.

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
2. **Malý AI model do VM na skúšku?** Text Bar v režime AI potrebuje model v Ollame. Vo VM (11 GB RAM)
   by sa hodil malý model (~1–2 GB, napr. qwen2.5:1.5b). Qwen3-14B-sk (~9 GB v Q4) až na HW. Nič som
   nesťahoval.
3. **Predvolený režim okien:** dal som **nekonečnú pásku** (srdce návrhu). Radar ale varuje, že
   nováčikovia z Windows chcú plávajúce okná. Zmena je jeden riadok (`latte/windows.lua`, `load_mode`).
