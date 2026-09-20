# Lišta, rohové dlaždice, farba priečinka a Heidelberg (návrh)

Písané pre vývojárov LatteOS. Je to **návrh**; v kóde sú zatiaľ kroky **R1** a **R2** (geometria lišty a matica v päte, časť 8).
Rozhodnutia autora sú v časti 0, čísla v tabuľkách sú odhady, ktoré sa dolaďujú na živom nákrese, a čo
ešte treba rozhodnúť, je v časti 9.

Vychádza z poznámok autora, z mockupu `inspo/latte desktop gui copy.png`, zo snímky popupu App
Managera s vyznačeným tvarom L, z IDEAS.md (nápady 3 a 4) a zo stavu kódu (`src/latte_shell/`,
`src/latte_files/`, `main_setting_v2.md`).

## 0. Čo je rozhodnuté

| Téma | Rozhodnutie |
|------|-------------|
| Viditeľné prvky systému | všetky sú v dolnej lište (názor sa ešte dolaďuje) |
| Rohové tlačidlá (App Manager, Device Manager) | obdĺžnik na výšku okolitej lišty, už nie štvorec a nie vyššie než lišta |
| Tvar L | **päta** = rohová dlaždica dole v lište, **kmeň** = vodorovný pás s info nad lištou (rameno L). Spolu sú to červeno orámované miesta na snímke; celý popup (žlté orámovanie) je väčší |
| Animácia | pasívna a pokojná, nie viazaná na inštaláciu ani prácu na pozadí; klik ju rozšíri z päty do kmeňa (rozšírenie, nie duplikát) |
| Dekoratívne lišty | zatiaľ pravá a ľavá (Device Manager a App Manager). Druh: jedna farba, GIF, alebo kódovaná textúra (matrix a ďalšie); všetko v Nastaveniach › Prostredie |
| Živá tapeta | neskôr; rovnaký stroj „scén“ ako lišty (časť 4) |
| Zväzky vľavo | premenovanie je len **alias** |
| Priečinky vľavo | **nesystémové** sa premenúvajú naozaj (na disku); systémové sa nepremenúvajú |
| Nápad 3 | pravý klik vľavo: Premenovať a Farba popisu |
| Nápad 4 | editor **Heidelberg** (názov Gutenberg je obsadený); začíname markdown, txt a html, s integrovaným formátovaním |

Zmena oproti README: bod 2.11 hovoril o „animovaných dlaždiciach viazaných na stav“. Toto rozhodnutie
ho nahrádza. Stavové údaje (počet aplikácií, „inštaluje sa“, bežiace procesy) ostávajú v kmeni L
ako text, nie v pohybe dlaždice.

## 1. Geometria lišty a rohov

Dnes (`src/latte_shell/app.py`):
- `BAR_HEIGHT = 104` a `CORNER = 104`; rohová dlaždica je 104 × 96, ostatné segmenty 64 × 64.
- Riadok lišty má okraje 8 (hore) a 10 (dole), segmenty majú 64 px, ale rezervované miesto
  (`set_exclusive_zone`) je 104, čo určuje výška rohovej dlaždice. Maximalizované okno preto končí
  104 px nad spodkom a nad segmentmi zostane pás rádovo 20–30 px. To je tá medzera. (Presná hodnota
  sa nameria na živej lište; pri R1 sa overí aj to, či povrch lišty nie je vyšší než rezervované miesto.)
- `BAR_HEIGHT = 104` je opísané trikrát: `app.py`, `maps.py`, `prompt.py`.

Návrh:
- Jedna výška lišty z jedného miesta (`latte_shell/geometry.py`): `BAR_HEIGHT = 84` a `SEGMENT = BAR_HEIGHT`.
  Hodnotu čítajú lišta, popupy, prompt a plocha. Zmena výšky lišty je zmena jedného čísla.
