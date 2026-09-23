# Lišta, rohové dlaždice, farba priečinka a Heidelberg (návrh)

Písané pre vývojárov LatteOS. Je to **návrh**; v kóde sú zatiaľ kroky **R1** až **R5** (geometria, kmeň L, nastavenia a scény, vlastné súbory; časť 8). Zostáva R6.
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
- Jedna výška lišty z jedného miesta (`latte_shell/geometry.py`), predvolene 84 px. Od 2026-09-21 je to
  **nastavenie** (`bar.height` v appearance.toml, Nastavenia › Prostredie › Lišta a systémové menu,
  posuvník 48 až 96 px po 2), ktoré sa prejaví hneď bez reštartu. Hodnotu si moduly pýtajú funkciou
  `geometry.bar_height()`, nikdy si ju nekopírujú do konštanty (stráži to `tests/test_geometry.py`).
- **Všetky dlaždice** (rohy aj segmenty: hodiny, napájanie, zoznam okien, prompt, správca súborov)
  **sedia na spodnom okraji obrazovky a majú hornú hranu v rovnakej výške.** Medzi nimi je len
  vodorovná medzera 8 px; zaoblené sú len horné rohy segmentov.
- Rohová dlaždica (päta L): **výška = BAR_HEIGHT, šírka ≈ 2 × výška (168 × 84)**, pritlačená k okraju
  obrazovky (bez 12 px odsadenia). Zaoblený je len vnútorný roh; vonkajší je pri okraji obrazovky rovný.
  Päta pri okraji je predpoklad pre časť 3: kmeň L sa opiera o jej hornú hranu.
- Maximalizované okno potom končí hneď nad lištou, žiadny pás navyše.
- **Zatvorená dlaždica nemá text**, len ikonu nad textúrou, ako ostatné položky lišty (rozhodnutie autora
  2026-09-21). Názov (`maps.NAMES`: App Manager, Správca zariadení) je v tooltipe, v popise pre čítačky
  obrazovky a ako malý nadpis v ramene otvoreného popupu, kde je aj **tlačidlo do podrobností**
  (`maps.DETAILS`): App Manager → Inštalácia aplikácií (kým nie je App Manager, vedie na stránku
  `settings://software/install`, ktorá povie, že je plánovaná; potom sa presmeruje na neho),
  Správca zariadení → Podrobnosti (otvorí `latte-devices`). Ikona v dlaždici je väčšia (42 % výšky lišty).

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

Päta je v okne lišty (vrstva TOP), kmeň je v samostatnom okne nad ňou (vrstva OVERLAY,
`maps.TrunkWindow`) a panel s obsahom v ďalšom okne (`maps.MapOverlay`). Sú to rôzne povrchy Waylandu,
jeden widget cez ne nejde. „Rozšírenie, nie duplikát“ sa preto rieši
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
   `(0, BAR_HEIGHT, POPUP_WIDTH, ARM_HEIGHT)`. Preto sa L dá zmeniť (výška lišty, iný monitor) bez
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

**Pravidlo pre každý animovaný povrch: nemá obsahovať nič statické.** Softvérové vykresľovanie
(`GSK_RENDERER=cairo`) pri zmene čo i len malej časti prekreslí celý povrch okna. Namerané: kmeň v okne
popupu (fullscreen, s panelom mriežky aplikácií) stál 21 % jedného jadra, rovnaký kmeň vo vlastnom
okne 820 × 110 stojí 5,5 % (a bez neho popup 0 %). Preto má kmeň vlastné okno a okno popupu zostáva
statické. To isté platí pre živú tapetu (časť 4): tapeta je vlastný povrch, ikony plochy nad ňou majú
byť v inom.

## 4. Textúry a scény: jeden stroj pre lišty aj živú tapetu

