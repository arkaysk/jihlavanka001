# Nastavenia systému a Prispôsobenie

Písané pre vývojárov LatteOS: ako sú nastavenia uložené, ako sa pridáva nová stránka do Nastavení
a ako Prispôsobenie zjednocuje vzhľad aplikácií.

## Jeden súbor, alebo viac?

**Jeden súbor na doménu**, nie jeden veľký súbor pre všetko.

| Doména      | Súbor používateľa                | Schéma                                | Kto ju používa  |
|-------------|----------------------------------|---------------------------------------|-----------------|
| appearance  | ~/.config/latteos/appearance.toml | data/settings/appearance.schema.toml  | latte-appearance, celé prostredie |
| clock       | ~/.config/latteos/clock.toml      | data/settings/clock.schema.toml       | latte-shell (manažér času) |
| prompt      | ~/.config/latteos/prompt.toml     | data/settings/prompt.schema.toml      | latte-shell (prompt, AI) |

Prečo nie jeden súbor:
- Komponent číta len to, čo potrebuje, a sleduje zmeny len svojho súboru (`settings.watch`), takže
  zmena písma neprebúdza hodiny.
- Chyba v jednom súbore (zlý zápis rukou) pokazí jednu doménu, nie celý systém. Problém sa ohlási
  (stderr, `Store.problems`, `latte-appearance status`), použijú sa predvolené hodnoty.
- Domény vlastnia rôzne komponenty a rôzne vrstvy (správca zamkne len to, čo chce).
- Nová doména = nový súbor a nová schéma, bez zásahu do ostatných.

Prečo nie súbor na každý kľúč: Nastavenia by museli spájať stovky súborov a zmena viacerých hodnôt
naraz (napr. motív a akcent) by nebola atomická. Jedna doména sa zapíše jedným premenovaním súboru.

## Tri druhy údajov, ktoré sa nemiešajú