- **Všetky dlaždice** (rohy aj segmenty: hodiny, napájanie, zoznam okien, prompt, správca súborov)
  **sedia na spodnom okraji obrazovky a majú hornú hranu v rovnakej výške.** Medzi nimi je len
  vodorovná medzera 8 px; zaoblené sú len horné rohy segmentov.
- Rohová dlaždica (päta L): **výška = BAR_HEIGHT, šírka ≈ 2 × výška (168 × 84)**, pritlačená k okraju
  obrazovky (bez 12 px odsadenia). Zaoblený je len vnútorný roh; vonkajší je pri okraji obrazovky rovný.
  Päta pri okraji je predpoklad pre časť 3: kmeň L sa opiera o jej hornú hranu.
- Maximalizované okno potom končí hneď nad lištou, žiadny pás navyše.
- Text „APP MANAGER“ (monospace, 10 px) sa kreslí cez textúru, takže potrebuje jemný tmavý prechod
  pod písmom. Kontrast textu na pohyblivom pozadí patrí pod bod 3.6 (prístupnosť).

## 2. Pohyb: pasívny a pokojný

Pravidlá:
- Cyklus 6–12 s, pohyb pomalý; žiadny záblesk, žiadna zmena podľa stavu systému.
- Najviac 8–12 obr/s. Relácia beží so **softvérovým vykresľovaním** (`GSK_RENDERER=cairo`,
  `WLR_RENDERER=pixman` v `session/labwc/environment`), takže každý obrázok za sekundu je práca
  procesora. Pri pokojnom pohybe je 10 obr/s dosť.
- Pohyb sa zastaví, keď je textúra zakrytá (okno na celú obrazovku, zamknutá obrazovka).
- Tri režimy: vždy, len pod kurzorom, vypnutý. Vypnutý alebo `gtk-enable-animations = false` znamená
  statický snímok. Navigácia musí fungovať aj tak (`main_setting_v2.md`, časti 9 a 48).
- Statický snímok musí byť vždy čitateľný; nič sa nesmie spoliehať na pohyb.

## 3. Päta a kmeň ako jeden obraz

Päta je v okne lišty (vrstva TOP), kmeň je v popupe (vrstva OVERLAY, `maps.MapOverlay`). Sú to dva
rôzne povrchy Waylandu, jeden widget cez oba nejde. „Rozšírenie, nie duplikát“ sa preto rieši
spoločným zdrojom obrazu, nie spoločným widgetom.

```
┌────────────────────────────────┐
│ obsah: mriežka aplikácií       │  popup, bez textúry
├────────────────────────────────┤
│▓▓▓▓ kmeň: pás s info ▓▓▓▓▓▓▓▓▓▓│  rameno L (ARM_HEIGHT), text na textúre
├──────────┬─────────────────────┘
│▓▓ päta ▓▓│  16:24  ⏻  okná …     lišta (BAR_HEIGHT)
└──────────┘
```

Mechanizmus:
1. **Jedno plátno** (`BarTexture`) so súradnicami od rohu obrazovky. Má jedny hodiny a jeden zdroj
   obrazu (časť 4). Vlastní ho `App` v `latte-shell`, nie lišta ani popup.
2. **Dva pohľady** (`TextureView`, vlastný widget so `snapshot`): jeden v dlaždici (päta), druhý
   v kmeni popupu. Oba kreslia z toho istého plátna s posunom, takže sú vo fáze: ten istý obraz,
   ten istý čas, bez švu na hranici päty a kmeňa.
3. **Maska** je zoznam obdĺžnikov v súradniciach plátna, uplatňuje sa pri kreslení (orezanie),
   nie v uloženom súbore. Pre ľavý roh: päta `(0, 0, 168, BAR_HEIGHT)` a kmeň
   `(0, BAR_HEIGHT, MAP_WIDTH, ARM_HEIGHT)`. Preto sa L dá zmeniť (výška lišty, iný monitor) bez
   nového exportu a okraje nie sú zubaté (GIF má len 1-bitovú priehľadnosť).