Autor chce neskôr aj **živú tapetu namiesto obrázka**. Preto sa textúra nerieši ako vec rohov: je to
všeobecná **scéna**, ktorú kreslí ten, kto ju potrebuje (dnes plátno lišty, neskôr `Desktop`).

Scéna = rozhranie: `render(cr, šírka, výška, čas)`, odporúčané fps, statický snímok. Spôsob vyjadrenia
v nastaveniach je jeden reťazec, aby sa dal pridať nový druh bez zmeny schémy:

| Zápis | Druh | Cena |
|-------|------|------|
| `solid:motív` | obyčajná dlaždica z motívu, **bez textúry** (CSS ako predtým) | nulová |
| `solid:#RRGGBB` | jedna farba ako textúra (predpokladá sa tmavá, text na nej je svetlý); len ručne v súbore | nulová, statická |
| `scene:matrix` | stekajúci kód (zelená klasika alebo akcent motívu) | nízka, kreslené kódom (cairo) |
| `scene:gears` | ozubené prevody, pomalé otáčanie, v paletě motívu | nízka, kreslené kódom |
| `scene:glow` | pomalé svetlo: mäkké farebné škvrny plynúce po dráhach, v paletě motívu (káva, karamel) | nízka, hladké gradienty |
| `file:cesta` | GIF alebo animované WebP od používateľa | podľa súboru (pamäť, nižšie) |

Ďalšie kódované scény sa pridávajú ako jedna trieda; tri vyššie stačia na štart. Kódovaná scéna
nemá vlastný súbor, je ostrá v každom rozlíšení, dá sa zafarbiť motívom a slučka nemá šev.

### Súbory (GIF, WebP) a video

- Prehráva to `latte_common/filescene.py` (`FileScene`, zápis `file:/absolútna/cesta`): GIF, animované
  WebP a obyčajný obrázok (PNG, JPEG… ako nehybná textúra). Snímky dekóduje `GdkPixbuf.PixbufAnimation`
  a dĺžku slučky nevie povedať, preto sa **trvania snímkov čítajú z hlavičiek** (GIF: rozšírenia
  Graphic Control, WebP: bloky ANMF; oneskorenie 0 alebo 1 stotina sa berie ako 100 ms ako v prehliadačoch).
  Súbor sa číta až pri prvom kreslení (`parse` nerobí I/O), snímky sa **vzorkujú v strede pevných
  intervalov** (hranice snímkov v GdkPixbuf sú vrátane) a obraz je čistá funkcia času ako pri kódovaných
  scénach. Obrázok sa zväčší tak, aby vyplnil plátno (cover), vystredí a ustrihne; nie je to strihač, ten
  príde s R6. Animované WebP je **overené na skutočnom súbore** (klip vyrobený z MP4 cez ffmpeg: 40 snímok, prehráva sa);
ak by dekodér animáciu nevedel, ukáže sa prvý snímok a povie sa to.
- **AVI, MP4, MKV sú len vstup strihača** (časť 5), za behu sa neprehrávajú. GStreamer má na tejto VM len
  základné moduly (bez demuxeru AVI a bez dekodéra H.264) a modul GTK pre médiá som nenašiel; prehrávanie
  videa by pridalo závislosť, ktorú relácia nemá, a na softvérovom vykresľovaní aj záťaž.
- **ffmpeg (2026-09-21, na pokyn autora):** nainštalovaný **plný `ffmpeg` z RPM Fusion** (repozitár
  `rpmfusion-free-release` pridaný, `ffmpeg-free` nahradený; späť: `dnf remove rpmfusion-free-release`,
  `dnf swap ffmpeg ffmpeg-free --allowerasing`). Dôvod: Fedorin `ffmpeg-free` dekóduje H.264 len cez
  `libopenh264`, ktorý vie iba Baseline profil; autorovo MP4 je **High profile s B-snímkami** a dalo stovky
  chýb „Error submitting packet to decoder“ (a WebP z neho 45 kB, teda takmer prázdny). Plný ffmpeg ho
  dekóduje čisto (4 s klip za 0,7 s). Kodéry `gif` a `libwebp_anim` sú, `ffmpegthumbnailer` (náhľady
  videí v správcovi súborov) ostal nainštalovaný. Strihač musí aj tak kontrolovať, či ffmpeg je a čo vie
  (`ffmpeg -decoders`), lebo iný stroj nemusí mať RPM Fusion.