| Druh       | Čo to je                                              | Kde                        |
|------------|-------------------------------------------------------|----------------------------|
| nastavenia | voľby, ktoré si používateľ vedome zvolil              | ~/.config/latteos/*.toml (schéma v data/settings/) |
| stav       | čo si komponent pamätá sám (polohy okien, históriu)   | ~/.local/state/latteos/    |
| dáta       | súbory dodané systémom (motívy, tapety, profily)      | data/ (v repozitári), /usr/local/share/latteos, ~/.local/share/latteos |

Do nastavení patrí len to, čo má zmysel ukázať v Nastaveniach. Ostatné do stavu.

## Vrstvy hodnôt

predvolené (schéma) < správca (`/etc/latteos/<súbor>`) < používateľ (`~/.config/latteos/<súbor>`)

- `Store.get(kľúč)` vráti účinnú hodnotu, `Store.source(kľúč)` povie, odkiaľ je (default, admin, user).
- `Store.locked(kľúč)` je pravda, ak hodnotu určil správca: Nastavenia ju ukážu zamknutú.
- Zápis ide vždy do súboru používateľa, atomicky (dočasný súbor a premenovanie). Kľúče, ktoré schéma
  nepozná, sa pri zápise zachovajú.
- Neplatná hodnota (zlý typ, mimo rozsahu, neznáma voľba) sa **neuloží** a hlási sa. Hodnota zo súboru,
  ktorá neprejde overením, sa nahradí predvolenou a problém sa zapíše do `Store.problems`. Nič sa nestane potichu.

## Formát schémy (`data/settings/<doména>.schema.toml`)

```toml
[domain]
id = "appearance"            # rovnaké ako názov súboru pred .schema.toml
title = "Prispôsobenie"
file = "appearance.toml"
owner = "latte-appearance"
scope = "user"               # user | system

[section.color]              # oddiely = nadpisy skupín v stránke Nastavení
title = "Farby"

[key."color.scheme"]         # id kľúča: "oddiel.názov" (v súbore [color] scheme = ...) alebo len "názov"
type = "enum"                # bool | int | float | string | enum | color | path
choices = ["dark", "light"]  # len pre enum
default = "dark"
label = "Farebný režim"      # text v Nastaveniach
description = "..."
apply = "live"               # live = hneď | session = po novom prihlásení | restart = po reštarte komponentu
```

Ďalšie polia: `min`, `max`, `step`, `unit` (čísla), `allow_empty = true` (prázdny text znamená „nenastavené“,
napr. vlastný akcent), `hidden = true` (interný kľúč, v Nastaveniach sa nezobrazí).

## Strom Nastavení (`data/settings/index.toml`)

Strom sleduje návrh main_setting_v2.md: **päť oblastí a Systém** (`software`, `data`, `hardware`, `account`,
`environment`, `system`). Oblasť je to, čo vidí používateľ; technické domény so schémami sa do nej mapujú cez stránky
(jedna doména môže mať viac stránok: Prispôsobenie je v Prostredí ako Motív a farby, Písmo, Pozadie, Okná, Prístupnosť).

Stránka (`[[page]]`) má `id`, `title`, `group` (oblasť), `icon`, `description` a `status`: `ready` (funguje), `partial` (časť),
`planned` (ešte nie je; ukáže sa plán z `contents` a etapa z README). Adresa stránky je `settings://oblasť/stránka`
(`Page.uri`, `Registry.resolve` prijme aj samotné id).

| Pole       | Význam |
|------------|--------|
| `domain`, `sections` | Doména so schémou a ktoré jej oddiely stránka ukazuje (bez `sections` všetky). Ovládacie prvky sa skladajú zo schémy. |
| `owner`    | Špecializovaný správca, ktorý operácie vlastní (App Manager, Správca zdrojov, ...). Nastavenia ich len ukážu. |
| `launch`   | Čo otvorí tlačidlo „Spravovať v ...“ (zatiaľ `files`). |
| `view`     | Vlastný obsah stránky v aplikácii (`about`, `storage`), keď nejde o schému. |
| `keywords` | Synonymá pre vyhľadávanie, bez diakritiky („wifi“ nájde Sieť). |
| `contents` | Čo stránka bude obsahovať; ukáže sa, kým je plánovaná. |

Oblasť (`[group.<id>]`) má `title` a `description`.

## Aplikácia Nastavenia (`src/latte_settings/`)

Spustenie: tlačidlo **Nastavenia** v menu napájania v lište, alebo `latte-settings [settings://oblasť/stránka]`
(`tools/run-settings.sh`). Druhé spustenie použije už otvorené okno a prejde na zadané miesto.

- `model.py` je logika bez GTK (hľadanie, stavy oblastí, nedávne stránky), pokrytá tests/test_settings_model.py.
- `controls.py` skladá riadok z kľúča schémy podľa typu (bool, enum, číslo, farba, cesta, text). Zapisuje len cez `Store.set`/`reset`,
  neplatná hodnota sa ukáže pod riadkom a neuloží sa. Riadok sa obnoví sám, ak súbor zmení niekto iný.
- `pages.py` sú stránky (domov, prehľad oblasti, zo schémy, plán, O LatteOS, Úložisko, výsledky hľadania) a inšpektor vpravo.
- `app.py` je okno: vrstvené karty oblastí vľavo, obsah, inšpektor. Vzhľad preberá pravidlá správcu súborov z `data/styles/latte.css`
  (pruh nástrojov, `.files-sidebar`, `.pane`, `.files-inspector`); nové sú `.area-card`, `.settings-*`, `.status-glyph`.

Pravidlá, ktoré kód dodržiava: Nastavenia integrujú stav a navigáciu, nie implementácie (operácie inej komponenty ukážu len ako odkaz);
stav nikdy nenesie iba farba (symbol `● ! × ↻ ○` + text); oblasť bez skutočného údaju ukáže „Zatiaľ len plán“, nie vymyslené OK;
hlavné karty sa neposúvajú, posúva sa len zoznam stránok vnútri aktívnej karty.

## Skladanie stránky zo schémy

Nastavenia nemusia poznať jednotlivé kľúče, stačí:

```python
from latte_common import settings

registry = settings.Registry()
for group_id, title, pages in registry.by_group():          # oblasti a ich stránky
    ...
page = registry.page("theme")
store = registry.store(page.domain)
for section_id, section_title, keys in registry.page_sections(page):   # len oddiely tejto stránky
    for key in keys:
        store.get(key.id), store.source(key.id), store.locked(key.id)
        # key.type, key.choices, key.choice_label(v), key.minimum/maximum, key.label, key.description -> vyberie sa widget
store.set("color.scheme", "light")                           # overí, zapíše, a komponenty zmenu prevezmú
```

Nikto ďalší sa neinformuje ručne: komponenty aj služba `latte-appearance` sledujú súbor a prekreslia sa sami.
Nová stránka = nová schéma a riadok v index.toml; kód Nastavení sa nemení. Texty volieb enumu dáva `labels` v schéme
(rovnaký počet ako `choices`).

### Pridanie novej domény

1. `data/settings/<doména>.schema.toml` so schémou.
2. Stránka (alebo viac, s `sections`) v `data/settings/index.toml` (`domain = "<doména>"`).
3. Komponent číta cez `Registry().store("<doména>")`, nie vlastným parserom; na živú zmenu `settings.watch([súbor], on_change)`.
4. Test v tests/ (vzor: tests/test_settings.py).

## Prispôsobenie (doména appearance)

Zdroj pravdy je `~/.config/latteos/appearance.toml` a balík motívu `data/themes/<id>/theme.toml`.
Služba **latte-appearance** z nich vyrába vrstvy pre jednotlivé druhy okien a drží ich zosúladené
(ak niekto zmení vygenerovaný súbor ručne, služba ho vráti, `latte-appearance status` ukáže „zmenené mimo Nastavení“).

| Vrstva        | Čo sa generuje                                               | Ako sa prejaví zmena |
|---------------|--------------------------------------------------------------|----------------------|
| latte         | CSS premenné `--latte-*` pre vlastné komponenty (lišta, správca súborov, prihlásenie) | hneď, bez reštartu |
| compositor    | `~/.config/labwc/themerc-override`: rámy, titulky, menu; téma `~/.local/share/themes/LatteOS/labwc/` s ikonami tlačidiel okien (rc.xml ju vyberá) | hneď (`labwc -r`) |
| portal        | xdg-desktop-portal backend `org.freedesktop.impl.portal.desktop.latteos`: farebný režim, akcent, kontrast, písmo, tlačidlá okien | hneď v GTK4, libadwaita, Flatpak |
| gtk4          | `~/.config/gtk-4.0/gtk.css`: farby libadwaita (svetlý základ a tmavý cez `@media (prefers-color-scheme: dark)`, preto sa prepína aj v bežiacej aplikácii) | nová aplikácia hneď, bežiaca podľa režimu |
| gtk-settings  | `settings.ini` GTK 3 a 4                                     | po novom spustení aplikácie |
| gtk3 | zosúladené cez GTK settings.ini            | základné voľby GTK 3 |
| qt, kde | zosúladené cez KDE farebnú schému | Qt/KDE farby, Gwenview/Dolphin/Kate/Okular; platform plugin ešte závisí od systému |
| firefox, chromium, wine | plánované adaptéry                       | zatiaľ nie sú |

Tlačidlá minimalizovať, maximalizovať a zavrieť majú vo všetkých troch druhoch okien (vlastné komponenty, libadwaita aplikácie,
rám od labwc) rovnaký vzhľad: plochý symbol, plocha 30x24, odstup 4, pri prejdení myšou zaoblený podklad. GTK a libadwaita to
rieši CSS (`window_controls_css`, libadwaita kreslí kruh na obrázku vnútri tlačidla, preto sa ruší tam), labwc SVG ikony
(`labwc_buttons`, rovnaké tvary ako symbolické ikony Adwaita, farby z motívu).

Výška záhlavia (hrúbka horného pruhu) je jeden parameter `window.titlebar` (46 až 64 px, predvolene 46): premenná
`--latte-titlebar-height` pre vlastné komponenty (ich hlavička má triedu `latte-titlebar`), `min-height` headerbaru v gtk.css
pre libadwaitu (`titlebar_css`) a `window.titlebar.padding.height` v themerc pre rám od labwc. Zmerané vo vnorenom labwc:
všetky druhy okien sa zhodujú na jeden pixel (46 aj 58 px). Pod 46 px sa nedá zísť, lebo libadwaita hlavička má tlačidlá
34 px a výplň 12 px. Aplikácie s vlastnou lištou pod hlavičkou (napr. karty v Textovom editore) majú v hlavičke o 5 px
viac, preto pre `.collapse-spacing` platí výška zmenšená o `COLLAPSED_SPACING_EXTRA`. Iná štruktúra okna môže dať
inú odchýlku, preto je to úroveň „zosúladené“, nie „vynútené“.

V gtk.css je vygenerovaná časť ohraničená značkami `>>> LatteOS` a `<<< LatteOS`, v settings.ini sa menia len kľúče,
ktoré Prispôsobenie riadi; zvyšok súboru používateľa sa nemení. `latte-appearance release` všetko, čo LatteOS spravuje, odstráni.

### Úrovne vynucovania a okná, kde sa to nedá

Profily sú v `data/appearance-profiles/` (formát v src/latte_common/appprofiles.py, výpis: `latte-appearance profiles`).

| Úroveň      | Význam                                                            |
|-------------|-------------------------------------------------------------------|
| vynútené    | vzhľad preberie aplikácia cez portál alebo kód LatteOS            |
| zosúladené  | farby preberie z konfigurácie (gtk.css, politiky)                 |
| odporúčané  | riadi sa len farebným režimom, zvyšok má vlastný                  |
| nedostupné  | aplikácia kreslí všetko sama; nedá sa nič vynútiť                 |

Pre okná pod úrovňou „zosúladené“ platí náhradné riešenie: rám a titulok kreslí kompozitor v téme LatteOS,
okno dostane poctivú značku „vlastný vzhľad“ a pre Windows a Android aplikácie režim kompatibility (rám a titulok,
obsah ostáva). Farby obsahu cudzieho okna sa **nikdy nemenia filtrom** (invertovanie ničí fotky a videá).

### Formát motívu

`data/themes/<id>/theme.toml`: `[theme]` (id, name), `[shape]` (polomery), a pre každý variant (`dark`, `light`)
`[<variant>.colors]`, `[<variant>.tint]`, `[<variant>.panels]`. Farby sú pomenované podľa úlohy
(`fg`, `fg-dim`, `accent`, `on-accent`, `danger`, ...), nie podľa odtieňa. Motív s jedným variantom je platný:
Prispôsobenie ho použije aj pre druhý režim a ohlási to. Vlastné motívy: `~/.local/share/latteos/themes/<id>/theme.toml`.
Kontrast textu voči pozadiu (AA) sa nekontroluje pri načítaní, ale testom (tests/test_appearance.py) pre dodané motívy; vlastný motív si ho treba overiť sám.

### Známe obmedzenia

- Portál nevie doručiť presný akcent: libadwaita ho zaokrúhli na najbližší z deviatich štandardných.
  Presný akcent preto prenáša gtk.css a vlastné komponenty.
- Zvýrazňovanie kódu v textovom editore má vlastnú schému (GtkSourceView), Prispôsobenie ju nemení.
- Overené je GTK4/libadwaita a základné GTK 3/Qt/KDE výstupy. Qt/KDE adaptér generuje štandardnú farebnú schému bez prepisovania `kdeglobals`; úplné automatické načítanie cez `QT_QPA_PLATFORMTHEME=kde` závisí od dostupnosti KDE platform pluginu v systéme. Firefox, Chromium a Wine sú zatiaľ len v pláne.

### Aktivácia

`tools/install-session.sh` nalinkuje službu a portál. Potom sa treba znovu prihlásiť (alebo
`systemctl --user restart xdg-desktop-portal`). Vývoj bez inštalácie: `tools/run-appearance.sh`.
Skúška zmeny: `latte-appearance set color.scheme light`, návrat `latte-appearance reset`.

## Správca zariadení a Obrazovky

Cesta od hardvéru k nastaveniu: **detekcia → skupiny → stránka Nastavení → uloženie → použitie pri prihlásení**.

| Vrstva | Modul | Čo robí |
|--------|-------|---------|
| detekcia | `latte_common/hardware.py` | Inventár všetkého hardvéru bez práv správcu (sysfs, /proc, `lspci`, `lsblk`) a monitorov od kompozitora. Každé zariadenie je v jednej skupine podľa toho, čo robí (USB klávesnica je Vstup, USB disk je Disk). Čo sa nedá zistiť, ide do `problems`, nič sa nehlási potichu. |
| monitory | `latte_common/outputs.py` | Klient protokolu `wlr-output-management` (bez závislostí, ako `foreign_toplevel.py`): zoznam monitorov s režimami z EDID a zmena režimu, mierky a otočenia. |
| model a uloženie | `latte_common/displays.py` | Identita monitora (výrobca-model-sériové číslo, nie port), ponuka rozlíšení a frekvencií, odporúčané hodnoty, `~/.config/latteos/displays.toml`. |
| stránka | `latte_settings/display.py` | Hardvér › Obrazovky. Použitie vyžaduje potvrdenie do 15 s, inak sa zmena vráti (aj pri zatvorení okna). Enter = ponechať, Esc = vrátiť. |
| príkazy | `latte_devices/app.py` | `latte-devices list [--json]`, `display list`, `display set VÝSTUP 1920x1080@60 [--scale] [--transform] [--save]`, `display apply`. |

**Prečo sa ukladá:** labwc si nastavenie výstupov nepamätá, `session/labwc/autostart` preto pri prihlásení spustí
`latte-devices display apply`. Uložený režim, ktorý monitor už nemá, sa nepoužije a ohlási sa; monitor, ktorý nie je zapojený, sa preskočí.

**Správca zdrojov (ZDROJE v lište)** ukazuje zariadenia ako dlaždice (veľká ikona v zaoblenom štvorci, názov, stav) po skupinách
v dvoch stĺpcoch. Záložka **Zariadenia**: obrazovky, grafické karty, zvukové karty, sieťové karty (Ethernet aj Wi-Fi), optické
mechaniky, disky, klávesnice a myši, kamery, Bluetooth, napájanie, počítač (procesor, pamäť), čipset. Záložka **Siete**: sieťové karty,
pripojenia a VPN (z NetworkManagera cez `nmcli`, len na čítanie). Ukazuje **zariadenia, nie ich obsah**: žiadne zdieľané priečinky,
zväzky ani súbory (to je Správca súborov). Vlastné ikony (grafická karta, procesor, pamäť) sú v data/icons/, ostatné z témy.

**Prístup k nastaveniam zariadenia** (Správca zdrojov, ZDROJE v lište): klepnutím sa zariadenie vyberie a v ramene L sa objaví veľké
tlačidlo **Nastavenia** (cieľ pre prst, funguje aj myšou a klávesnicou). Rýchlejšie cesty pre myš: dvojklik a pravý klik
(kontextové menu), pre dotyk dvojité klepnutie a dlhé podržanie. Každá skupina vie, kam patrí (`hardware.GROUPS`), pri monitore sa otvorí
rovno ten monitor: `settings://hardware/display/<konektor>` (tretia časť adresy je objekt stránky, `Registry.split_object`).

Skúška bez GUI: v izolovanom labwc (`WLR_BACKENDS=headless`) `latte-devices display set HEADLESS-1 1280x720 --scale 1.5 --save`.
Testy: tests/test_outputs.py (protokol proti falošnému kompozitoru), test_displays.py, test_hardware.py.

## Kôš v súkromnom priestore

Skutočný Kôš je podľa freedesktop v `~/.local/share/Trash/files`, používateľovi sa ale neukazuje technická cesta.
`latte_common/places.py` ho v Správcovi súborov zloží na zložku **Kôš** v jeho súkromnom priestore:
`Tento počítač › System › home › meno › Kôš`. V domovskej zložke je Kôš aj ako zložka s počtom položiek, záhlavie okna hovorí „Kôš“
a „..“ z Koša vedie do domova. Skutočné umiestnenie sa nemení (funguje `Gio.File.trash` aj iné aplikácie). Kôš (`files`, `info`,
mód 0700) sa pripraví pri štarte Správcu súborov, ak chýba. Každý používateľ má svoj Kôš vo svojom domove, ktorý iný účet nevidí.

## Používatelia

Vytváranie účtov vyžaduje roota, preto to robí skript, nie aplikácia: `su -c 'sh tools/create-users.sh'` vytvorí **arkay** a **kenshi**
(bežné účty bez práv správcu, domov 0700, vlastný Kôš, na konci sa pýta heslo). Existujúci účet nemení. Iný zoznam:
`USERS="anna:Anna Nováková,peter:Peter" sh tools/create-users.sh`. Prihlasovacia obrazovka ich ukáže sama (UID od 1000, s platným shellom).
Test skriptu s falošnými príkazmi: tests/test_create_users.py.