4. **Otváranie**: kmeň sa vysunie z hornej hrany päty (šírka aj výška naraz, 250–350 ms, spomalený
   dobeh), potom sa objaví panel s obsahom nad ním. Zatváranie je opačne. Kým sa otvára, druhý klik
   ho zavrie, žiadne rozbehnuté animácie navyše. S vypnutými animáciami je prechod okamžitý.
5. **Pravý roh** je zrkadlová geometria (plátno má počiatok vpravo dole, kmeň je zarovnaný doprava);
   obsah ani text sa nezrkadlia.
6. **Text na kmeni**: kmeň nesie text („17 aplikácií · 3,7 GB“, tlačidlo Aktualizácie). Pod textom sa
   textúra stlmí prechodom (viditeľná pri päte, pokojná pod písmom). Miera stlmenia je voľba.

Jeden povrch pre celý L by musel byť buď v lište (TOP), alebo v popupe (OVERLAY), a dnes sú
oddelené. Dva pohľady na jedno plátno to obídu bez prestavby lišty.

## 4. Textúry a scény: jeden stroj pre lišty aj živú tapetu

Autor chce neskôr aj **živú tapetu namiesto obrázka**. Preto sa textúra nerieši ako vec rohov: je to
všeobecná **scéna**, ktorú kreslí ten, kto ju potrebuje (dnes plátno lišty, neskôr `Desktop`).

Scéna = rozhranie: `render(cr, šírka, výška, čas)`, odporúčané fps, statický snímok. Spôsob vyjadrenia
v nastaveniach je jeden reťazec, aby sa dal pridať nový druh bez zmeny schémy:

| Zápis | Druh | Cena |
|-------|------|------|
| `solid:motív` alebo `solid:#RRGGBB` | jedna farba (predvolene farba motívu) | nulová, statická |
| `scene:matrix` | stekajúci kód (zelená klasika alebo akcent motívu) | nízka, kreslené kódom (cairo) |
| `scene:gears` | ozubené prevody, pomalé otáčanie, v paletě motívu | nízka, kreslené kódom |
| `scene:glow` | pomalé svetlo: mäkké farebné škvrny plynúce po dráhach, v paletě motívu (káva, karamel) | nízka, hladké gradienty |
| `file:cesta` | GIF alebo animované WebP od používateľa | podľa súboru (pamäť, nižšie) |

Ďalšie kódované scény sa pridávajú ako jedna trieda; tri vyššie stačia na štart. Kódovaná scéna
nemá vlastný súbor, je ostrá v každom rozlíšení, dá sa zafarbiť motívom a slučka nemá šev.

### Súbory (GIF, WebP) a video

- Prehráva sa cez `GdkPixbuf.PixbufAnimation` (dekodér GIF aj WebP v systéme je, overené zoznamom
  `GdkPixbuf.Pixbuf.get_formats()`; animované WebP treba overiť na skutočnom súbore), snímky ako
  `Gdk.Texture`, vlastný časovač.
- **AVI, MP4, MKV sú len vstup strihača** (časť 5), za behu sa neprehrávajú. Na tejto VM nie je
  `ffmpeg`, GStreamer má len základné moduly (bez demuxeru AVI a bez dekodéra H.264) a modul GTK pre
  médiá som nenašiel. Prehrávanie videa by pridalo závislosť, ktorú relácia nemá, a na softvérovom
  vykresľovaní aj záťaž. Na cieľovom stroji to treba ešte overiť.
- Rozpočet pamäte: rozbalené snímky zaberú `snímky × plocha × 4 B`. Rádový príklad: L s plochou
  ~135 000 px² je pri 60 snímkach 32 MB; ohraničujúci obdĺžnik (403 000 px²) až 97 MB. Preto strihač
  ukladá plátno v polovičnom rozlíšení, drží 8–12 obr/s a najviac ~6 s, pred exportom ukáže odhad
  pamäte a nedovolí prekročiť strop (návrh 24 MB na animáciu).