- **Rozpočet pamäte** (`filescene.BUDGET_BYTES` = 24 MB na animáciu): rozbalené snímky zaberú
  `snímky × plocha × 4 B`, preto sa držia v **polovičnom rozlíšení plátna** (820 × 194 → 410 × 97,
  159 kB na snímku, cca 150 snímok) a kreslia zväčšené. Vzorkuje sa najviac 10 obr/s; ak sa animácia
  nezmestí, vzorkuje sa redšie (najmenej 4 obr/s, dĺžka sa zachová); ak sa nezmestí ani tak, použije sa len
  jej začiatok a `FileScene.problem` to povie (Nastavenia ukážu červený riadok, lišta ohlási raz na stderr),
  nikdy potichu. Pamäť sa nikdy neprekročí (testy `BudgetTest`). Hlásenia: chýbajúci alebo pokazený súbor,
  príliš veľký (128 MB), adresár, text namiesto obrázka.
- **Načítanie beží vo vlákne** (`FileScene.loading`): dekódovanie všetkých snímkov trvá pri veľkom GIF-e aj
  sekundu (800 × 600, 101 snímok: 1,4 s). Kým nie je hotové, kreslí sa tmavý podklad; výsledok sa odovzdá
  hlavnému vláknu cez `GLib.idle_add` a platí len posledná požiadavka na rozmer plátna (staré snímky ostávajú
  vidieť, kým sa nenačítajú nové). Namerané: najväčšie meškanie časovača hlavnej slučky pri načítaní toho GIF-u
  **998 ms bez vlákna, 46 ms s vláknom**. Bez vlákna by sa lišta pri každom štarte relácie zdržala o toľko,
  koľko trvá prvé vykreslenie dlaždice.
- **Skutočné súbory** (`inspo/*.gif`, pridal autor): 12 až 101 snímok, 0,2 až 4 MB, načítanie 45 až 1409 ms,
  v pamäti 1,1 až 5,2 MB, žiadny nepresiahol rozpočet (101 snímok sa vzorkuje na 34 pri 10 obr/s).
  Obraz sa zväčší na vyplnenie a vystredí: GIF 498 × 278 v plátne 820 × 194 (pomer 4,2 : 1) ukáže len
  stredný pás, preto potrebujeme strihač (výber výrezu).
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

Kde: **Prostredie**, stránka **Lišta a systémové menu** (`main_setting_v2.md`, časť 46), oddiel
„Rohové dlaždice lišty“; vypínač pohybu sa dá pridať aj do **Animácie a efekty** (časť 48). Údaje patria
do domény `appearance` (`~/.config/latteos/appearance.toml`), lebo tá už drží tapetu a lišta ju sleduje.
Názov kľúča smie mať len jednu bodku (`oddiel.kľúč`), preto `bars.left` a `bars.right`, nie
`bars.apps.source`; ľavý a pravý roh sú pomenované podľa polohy, nie podľa aplikácie.

| Kľúč | Význam | Predvolené |
|------|--------|------------|
| `bars.left`, `bars.right` | zdroj textúry rohu: zápis z časti 4 | `scene:matrix`, `scene:gears` |
| `bars.motion` | `always`, `hover` (len pod kurzorom alebo kým je otvorený popup), `off` (statický snímok) | `always` |
| `bars.speed` | rýchlosť pohybu, posuvník 0,25 až 1,5 | 1,0 |
| `bars.dim` | stlmenie textúry pod textom, posuvník 0 až 0,9 | 0,6 |

