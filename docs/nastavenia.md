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

Zoznam skupín (ľavý zoznam ako vo Windows 11) a stránok. Stránka má `id`, `title`, `group`, `icon`, `description`
a `status`: `ready` (funguje), `partial` (časť), `planned` (ešte nie je; ukáže sa ako plán s odkazom na etapu z README).
Ak má stránka `domain`, jej ovládacie prvky sa skladajú zo schémy.

## Ako pripraviť Nastavenia (budúca aplikácia)

Nastavenia nemusia poznať jednotlivé kľúče, stačí:

```python
from latte_common import settings

registry = settings.Registry()
for group_id, title, pages in registry.by_group():          # ľavý strom
    ...
page = registry.page("appearance")
store = registry.store(page.domain)
for section_id, section_title, keys in store.domain.grouped():   # ovládacie prvky stránky
    for key in keys:
        store.get(key.id), store.source(key.id), store.locked(key.id)
        # key.type, key.choices, key.minimum/maximum, key.label, key.description -> vyberie sa widget
store.set("color.scheme", "light")                           # overí, zapíše, a komponenty zmenu prevezmú
```

Nikto ďalší sa neinformuje ručne: komponenty aj služba `latte-appearance` sledujú súbor a prekreslia sa sami.
Nová stránka = nová schéma a riadok v index.toml; kód Nastavení sa nemení.

### Pridanie novej domény

1. `data/settings/<doména>.schema.toml` so schémou.
2. Stránka v `data/settings/index.toml` (`domain = "<doména>"`).
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
| gtk3, qt, firefox, chromium, wine | plánované adaptéry                       | zatiaľ nie sú |

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
- Overené je GTK4/libadwaita; GTK 3, Qt, Firefox, Chromium a Wine sú zatiaľ len v pláne.

### Aktivácia

`tools/install-session.sh` nalinkuje službu a portál. Potom sa treba znovu prihlásiť (alebo
`systemctl --user restart xdg-desktop-portal`). Vývoj bez inštalácie: `tools/run-appearance.sh`.
Skúška zmeny: `latte-appearance set color.scheme light`, návrat `latte-appearance reset`.