- Súbory sú v `~/.local/share/latteos/animations/` (pár `<id>.webp` + `<id>.toml`), vstavané
  v `data/animations/`.

### Živá tapeta: čo z toho vyplýva vopred

Nie je to súčasť tohto návrhu, ale stroj sa má dať použiť aj tam:
- Celá obrazovka je plocha, ktorú softvérové vykresľovanie nezvládne v plnom rozlíšení a s každým
  obrázkom. Scény preto vedia kresliť v menšom rozlíšení (mäkké scény: štvrtinové, zväčšené) a
  s vlastným fps. Rozpočet sa nameria, kým sa niečo sľúbi.
- Tapeta je väčšinu času zakrytá oknami. Pohyb sa zastaví, keď ju zakrýva maximalizované okno.
  `foreign_toplevel.py` dnes číta len stavy minimalizované a aktívne; pribudnúť musia maximalizované
  a celá obrazovka (v protokole sú to stavy 0 a 3).
- Prihlasovacia obrazovka používa systémovú tapetu, takže ak má scéna platiť aj tam, patrí do
  `latte_common`, nie do `latte_shell`.

## 5. Nastavenia a strihač

Kde: **Prostredie**, stránka **Lišta a systémové menu** (`main_setting_v2.md`, časť 46) a vypínač pohybu
aj v **Animácie a efekty** (časť 48). Údaje patria do domény `appearance` (súbor
`~/.config/latteos/appearance.toml`), lebo tá už drží tapetu a `Desktop` ju sleduje; kľúče
v novej sekcii `bars` (formát schémy je v `docs/nastavenia.md`):

```toml
[section.bars]
title = "Dekoratívne lišty"

[key."bars.apps.source"]      # zápis z časti 4
type = "string"
default = "scene:matrix"
label = "Ľavý roh (App Manager)"

[key."bars.devices.source"]
type = "string"
default = "scene:gears"
label = "Pravý roh (Device Manager)"

[key."bars.motion"]
type = "enum"
choices = ["always", "hover", "off"]
labels = ["Vždy", "Len pod kurzorom", "Vypnutá"]
default = "always"
label = "Pohyb"

[key."bars.speed"]           # 1.0 = návrhová rýchlosť, menej = pokojnejšie
type = "float"
default = 1.0
min = 0.25
max = 1.5
step = 0.05
label = "Rýchlosť"

[key."bars.dim"]             # stlmenie textúry pod textom kmeňa
type = "float"
default = 0.6
min = 0.0
max = 0.9
step = 0.05
label = "Stlmenie pod textom"
```

Nastavenia ukážu živý náhľad L (päta + kmeň) pri každej voľbe. Chybný zápis alebo chýbajúci súbor
sa nahradí predvolenou scénou a ohlási sa (rovnako ako ostatné schémy).

### Strihač (importér videa)

Nedeštruktívny nástroj: uloží sa cesta k originálu a parametre, výsledok sa dá znova vyrobiť
(napr. keď sa zmení geometria L).

1. Vybrať súbor (GIF, WebP, AVI, MP4, MKV).
2. Časová os: začiatok a dĺžka (najviac ~6 s). Náhľad je jeden snímok cez
   `ffmpeg -ss <t> -frames:v 1`, nie prehrávač.
3. Náhľad ukazuje **pevnú masku L** (päta + kmeň) a pod ňou sa posúva a približuje video, nie ťahanie
   obdĺžnika po videu. Tak používateľ vidí presne to, čo bude v lište.
4. Voľby: rýchlosť (spomalenie ×0,25 až ×1), stmavenie, **vyhladenie slučky** (prelínanie posledných
   ~1 s do prvých; pri stekajúcom kóde a otáčajúcich sa prevodoch by spätný chod pôsobil zle, preto nie
   „tam a späť“).
5. Export cez `ffmpeg` (trim, rýchlosť, orez, zmenšenie, fps, prelínanie, WebP alebo GIF s paletou).