Výber zdroja má vlastný ovládač (`controls.LPreview`): rozbaľovací zoznam z `scenes.CHOICES` a pod ním
**živý náhľad L** (päta + kmeň, vpravo zrkadlovo), ktorý kreslí rovnaký kód ako lišta a berie
rýchlosť, stlmenie a pohyb z ostatných riadkov stránky, takže ich zmena je hneď vidieť. Zápis mimo
ponuky (napr. `solid:#RRGGBB` z ručne upraveného súboru) sa v zozname ukáže ako „Vlastné“. Chybný zápis
(`scene:zle`) sa nahradí predvoleným a ohlási na stderr lišty (`latte-shell: bars.left: neznámy zdroj ...`).
Výber vlastného súboru (`file:`) a vlastnej farby príde s R5.

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
| R3 ✅ | maska L, pohľad v kmeni popupu, animácia otvárania | snímky v štyroch fázach; fázová zhoda päty a kmeňa |
| R4 ✅ | kľúče `bars.*`, `scene:gears`, `scene:glow`, výber v Nastaveniach s náhľadom | test schémy a modelu, načítanie poškodeného zápisu |
| R5 ✅ | `file:` (GIF, WebP) | skúšobný súbor, rozpočet pamäte |
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

**Výška lišty ako nastavenie (2026-09-21).** Lišta číta `bar.height` pri štarte a sleduje súbor
(`settings.watch`); pri zmene prepočíta rezervované miesto (`set_exclusive_zone`), rohové dlaždice, ikonu
v nich (32 px pri vysokej lište, 20 px pri 48), plátno textúry a odsadenie ikon plochy a zatvorí
otvorené popupy (majú starú polohu). Segmenty už nemajú pevnú výšku, vyplnia výšku lišty. Maximalizované
okno labwc prepočíta samo. Namerané v izolovanom labwc pri zmenách 84 → 60 → 56 → 104 → 84 (a pri 48, 44,
40 priamo): povrch lišty aj koniec okna sedia s nastavenou výškou. Dolná hranica 48: obsah lišty (hodiny,
prompt) si pýta aspoň 43 px, pri 40 nastavených by povrch mal 43. Horná 96: pri 104 sa na obrazovke
1280 px široko zdrobní zoznam okien, lebo rohy sú 2 × výška široké. Nastavenie je na stránke Lišta ako
posuvník (nový `control = "slider"`), zápis najviac 10 × za sekundu.

**R5, stav (2026-09-21).** Zdroj `file:` (časť 4) v lište aj v Nastaveniach. Výber zdroja má okrem
zoznamu tlačidlo „Súbor…“ (`Gtk.FileDialog`, filter GIF, WebP, PNG, JPEG) a tlačidlo farby (`solid:#RRGGBB`,
tmavá, lebo text na nej je svetlý); zápis mimo ponuky sa v zozname ukáže ako „Súbor: a.gif“ alebo
„Farba: #RRGGBB“ (`scenes.custom_label`), pod náhľadom je stav (`40 snímok, 4.0 s, 6.1 MB`, alebo červený
dôvod, prečo súbor nejde). Lišta ohlási problém scény raz (`BarTexture.report`, nie pri každom snímku).
Overené v izolovanom labwc so zápisníkom vlastných GIF (`tests/animfiles.py` je malý zapisovač GIF bez
závislostí, kvôli testom a skúškam): GIF plynie súvisle cez pätu a kmeň, chýbajúci súbor ohlási chybu a
dlaždica je tmavá, späť na matrix a prevody za behu. Záťaž (jedno jadro procesu lišty): GIF vľavo 1,8 %, s
otvoreným popupom 2,8 % (kopírujú sa už hotové snímky, je to lacnejšie než kódované scény).