Závislosť `ffmpeg` sa kontroluje pri otvorení strihača. Ak chýba, strihač povie „Na import videa chýba
ffmpeg“ namiesto sivého tlačidla bez vysvetlenia (rovnaký princíp ako „tichá degradácia je zakázaná“
pri bode 9.1). Balík `ffmpeg-free` môže mať obmedzené dekodéry (H.264, DivX); overiť pred sľubom,
že sa dá otvoriť každé AVI.

## 6. Nápad 3: premenovanie a farba priečinka v bočnom paneli

Znenie z IDEAS.md: pravým klikom na priečinok vľavo sa dá premenovať, v tom istom menu má byť aj
farba popisu priečinka.

Stav kódu (`src/latte_files/app.py`):
- Zväzky vľavo majú menu (Premenovať, Odpojiť, Pripojiť); meno je **alias** v `volumes.toml` podľa UUID.
- Obľúbené priečinky majú menu len s „Odobrať z obľúbených“; `favorites.toml` drží len cestu.
- `popup_menu()` vie iba textové tlačidlá v oddieloch.
- Skutočné premenovanie existuje len v hlavnom paneli (`do_rename`): `os.rename`, pri odmietnutí
  ponuka správcu cez polkit.

Rozhodnuté:
- **Zväzky**: „Premenovať“ = alias (bez zmeny).
- **Nesystémové priečinky**: „Premenovať“ = skutočné premenovanie na disku.
- **Farba**: pri oboch, farbí sa text popisu.

### Čo je systémový priečinok

Nesmie sa premenovať, lebo na jeho mene závisia iné časti systému. Návrh definície (jedna funkcia
`is_system_folder(path)` v `latte_common/places.py`, ktorú použije aj hlavný panel):
- korene zväzkov a položky `SYSTEM_ENTRIES` (Apps, Users, Shared),
- domov používateľa a jeho Kôš (`places.trash_files()`),
- priečinky, na ktoré sa odvolávajú aplikácie: `~/Desktop` (ikony plochy v lište) a používateľské
  priečinky z `~/.config/user-dirs.dirs` (Dokumenty, Stiahnuté…).

Pri systémovom priečinku sa položka „Premenovať“ neskryje, ale ukáže sa neaktívna s dôvodom
(„Systémový priečinok“), aby používateľ nehľadal, kam zmizla. Farbu a odobratie z obľúbených
systémové priečinky majú aj tak. Hranica je návrh, treba ju potvrdiť (otázka 1 v časti 9).

### Skutočné premenovanie zo strany panela

- Logika z `do_rename` sa vytiahne do funkcie `rename_path(src, nové_meno)`, ktorú použije hlavný
  panel aj bočný. Pri odmietnutí ostáva rovnaká ponuka správcu.
- **Po premenovaní sa musia prepísať cesty v `favorites.toml`**: položka sama a všetky obľúbené
  vnútri premenovaného priečinka (predpona). Bez toho by priečinok vľavo zmizol do „nedostupné“.
  Dnes sa to stane už pri premenovaní v hlavnom paneli, takže oprava pomôže obom miestam. Rovnaký
  problém je pri presune priečinka (`transfer`); mimo tohto návrhu, ale rovnaká funkcia `moved(old, new)`.
- Alias pri obľúbených netreba (kľúč `name` sa neprevádza); alias je len pri zväzkoch.

### Farba

- Nový kľúč `color` pri položke v `favorites.toml` (a voliteľne aj v `volumes.toml`, lacné a zrejmé,
  lebo zväzky sú v tom istom paneli).
- Výber z **pevnej palety pomenovaných farieb** (7–8 a „bez farby“) z motívu
  (`data/themes/*/theme.toml`), nie voľné RGB. Dôvod: každá farba musí mať kontrast AA na pozadí
  bočného panelu v tmavom, svetlom aj vysokom kontraste; `tests/test_theme.py` už kontroluje AA
  a rozšíri sa o tieto farby.
- Zobrazenie: CSS trieda `.label-color-<id>` na štítku v `fill_favorites()` (a `fill_sidebar()`).
- `popup_menu()` sa rozšíri o položku typu „riadok farebných bodiek“.
- **Zmeny API**: `favorites.load()` vracia dnes zoznam ciest a `save()` zapisuje len `path`, takže
  by zahodil cudzie kľúče. Pridá sa `favorites.entries()` (zoznam slovníkov, `load()` ostane kvôli
  volajúcim), `set_color()`, `moved()` a `save()` zachová neznáme kľúče.
- Testy (`tests/test_favorites.py` už existuje): zachovanie kľúčov, neznáma farba sa ignoruje,
  `moved()` prepíše aj vnorené cesty, `is_system_folder()` na hraničných prípadoch
  (`tests/test_places.py` už existuje).
- Mimo rozsahu: farba pre ľubovoľný priečinok v hlavnom paneli (ako štítky vo Finderi). Kľúčom by
  bola cesta, ktorá sa pri premenovaní alebo presune stráca. Riešiť samostatne, ak bude záujem.

## 7. Nápad 4: Heidelberg, editor dokumentov LatteOS

Názov: pôvodne Gutenberg, ten je obsadený, preto **Heidelberg** (príkaz `latte-heidelberg`).

Znenie z IDEAS.md: originálny editor dokumentov; vie otvoriť, upraviť, uložiť a formátovať rôzne
druhy textových súborov: txt, rtf, doc, mobi, epub, md, xml, html, json, .pages, odt, vrátane pdf,
ak to nie je nemožné.

Nie všetky formáty sú rovnako ťažké. Poctivé rozdelenie podľa toho, čo sa dá urobiť:

| Úroveň | Formáty | Čo Heidelberg vie |
|--------|---------|-------------------|
| **A. Text (začíname)** | **md, txt, html**, potom json a xml ako zdroj | úprava a uloženie; formátovanie je súčasťou okna (nižšie) |
| **B. Formátovaný text** | rtf, odt | podmnožina: odseky, nadpisy, tučné, kurzíva, zoznamy, obrázky |
| **C. Cudzie kancelárske** | docx | rovnaká podmnožina ako B; upozornenie, že uloženie nemusí zachovať všetko |
| **D. Len čítanie / kópia** | doc, .pages, epub, mobi | otvoriť na čítanie, uložiť ako **novú kópiu** v odt (LibreOffice má filtre pre doc aj Pages, overiť; epub sú zip s XHTML; mobi len cez prevod) |
| **E. PDF** | pdf | zobraziť, vyhľadať, kopírovať text, poznámky, spájať a preusporiadať strany (poppler). **Úprava textu vo vnútri PDF nie je reálna** |

### Etapa H1: markdown, txt a html s integrovaným formátovaním

Integrované formátovanie = panel nástrojov a skratky priamo v okne (tučné, kurzíva, nadpis, zoznam,
citát, kód, odkaz), nie okno na preklopenie do iného programu. Čo je možné, závisí od formátu, a to
sa ukáže poctivo:

| Formát | Plocha na úpravu | Formátovanie |
|--------|------------------|--------------|
| **txt** | obyčajný text | tlačidlá sú neaktívne s dôvodom („Obyčajný text formátovanie nemá“) a ponuka „Uložiť ako Markdown“ |
| **md** | zdrojový text so živým štýlovaním (nadpisy väčšie, tučné tučné, značky stlmené) | tlačidlá vkladajú a prepínajú značky (`**`, `#`, `-`, `>`…). Súbor sa nemení, kým používateľ nezasiahne, takže **bez straty** |
| **html** | formátovaný pohľad pre podmnožinu značiek; vždy aj **Zdroj** | tlačidlá formátujú model a zapíšu čistý HTML. Dokument s inými prvkami (tabuľky, `style`, `script`, rozloženie cez `div`) sa otvorí v režime Zdroj s upozornením, aby sa nič potichu nestratilo |