**Chyba z živej relácie: výber zdroja zavesil Nastavenia (2026-09-21).** Autor zvolil v zozname „Jedna farba“;
lišta sa prepla, ale okno Nastavení zamrzlo (proces 98 % jadra) a po minimalizácii ostal zoznam visieť na
ploche. Príčina: nekonečná slučka `commit` → `refresh` → `set_widget` (vymenil model zoznamu) → oznámenie
o výbere, ktoré GTK doručí až keď už neplatí ochrana `updating` → `commit` → … (9000 volaní za pár sekúnd).
Predtým som ovládač skúšal len zápisom cez Store a náhľad cez kód, nie skutočným klikom do zoznamu, preto
mi to uniklo. Opravené: obsluha výberu je idempotentná (`scenes.pick_source` nezapíše nič, ak je položka
už aktuálna hodnota) a model zoznamu sa mení len keď sa zmenia názvy (`scenes.source_list`), náhľad sa
prekreslí len pri zmene zdroja. Zopakované skutočným klikaním (`wlrctl`) v izolovanom labwc: pred opravou
98 % jadra a visiaci zoznam, po oprave štyri výbery za sebou bez záťaže, správne zapísané hodnoty. Testy
`SourceListTest` (vrátane simulácie cyklu zápis → obnova → oznámenie, ktorá sa musí zastaviť po jednom
zápise). Pravidlo pre ovládače Nastavení: obsluha signálu, ktorý môže vyvolať aj program, nesmie zapisovať,
ak sa hodnota nezmenila. Súvisiaca úprava: náhľad L sa hýbe len pod kurzorom a 4 s po zmene nastavenia
(dva stále bežiace náhľady stáli 35 % jadra, nečinný náhľad 0 %).

**Názov až v popupe (2026-09-21).** `Bar.corner_tile(kind, right)` už nemá popis; `fill_tile` skladá ikonu
nad textúrou. V rameni pribudli `maps.name_label` a `maps.details_button` (štýl `.arm-link`, veľký cieľ pre
prst), `MapOverlay` má `on_details`, lišta `launch_details(kind)`. Overené v izolovanom labwc skutočným
klikom (`wlrctl`): kliky spustili očakávané príkazy (`latte_settings/app.py software/install`,
`latte_devices/app.py`) a zatvorili popup, tri behy po sebe.

**R4, stav (2026-09-21).** Nastavenia `bars.*` (tabuľka v časti 5), scény `gears` (rozloženie z pevného
semienka rastie z päty; uhly sú funkcia času, zub vždy zapadne do medzery a otáča sa opačne a v pomere
zubov; pravý roh je zrkadlo) a `glow` (šesť pomalých škvŕn po dráhach s periódou 40 až 120 s), farby scén
z motívu (`scenes.palette_from_colors`), tmavý prechod pod textom **zapečený do plátna**
(`scenes.dim_overlay`, parameter `bars.dim`; odpadli dve CSS vrstvy a prechod má nastaviteľnú mieru),
režimy pohybu, výber s náhľadom v Nastaveniach. Lišta drží `bar_texture.Config` a plátna stavia znova len
keď sa zmenila (zdroje, rýchlosť, stlmenie, pohyb, farby motívu), nie pri každej zmene súboru; obsah
dlaždíc sa vymení za behu (`Bar.fill_tiles`), otvorené popupy sa zatvoria.
Pravá dlaždica má predvolene prevody (predtým obyčajná).
Namerané v izolovanom labwc (jedno jadro procesu lišty, 10 obr/s): matica vľavo a prevody vpravo 2,9 %,
s otvoreným popupom s maticou 7,8 % a s prevodmi 12,2 % (prevody sú najdrahšia scéna: 5 ms na celé plátno),
svetlo na oboch stranách 2,5 %, obyčajné dlaždice 0 %. Ďalej: zmeny
zdrojov, hover (skutočný kurzor cez `wlrctl`), vypnutý pohyb, chybný zápis v súbore. Meranie odhalilo
chybu: `Gears` v pravom rohu nechal zrkadlenie platné a tmavý prechod sa potom kreslil zrkadlovo (jas
pravej päty sa pri stlmení 0 / 0,6 / 0,9 nemenil: 49,5 / 48,6 / 49,3, po oprave 49,5 / 17,4 / 12,2). Stráži
to `SceneSideEffectsTest` (scéna nesmie zmeniť transformáciu ani orezanie kontextu) a testy stlmenia pre
pravý roh.