Technický základ:
- Plocha je `GtkSource.View` (GtkSourceView 5 je v systéme, overené) s tagmi. Nové závislosti nie sú
  potrebné okrem toho; knižnice na markdown (`markdown`, `markdown-it`, `mistune`) v systéme nie sú.
- **Model dokumentu** (odseky s formátovanými úsekmi: nadpis, tučné, kurzíva, kód, odkaz, zoznam,
  citát) potrebuje html a prevod medzi formátmi. Markdown má malý vlastný tokenizér (nadpisy,
  zdôraznenia, kód, zoznamy, citáty, odkazy), ktorý slúži pre živé štýlovanie a pre prevod do modelu.
  HTML sa číta cez `html.parser` zo štandardnej knižnice.
- „Uložiť ako“ medzi md, html a txt ide cez model (md → html je prvý užitočný prevod).
- Zachová sa kódovanie (UTF-8, rozpoznanie BOM) a zakončenia riadkov (CRLF sa nezmení na LF);
  zápis ide cez dočasný súbor a premenovanie ako inde v prostredí.
- Osnova dokumentu (nadpisy) v ľavom paneli podľa nápadu 1 (priesvitný ľavý panel cez celú výšku
  okna). Priesvitnosť čaká na vlastný kompozitor (bod 3.5), do tej doby je panel plnofarebný.
- Formáty a model sú čistý Python bez GTK, testovateľné ako `latte_common` (`tests/test_heidelberg_*.py`).
- Nový príkaz je predvoleným otváračom pre md, txt a html zo správcu súborov.

### Ďalšie etapy

- **H2** rtf a odt (čítanie a zápis podmnožiny, štítok vernosti).
- **H3** docx (zápis podmnožiny s upozornením), epub na čítanie.
- **H4** doc, pages a mobi cez prevod; pdf (zobrazenie, poznámky).

Pravidlo pre všetky etapy: pri otvorení sa ukáže **štítok vernosti** (Plná / Čiastočná / Len čítanie),
podobne ako štítky pôvodu v App Manageri. Ak uloženie zahodí, čo Heidelberg nepozná, používateľ to
vidí *pred* uložením (pravidlo poctivosti z README: bez tichej straty). Tabuľky, hlavičky a pätičky,
obtekanie obrázkov a presné rozloženie strán nie sú cieľ prvých verzií. `.pages` je uzavretý formát
Applu: čítať sa dá cez LibreOffice, zapisovať sa nesľubuje.

## 8. Poradie práce

Rohy (časti 1–5) sa robia po krokoch, každý overiteľný bez ďalších:

| Krok | Obsah | Ako sa overí |
|------|-------|--------------|
| R1 ✅ | `geometry.py`, jedna výška lišty, obdĺžnikové rohy, jedna hodnota namiesto troch `104` | izolovaná skúška lišty (headless labwc + grim): maximalizované okno bez medzery |
| R2 ✅ | rozhranie scény, `solid` a `scene:matrix`, plátno len v päte | snímka a zaťaženie procesora pri 10 obr/s |
| R3 | maska L, pohľad v kmeni popupu, animácia otvárania | snímky v štyroch fázach; fázová zhoda päty a kmeňa |
| R4 | kľúče `bars.*`, `scene:gears`, `scene:glow`, výber v Nastaveniach s náhľadom | test schémy a modelu, načítanie poškodeného zápisu |
| R5 | `file:` (GIF, WebP) | skúšobný súbor, rozpočet pamäte |
| R6 | strihač (ffmpeg) | export skúšobného klipu, odhad pamäte |

Skúšky sa robia v izolovanej relácii (vlastná zbernica, headless labwc), nie v živej.

**R1, stav (2026-09-20).** Výška lišty je 84 px (`latte_shell/geometry.py`); rohy (168 × 84) aj segmenty
sú pritlačené k spodnému okraju s hornou hranou v rovnakej výške. Namerané v izolovanom labwc
s maximalizovaným oknom: pod oknom bolo predtým 104–106 px (podľa stĺpca), teraz 84 px všade;
povrch lišty je 84 px vysoký (rovný rezervovanému miestu); popupy (mapy, hodiny, systémové menu,
prompt) ležia na lište bez medzery, resp. so šesťpixelovou medzerou ako predtým.
Zostáva do R3: ľavá hrana ramena mapy aplikácií je na `COLUMN + 40 = 144` px, dlaždica je široká 168 px,
takže rameno začína o 24 px nad dlaždicou. Kmeň sa v R3 prekreslí na celú šírku popupu, preto sa
to teraz neopravuje.

**R2, stav (2026-09-20).** Scény sú v `latte_common/scenes.py` (`Solid`, `Matrix`, `parse`; obraz je čistá
funkcia času, scéna kreslí len orezanú oblasť). Plátno a pohľad sú v `latte_shell/bar_texture.py`:
`BarTexture` kreslí raz za snímku do spoločného povrchu (len tú časť, ktorú niektorý pohľad
ukazuje), `TextureView` z neho kopíruje svoj výsek. Ľavá dlaždica (App Manager) ukazuje maticu, pravá
zostáva obyčajná z motívu (`DEFAULT_SOURCES`, v R4 to nahradia nastavenia; `gears` príde v R4).
Časovač beží, len kým je pohľad zobrazený, scéna sa hýbe a `gtk-enable-animations` je zapnuté; inak
sa ukáže statický snímok v pevnom čase. Namerané v izolovanom labwc: 10 obr/s stojí 2,7 až 3,3 %
jedného jadra procesu lišty (bez textúry 0 %; kompozitor a monitor sú mimo merania, headless), so
vypnutými animáciami sú dva snímky v odstupe 1,5 s bajt po bajte rovnaké. Päta ukazuje len spodných
6 riadkov plátna (kmeň s hornými riadkami príde v R3), preto je v nej zatiaľ pokojne a redšie.
Textúra je zatiaľ len v päte, farba v CSS (`.corner-scrim`) je pevná, nie z motívu. Zápis `solid:motív`
zatiaľ nie je (`parse` pozná `solid:#RRGGBB` a `scene:matrix`); farby motívu sa do scén dostanú v R4.
Pozor pri ďalších pohľadoch: pohľad textúry v `Gtk.Overlay` nesmie mať `hexpand` (dlaždica by
si vzala časť voľného miesta) ani vlastnú minimálnu výšku (okraj tlačidla by zväčšil lištu o pixel);
`TextureView` preto nemá žiadnu vlastnú veľkosť a dlaždica sa nastavuje na jej rozmer.

Farba a premenovanie vľavo (časť 6) sú nezávislé od rohov a sú malé; poradie vnútri: `favorites`
(entries, moved, color) a `is_system_folder` s testami, potom `rename_path`, nakoniec menu.
Heidelberg (časť 7) je samostatná aplikácia; s lištou súvisí len cez App Manager, správcu súborov
a okná.

## 9. Otvorené otázky

1. **Hranica „systémový priečinok“** (časť 6): domov, Kôš, korene zväzkov, `SYSTEM_ENTRIES`, `~/Desktop`
   a používateľské priečinky (Dokumenty, Stiahnuté…). Zodpovedá to zámeru, alebo majú byť
   Dokumenty a spol. premenovateľné?
2. **Veľkosť päty**: 168 × 84 je odhad. Rozhodne živý nákres.
3. **Farba matrixu**: zelená klasika predvolene, akcent motívu ako voľba. Súhlasíš?
4. **Prevody a „pomalé svetlo“** ako kódované scény: chceš ich, alebo iné (napr. dážď na skle podľa
   tapiet)? Dajú sa pridať kedykoľvek, tri stačia na štart.
5. **Čo prvé**: začať R1 (geometria) hneď, alebo najprv malý celok z časti 6 (farba a
   premenovanie vľavo)?