**R3, stav (2026-09-21).** Popup má tri časti: statické okno s panelom a zachytávaním kliknutí mimo
(`MapOverlay`, fullscreen), okno kmeňa (`TrunkWindow`, 820 × 110 nad lištou) a pätu v lište. Kmeň je
rameno na celú šírku popupu (`POPUP_WIDTH = 820`, v ňom sa vojdú dva stĺpce skupín zariadení bez
posuvníka), pozadie kreslí textúra (ak ju dlaždica má) a nad ňou tmavý prechod: slabší pri päte, silnejší
pod textom. Text je odsadený od päty (`CORNER_WIDTH + 24`), nie o pevný „stĺpec“ ako predtým; nepoužitý
`column_box` a `COLUMN` sú preč. Otváranie (`reveal.py`): kmeň rastie z hornej hrany päty (výška aj šírka
naraz, 380 ms, prvé tri štvrtiny), panel sa objaví od polovice; zatváranie je opačne (300 ms), popup sa
pre lištu považuje za zatvorený hneď a okná zaniknú po animácii; prepnutie smeru uprostred pokračuje
z aktuálnej hodnoty. So `gtk-enable-animations = false` je všetko okamžité. Kým je popup otvorený,
dlaždica má triedu `open` (bez hornej čiary), aby päta a kmeň nadväzovali bez švu.
Overené v izolovanom labwc: fázy odhaľovania (snímky pri 15, 40 a 65 %), pravý roh (Zdroje), zatváranie
(okná zaniknú, dlaždica stratí triedu), vypnuté animácie a klikanie cez `wlrctl` (klik do kmeňa popup
nezatvorí, klik mimo zatvorí). Záťaž s otvoreným popupom: 5,5 % jedného jadra (pred rozdelením na okná
21 %). Päta v lište a kmeň sú dva povrchy, ktoré sa prekresľujú každý vo svojej snímke, takže sa
môžu rozísť najviac o jednu snímku (0,1 s); na hranici to nie je vidieť.
Pravý kmeň (Zdroje) je zatiaľ bez textúry, príde s `gears` v R4.

Farba a premenovanie vľavo (časť 6) sú nezávislé od rohov a sú malé; poradie vnútri: `favorites`
(entries, moved, color) a `is_system_folder` s testami, potom `rename_path`, nakoniec menu.
Heidelberg (časť 7) je samostatná aplikácia; s lištou súvisí len cez App Manager, správcu súborov
a okná.

## 9. Otvorené otázky

1. **Hranica „systémový priečinok“** (časť 6): domov, Kôš, korene zväzkov, `SYSTEM_ENTRIES`, `~/Desktop`
   a používateľské priečinky (Dokumenty, Stiahnuté…). *Potvrdené autorom.*
2. **Veľkosť päty**: 168 × 84 je odhad. Rozhodne živý nákres.
3. **Farba matrixu**: zelená klasika predvolene, akcent motívu ako voľba. Súhlasíš?
4. **Prevody a „pomalé svetlo“** ako kódované scény: chceš ich, alebo iné (napr. dážď na skle podľa
   tapiet)? Dajú sa pridať kedykoľvek, tri stačia na štart.
5. **Čo ďalej** po R3: R4 (nastavenia a ďalšie scény), alebo najprv malý celok z časti 6 (farba a
   premenovanie vľavo)? (R1 až R3 sa robili v poradí podľa autora.)
