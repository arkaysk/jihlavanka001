# Nastavenia systému LatteOS

Návrh informačnej architektúry a kompletného zoznamu stránok pre aplikáciu Nastavenia.

Stav: návrh pre etapu 8.10  
Aktualizované: 2026-09-20

## Krátke rozhodnutie

LatteOS má mať jedno hlavné **Nastavenie systému**, ktoré je domovom pre všetky používateľské voľby a vyhľadávanie. Nemá však preberať všetku funkcionalitu ostatných manažérov.

- **Nastavenia** vysvetlia voľbu, zobrazia jej stav a nastavia bežnú konfiguráciu.
- **App Manager** vlastní aplikácie, balíky, Flatpak, repozitáre, aktualizácie aplikácií a oprávnenia aplikácií.
- **Správca zdrojov** vlastní živé zariadenia, pripojenie a diagnostiku hardvéru.
- **Správca účtov** vlastní používateľov, heslá a autentizačné metódy.
- **latte-updated** vlastní systémové aktualizácie, reštart do offline aktualizácie a návrat po zlyhaní.

Pre používateľa to má vyzerať ako jedno miesto. Technicky má zostať vlastníctvo oddelené. Klik z Nastavení môže otvoriť správneho manažéra na konkrétnej karte alebo s konkrétnou akciou.

### Odpoveď na otázku o aktualizáciách a hardvéri

**Aktualizácie systému nech sú viditeľné v Nastaveniach, ale vykonáva ich `latte-updated`.** Windows 11 to robí podobne: používateľ ich hľadá v Nastaveniach, hoci aktualizačný servis je samostatná vrstva. App Manager môže na svojej stránke zobrazovať aktualizácie aplikácií, ale nemá byť vlastníkom aktualizácie celého operačného systému.

**Hardvér a sieť nech zostanú v Správcovi zdrojov.** Do Nastavení patria ich stabilné používateľské voľby, napríklad rozlíšenie, predvolený zvukový výstup, Wi-Fi profily alebo automatické pripájanie. Živý zoznam zariadení, pripájanie diskov, diagnostika ovládača, skenovanie siete a servisné operácie patria do Správcu zdrojov.

Ideálny vzor je:

> Nastavenie obsahuje voľbu alebo zhrnutie + tlačidlo **Otvoriť v Správcovi zdrojov**.

Tým sa nestratia funkcie v druhom okne, ale ani nevzniknú dve konkurenčné miesta, ktoré menia tú istú hodnotu.

## Päť oblastí a jedno hlavné menu

Tvoja nová formulácia je presnejšia než delenie podľa jednotlivých aplikácií. Základ môžu tvoriť tri technické domény, ku ktorým LatteOS pridá dve prierezové oblasti prostredia:

1. **Softvér** - operačný systém, služby, aplikácie, Flatpak, repozitáre, aktualizácie, oprávnenia a predvolené aplikácie.
2. **Dáta** - používateľské súbory, úložisko, zálohy, obnova, synchronizácia a obsah vytvorený aplikáciami.
3. **Hardvér** - displeje, zvuk, sieťové adaptéry, Bluetooth, disky, tlačiarne, vstupné zariadenia a napájanie.
4. **Prihlásenie** - používatelia, heslá, spôsob prihlasovania, uzamknutie a správanie prihlasovacej obrazovky.
5. **Vzhľad** - motív, farby, písmo, pozadie, okná, lišta a vizuálne správanie celého prostredia.

**Nastavenia systému nie sú šiesta doména.** Sú to spoločné rozhranie nad týmito piatimi oblasťami. V hlavnom menu preto môžu byť zhromaždené položky zo Softvéru, Dát, Hardvéru, Prihlásenia aj Vzhľadu, ale každá položka musí mať svojho hlavného vlastníka.

### Hlavní vlastníci oblastí

| Oblasť | Hlavný zdroj pravdy | Špecializovaný vstup |
|---|---|---|
| Softvér | App Manager + `latte-updated` | App Manager |
| Dáta | Správca súborov, úložísk a záloh | Správca súborov / zálohovací nástroj |
| Hardvér | Správca zdrojov | Správca zdrojov |
| Prihlásenie | `latte-greeter` + správca účtov a relácie | prihlasovacia obrazovka / Správca účtov |
| Vzhľad | `latte-appearance` | Nastavenia vzhľadu |

Prihlásenie a Vzhľad nie sú iba podkategórie Softvéru. Používateľ ich vníma ako základnú identitu a tvár systému, preto si zaslúžia vlastné výrazné vstupy.

### Návrh rozhrania

Hlavné Nastavenia by nemali pôsobiť ako dlhý ľavý zoznam Windows nastavení. V úvodnej obrazovke môže byť päť veľkých, vizuálne odlišných oblastí s jasnými hranicami a krátkym stavom:

- **Softvér** - aplikácie, aktualizácie a systémové komponenty;
- **Dáta** - súbory, miesto, zálohy a obnova;
- **Hardvér** - zariadenia, sieť, zvuk, obrazovky a napájanie;
- **Prihlásenie** - účet, heslo, uzamknutie a vstup do relácie;
- **Vzhľad** - motív, farby, písmo, pozadie a okná.

Každá oblasť by mala mať vlastný vizuálny jazyk, ale zostať súčasťou jedného LatteOS dizajnu. Rozdiel nemá byť iba vo farbe ikony: oblasť môže mať vlastnú hlavičku, súhrnný stav, podnavigáciu a návrat späť na mapu oblastí. Tak používateľ okamžite chápe, či mení aplikácie, súborové dáta, fyzické zariadenie, prihlasovanie alebo vzhľad.

### Vrstvený bočný panel

Najlepšie to môže fungovať podobne ako bočný panel v Správcovi súborov, ale s jednou ďalšou vrstvou navigácie. Bočný panel Nastavení bude stále obsahovať všetky položky, rozdelené do piatich veľkých skupín:

```text
SOFTVÉR       [ikona App Managera]
  Objavovať
  Aktualizácie
  Nainštalované aplikácie
  Nastavenia aplikácií

DÁTA          [ikona súborov]
HARDVÉR       [ikona zariadení]
PRIHLÁSENIE   [ikona používateľa]
VZHĽAD        [ikona motívu]
```

Každá skupina je v skutočnosti **prekryvná skupina kariet**:

- názov skupiny, logo a jej hlavné položky sú vždy rozpoznateľné;
- aktívna skupina sa vysunie do popredia, dostane plnú plochu a odkryje svoje karty;
- neaktívne skupiny sa zasunú pod ňu ako vrstvy, ale ich názvy a ikony zostanú viditeľné;
- kliknutie na inú skupinu ju vysunie dopredu a pôvodná skupina sa prekryje;
- aktívna položka v skupine používa rovnaký princíp zvýraznenia ako aktívny zväzok v Správcovi súborov;
- pri úzkom okne sa skupiny nezmiznú do nečitateľného hamburger menu: zmenšia sa na ikonu, názov a stavový bod.

To dáva používateľovi naraz dve informácie: **v ktorej oblasti sa nachádza** a **na ktorej konkrétnej karte**. Nie je to obyčajný dlhý zoznam, ale mapa s fyzickou hĺbkou. Prechod z App Managera na Vzhľad bude vizuálne jasný, pretože vrstva App Managera ustúpi a vrstva Vzhľadu sa dostane pred ňu.

Príklad:

```text
VZHĽAD       [predná vrstva]
  Motív              <- aktívna karta
  Farby
  Písmo
  Pozadie

SOFTVÉR      [zasunutá vrstva]
DÁTA         [zasunutá vrstva]
HARDVÉR      [zasunutá vrstva]
PRIHLÁSENIE  [zasunutá vrstva]
```

Po kliknutí na **Softvér** sa iba zmení poradie vrstiev a zobrazí sa jeho skupina:

```text
SOFTVÉR      [predná vrstva]
  Objavovať
  Aktualizácie
  Nainštalované aplikácie
  Nastavenia aplikácií  <- aktívna karta

VZHĽAD       [zasunutá vrstva]
DÁTA         [zasunutá vrstva]
HARDVÉR      [zasunutá vrstva]
PRIHLÁSENIE  [zasunutá vrstva]
```

Toto je vhodnejšie než samostatné okná pre každú skupinu. Používateľ má pocit jedného systému, ale zároveň vidí hranicu medzi oblasťami. Stavové informácie môžu byť priamo na vrstve, napríklad bod pri Softvéri znamená dostupné aktualizácie a bod pri Hardvéri znamená problém so zariadením.

Vizuálne má panel nadviazať na `files-sidebar`, `section-title`, `navigation-sidebar` a zvýraznenie `row:selected` zo Správcu súborov. Nové sú iba tri pravidlá: skupina má vlastnú hlavičku, aktívna skupina je nad ostatnými a prechod medzi skupinami má krátku, pokojne animovanú zmenu vrstvy. Obsah stránky nemá skákať ani meniť šírku.

#### Dôležité pravidlo pre prekrývanie

Prekrytie má byť vizuálna metafora, nie skutočné zakrytie ovládacích prvkov. Neaktívne skupiny musia zostať klikateľné, mať čitateľný názov a byť dostupné klávesnicou. Aktívnu skupinu treba označiť aj textom, ikonou a stavom fokusu, nielen farbou alebo hĺbkou.

Praktická navigácia môže mať tri úrovne:

1. **Mapa oblastí** - päť hlavných vstupov a globálne vyhľadávanie.
2. **Domov oblasti** - súhrn stavu a jej hlavné podstránky.
3. **Konkrétna funkcia** - vlastná stránka alebo otvorenie príslušného manažéra na konkrétnej karte.

Napríklad:

`Nastavenia > Softvér > Aktualizácie > App Manager > Aktualizácie`

alebo:

`Nastavenia > Vzhľad > Motív > latte-appearance`

V oboch prípadoch používateľ ostáva v jednom navigačnom modeli, aj keď samotnú operáciu vykonáva špecializovaný komponent.

### Prihlásenie ako samostatná oblasť

Oblasť **Prihlásenie** má zahŕňať iba veci, ktoré používateľ očakáva medzi účtom a vstupom do systému:

- aktuálny používateľ a prepínanie používateľov;
- zmena hesla a bezpečnostných metód;
- automatické prihlásenie;
- uzamknutie po nečinnosti;
- správanie po štarte a po odhlásení;
- obrazovka prihlasovania a jej povolené voľby;
- relácie, prístupnosť prihlasovania a napájacie voľby na greeteri.

Účet a heslo spravuje Správca účtov, prihlasovaciu obrazovku `latte-greeter` a stav relácie správca relácie. Hlavné Nastavenia zobrazia všetko na jednom mieste, ale nevytvoria tretí systém účtov.

### Vzhľad ako samostatná oblasť

Oblasť **Vzhľad** má byť výraznejšia než bežná stránka v zozname. Môže obsahovať živý náhľad prostredia a pod ním podstránky:

- motív a farebný režim;
- farba zvýraznenia a kontrast;
- písmo a mierka;
- pozadie a prihlasovacia tapeta;
- okná, rohy a tlačidlá;
- lišta, pracovné plochy a oznámenia;
- priehľadnosť, animácie a prístupnosť vzhľadu.

Zdrojom pravdy zostáva `appearance.toml` a služba `latte-appearance`. Prihlasovacia obrazovka môže vzhľad používať, ale nastavenia prihlasovania a nastavenia motívu sa nemajú zliať do jedného vlastníka. Vzhľad je spoločný vizuálny systém, nie lokálna voľba jednej aplikácie.

### Konkrétny model App Managera

Ak sa App Manager otvára z ľavého dolného rohu a má napríklad tieto karty:

- **Objavovať alebo Inštalovať** - nové aplikácie, Flatpak a repozitáre;
- **Aktualizácie** - aktualizácie aplikácií a podľa návrhu aj aktualizácie systému;
- **Nastavenia aplikácií** - predvolené aplikácie, oprávnenia, automatické spúšťanie a kompatibilita;

potom tieto funkcie **majú byť dostupné aj v hlavnom Nastavení systému**. Nie však ako skopírované druhé obrazovky.

Odporúčaný spôsob:

| V hlavnom Nastavení | Po otvorení | Vlastník obrazovky |
|---|---|---|
| Softvér > Aplikácie | App Manager > Nainštalované | App Manager |
| Softvér > Inštalácia aplikácií | App Manager > Objavovať | App Manager |
| Softvér > Aktualizácie | App Manager > Aktualizácie, s oddeleným blokom systému | App Manager + `latte-updated` |
| Softvér > Nastavenia aplikácií | App Manager > Nastavenia aplikácií | App Manager |
| Softvér > Repozitáre | App Manager > Repozitáre | App Manager |
| Dáta > Úložisko a zálohy | Správca súborov alebo zálohovací nástroj | dátový manažér |
| Hardvér > Zariadenia | Správca zdrojov | Správca zdrojov |

To znamená, že používateľ môže začať na dvoch miestach:

- klikne na **App Manager** v systémovom menu a používa jeho karty;
- otvorí **Nastavenia systému**, vyberie Softvér a dostane sa na rovnakú kartu App Managera.

Obe cesty majú byť rovnocenné. Hlavné Nastavenia nemajú zobrazovať iba textový odkaz, ak sa dá otvoriť konkrétna karta. Ideálne je odovzdať cieľ, napríklad `app-manager://updates` alebo `app-manager://settings/default-apps`, aby sa otvorila správna stránka.

### Aktualizácie v jednej karte

Aktualizácie aplikácií a systému môžu byť v App Manageri spolu, pretože používateľ ich vníma ako jednu úlohu: **„Je môj počítač aktuálny?“** Vnútri však musia zostať rozlíšené:

- **Aplikácie a Flatpak** spracuje App Manager.
- **Základný systém a LatteOS** spracuje `latte-updated`.
- **Firmware zariadení** spracuje Správca zdrojov alebo samostatný firmware backend.

App Manager môže mať jednu kartu **Aktualizácie** s tromi oddielmi. Hlavné Nastavenia na ňu vedú z položky **Softvér > Aktualizácie**. Tým sa dosiahne jednotné miesto pre používateľa bez toho, aby App Manager dostal nebezpečne široké vlastníctvo.

### Kam patria dáta

„Dáta“ nie sú len ďalšia stránka v Nastaveniach. Sú to objekty, ktoré používateľ vytvára alebo uchováva:

- dokumenty, fotografie, videá a osobné priečinky;
- miesto na disku, pripojené zväzky a externé médiá;
- zálohy, synchronizované kópie a obnova;
- dáta aplikácií a cache;
- história, stav okien a dočasné súbory.

Nastavenia majú zobrazovať ich stav a bezpečné voľby, napríklad cieľ zálohy alebo predvolený priečinok. Samotné prehliadanie a presúvanie dát patrí Správcovi súborov, pripojenie diskov Správcovi zdrojov a zálohovanie zálohovaciemu nástroju.

### Praktické hlavné menu

Najčistejší model pre systémové menu je:

- **Nastavenia systému** - všetkých päť oblastí v jednom vyhľadateľnom katalógu;
- **App Manager** - rýchly vstup do Softvéru: inštalácia, aktualizácie a nastavenia aplikácií;
- **Správca zdrojov** - rýchly vstup do Hardvéru: zariadenia, pripojenia a diagnostika;
- **Správca súborov** - rýchly vstup do Dát: súbory, priečinky a externé médiá.

Položka v hlavnom Nastavení môže byť teda dostupná aj v špecializovanom manažéri. Platí zásada: **viac vstupov je v poriadku, viac vlastníkov tej istej hodnoty nie.**

## Čo ukazuje porovnanie

### Windows 11

Windows 11 používa široké hlavné kategórie: **Systém**, **Bluetooth a zariadenia**, **Sieť a internet**, **Prispôsobenie**, **Aplikácie**, **Účty**, **Čas a jazyk**, **Hranie hier**, **Prístupnosť**, **Súkromie a zabezpečenie** a **Windows Update**.

Dôležité ponaučenie pre LatteOS:

- Aktualizácie sú pre používateľa súčasťou Nastavení.
- Hardvér a sieť sú tiež súčasťou Nastavení, ale vo vlastných kategóriách.
- Aplikácie majú vlastnú kategóriu, nie sú roztrúsené v Systéme.
- Účty sú samostatná hlavná oblasť.
- Systémové informácie, obnovenie a riešenie problémov patria pod Systém.

### KDE Plasma

KDE System Settings má tri prirodzené vrstvy: vzhľad a správanie pracovnej plochy, hardvér a systémovú správu. Zahŕňa napríklad vzhľad, pracovný priestor, okná, klávesové skratky, displeje, zvuk, napájanie, sieť, Bluetooth, tlačiarne, používateľov, lokalizáciu a aktualizácie.

Dôležité ponaučenie:

- Konfiguračné moduly môžu byť v jednom katalógu, ale každý má jasného vlastníka.
- Pokročilé moduly nemajú byť preplnené do jednej stránky Systém.
- Hardware a desktop customization sú odlišné oblasti.

### GNOME a Fedora Workstation

GNOME Settings dáva používateľovi bežné voľby ako Wi-Fi, Bluetooth, pozadie, vzhľad, oznámenia, aplikácie, súkromie, zvuk, napájanie, obrazovky, myš, klávesnicu, tlačiarne, používateľov, dátum a čas a prístupnosť. Hardvér a diagnostické témy sú prirodzene samostatná časť.

Fedora Workstation navyše ukazuje, že aktualizácie, distribúcia balíkov a upgrade vydania môžu mať samostatné služby, hoci ich používateľ spúšťa z grafického nástroja. LatteOS má rovnakú hranicu zachovať.

## Kanonický strom Nastavení

Každá položka je uvedená iba raz. Stav alebo akcia sa môže objaviť aj v inom manažéri, ale v tomto strome má jedno hlavné miesto. Nadpis v zátvorke je vlastník, ktorý stránku skutočne implementuje.

### 1. Softvér

- **Všeobecné systémové nastavenia** (LatteOS system backend)
  - názov počítača a zdieľanie zariadenia
  - predvolené aplikácie a akcie pre typy obsahu
  - jazyk, región, časové pásmo a formáty
  - klávesové skratky a vstupné metódy
- **O LatteOS a softvérová diagnostika** (App Manager + `latte-diagd`)
  - verzia LatteOS, jadra, App Managera a nainštalovaných komponentov
  - licencie, zdroje balíkov a schopnosti softvérového prostredia
  - zlyhané aplikácie, služby a softvérové hlásenia
  - export logov a odoslanie softvérového hlásenia
- **App Manager** (App Manager)
  - Objavovať a inštalovať aplikácie
  - Nainštalované aplikácie, odinštalovanie a veľkosť
  - Flatpak, repozitáre a zdroje aplikácií
  - Nastavenia aplikácií: predvolené aplikácie, automatické spúšťanie a kompatibilita
  - Oprávnenia aplikácií: súbory, sieť, kamera, mikrofón a oznámenia
- **Aktualizácie** (App Manager + `latte-updated`)
  - aplikácie a Flatpak
  - systém LatteOS a balíky distribúcie
  - firmware zariadení, ak je dostupný
  - automatické aktualizácie, reštart, história a návrat po zlyhaní
- **Systémové služby a relácia** (správca relácie)
  - služby spúšťané po prihlásení
  - aplikácie pri prihlásení, rozšírenia a služby bežiace na pozadí
  - správanie po štarte, odhlásení, uspaní a reštarte
  - stav a diagnostika zlyhaných služieb
- **Súkromie a bezpečnosť** (portál + bezpečnostný backend)
  - poloha, kamera, mikrofón, súbory a oznámenia na uzamknutej obrazovke
  - diagnostické údaje a hlásenia
  - firewall, šifrovanie disku a bezpečné spustenie

### 2. Dáta

- **Súbory a priečinky** (Správca súborov)
  - osobné priečinky a predvolené umiestnenia
  - predvolené aplikácie pre typy súborov
  - kôš a dočasné súbory
- **Úložisko a zväzky** (Správca zdrojov + Správca súborov)
  - využitie miesta podľa kategórií
  - pripojené a externé zväzky
  - bezpečné odpojenie a formátovanie cez Správcu zdrojov
- **Zálohovanie a obnova** (zálohovací nástroj)
  - čo sa zálohuje, cieľ a plán
  - posledná úspešná záloha
  - obnova súborov
  - obnova používateľských nastavení a systému, ak ju platforma podporuje
- **Synchronizácia a dáta aplikácií** (príslušný dátový manažér)
  - online účty, synchronizované priečinky a stav
  - veľkosť cache a dát aplikácií

### 3. Hardvér

- **Obrazovky** (Správca zdrojov / display backend)
  - rozlíšenie, orientácia, mierka a obnovovacia frekvencia
  - hlavná obrazovka a usporiadanie monitorov
  - nočné svetlo a správanie po pripojení displeja
- **Zvuk** (PipeWire audio manager)
  - výstup, vstup, hlasitosť a citlivosť mikrofónu
  - predvolené zariadenie a systémové zvuky
  - živý zoznam zariadení a aplikácií používajúcich zvuk
- **Sieť** (NetworkManager / Správca zdrojov)
  - Wi-Fi, káblová sieť, VPN a hotspot
  - uložené siete, automatické pripájanie a merané pripojenie
  - IPv4/IPv6, DNS a proxy
  - diagnostika rozhrania, DNS a dostupnosti internetu
- **Bluetooth a periférie** (BlueZ / Správca zdrojov)
  - párovanie a automatické pripájanie
  - klávesnica, myš, touchpad, gamepady a USB
  - tlačiarne a skenery
  - kamery a mikrofóny
- **Úložné zariadenia** (udisks2 / Správca zdrojov)
  - detekcia, pripojenie, odpojenie a stav diskov
  - optické médiá, USB a čítačky kariet
- **Napájanie** (power backend)
  - stav batérie a napájanie zo siete
  - obrazovka, uspatie a správanie pri zatvorení veka
  - úsporný, vyvážený a výkonný režim
  - zdravie batérie, nabíjanie a štatistika spotreby
- **Tlač a skenovanie** (CUPS / Správca zdrojov)
  - predvolená tlačiareň, front a základné predvoľby
- **Diagnostika zariadení** (Správca zdrojov)
  - model, výrobca, ovládače a stav zariadení
  - chyby displeja, zvuku, siete, Bluetooth, diskov a periférií
  - testy zariadení a otvorenie podrobností v Správcovi zdrojov

### 4. Prihlásenie

- **Účet a používatelia** (Správca účtov)
  - aktuálny účet, meno a obrázok
  - ďalší používatelia a typ účtu
  - online účty a synchronizácia identity
- **Heslo a bezpečnostné metódy** (Správca účtov / polkit)
  - zmena hesla, PIN, biometria a hardvérový kľúč
- **Prihlasovanie a uzamknutie** (`latte-greeter`)
  - automatické prihlásenie
  - správanie prihlasovacej obrazovky
  - uzamknutie po nečinnosti
  - prístupnosť prihlasovania a napájacie voľby na greeteri

### 5. Vzhľad

- **Motív a farby** (`latte-appearance`)
  - svetlý/tmavý režim, akcent, kontrast a priehľadnosť
- **Písmo a mierka** (`latte-appearance`)
  - rodina písma, veľkosť textu a mierka prostredia
- **Pozadie** (`latte-appearance` + Správca súborov)
  - tapeta plochy, prispôsobenie a prihlasovacie pozadie
- **Okná a pracovná plocha** (`latte-appearance` + compositor)
  - rohy, záhlavie, tlačidlá, pracovné plochy a správanie okien
- **Lišta, prompt a oznámenia** (`latte-shell`)
  - obsah lišty, hodiny, prompt, oznámenia a Nerušiť
  - rýchle nastavenia a viditeľnosť položiek v systémovom menu
- **Pracovná plocha a okná** (`latte-appearance` + compositor)
  - virtuálne pracovné plochy, rohy, záhlavie, tlačidlá a správanie okien
  - pracovný priestor, automatické skrývanie panelov a uvítacie správanie
- **Kontinuita a zdieľanie** (systémové portály)
  - zdieľanie obrazovky, súborov a zariadení
  - prenos schránky a nadväzujúce funkcie medzi zariadeniami
- **Prístupnosť prostredia** (systém + `latte-appearance`)
  - čítačka obrazovky, zväčšenie, veľký text a kurzor
  - farebné filtre, vysoký kontrast a obmedzenie animácií
  - klávesy jedným prstom, pomalé klávesy, titulky a vizuálne upozornenia

## Pravidlá vlastníctva

Diagnostika sa nerozhoduje podľa toho, kde sa zobrazí, ale podľa toho, čo diagnostikuje:

- **Softvérová diagnostika**: verzia LatteOS, balíky, aplikácie, služby a ich logy -> App Manager alebo `latte-diagd`.
- **Hardvérová diagnostika**: zariadenia, ovládače, disky, sieť, zvuk, obrazovky a periférie -> Správca zdrojov.
- **Dátová diagnostika**: poškodené súbory, miesto, zálohy a obnova -> Správca súborov alebo zálohovací nástroj.
- **Celkový prehľad** môže tieto výsledky spojiť na jednej stránke, ale každá karta musí viesť k príslušnému vlastníkovi.

| Funkcia | Miesto v Nastaveniach | Skutočný vlastník |
|---|---|---|
| Zmena rozlíšenia | Systém > Obrazovka | Správca zdrojov / display backend |
| Zoznam monitorov a diagnostika | Hardvér > Diagnostika zariadení | Správca zdrojov |
| Hlasitosť a predvolený výstup | Systém > Zvuk | audio manager / PipeWire |
| Pripojenie Wi-Fi | Sieť > Wi-Fi | Správca zdrojov / NetworkManager |
| Párovanie Bluetooth | Zariadenia > Bluetooth | Správca zdrojov / BlueZ |
| Pripojenie a formátovanie disku | Úložisko | Správca zdrojov / udisks2 |
| Inštalácia aplikácie | Aplikácie | App Manager |
| Aktualizácia Flatpaku | Softvér > Aktualizácie | App Manager |
| Aktualizácia Fedora/LatteOS | Softvér > Aktualizácie | `latte-updated` |
| Pridanie používateľa | Účty | Správca účtov / polkit |
| Zmena farieb a motívu | Vzhľad > Motív a farby | `latte-appearance` |
| Oprávnenia aplikácií | Softvér > Súkromie a bezpečnosť | App Manager + portál |
| Firewall | Softvér > Súkromie a bezpečnosť | bezpečnostný backend |

Pravidlo: jedna hodnota má mať jedného vlastníka a jedno miesto, ktoré ju zapisuje. Ostatné obrazovky môžu zobrazovať stav alebo ponúknuť odkaz, ale nemajú vytvoriť druhý parser a druhý zápis.

## Ako majú fungovať odkazy na manažéry

Každá prepojená stránka má mať tri časti:

1. stručný bežný ovládací prvok, ak je voľba bezpečná a stabilná;
2. aktuálny stav, napríklad „Wi-Fi pripojená“, „2 aktualizácie“ alebo „disk pripojený“;
3. tlačidlo s jednoznačnou akciou, napríklad **Spravovať zariadenia**, **Otvoriť App Manager** alebo **Zobraziť diagnostiku**.

Odkaz má odovzdať cieľovú stránku a podľa možnosti aj identifikátor objektu. Napríklad z Obrazovky sa má otvoriť konkrétny monitor, nie iba domovská stránka Správcu zdrojov.

## Vzhľad kontajnerových a cudzích aplikácií

LatteOS môže cudzej aplikácii ponúknuť spoločný vzhľad, ale nemôže jej bezpečne vložiť vlastný bočný panel do okna bez spolupráce aplikácie. Kontajner nemení vnútorné rozloženie programu; iba oddeľuje jeho procesy a súbory.

Preto treba rozlišovať tri úrovne podpory:

1. **Vynútený rám a základný vzhľad**
  - rám okna, titulok, tlačidlá, farby, svetlý/tmavý režim a písmo;
  - cez kompozitor, GTK/libadwaita tému, portál a nastavenia kontajnera;
  - funguje aj pri aplikácii, ktorá LatteOS nepozná.
2. **Zosúladené štandardné prvky**
  - štandardné tlačidlá, vstupné polia, zoznamy, dialógy, stavové pruhy a navigačné prvky;
  - funguje pri aplikácii používajúcej GTK, Qt alebo iný podporovaný toolkit;
  - aplikácia môže vyzerať ako LatteOS, ale jej vlastné rozloženie zostane jej rozhodnutím.
3. **Natívna LatteOS integrácia**
  - presný bočný panel oblastí, vrstvené karty, navigačný pruh a informačný pruh;
  - aplikácia použije spoločnú knižnicu komponentov alebo LatteOS UI protokol;
  - vhodné pre App Manager, Nastavenia, Správcu súborov a budúce natívne aplikácie.

Pri Flatpaku treba podporovať štandardné portály a tému, aby aplikácia dostala farebný režim, akcent, písmo a systémové dialógy bez prístupu k hostiteľským súborom. Pri GTK aplikácii sa dá ponúknuť aj LatteOS widgetová knižnica. Pri Qt, Wine/Win32, Android/Waydroid alebo vzdialenom okne sa dá zjednotiť najmä rám, téma a systémové dialógy; presný bočný panel nie.

**Gwenview je konkrétny vzor kompatibilného okna.** Už má ľavý navigačný panel, horný navigačný pruh a hlavnú pracovnú plochu s obrázkom. LatteOS by mu preto nemalo vytvárať druhý panel ani meniť jeho pracovný tok. Namiesto toho má jeho existujúci panel dostať rovnaký vizuálny kontrakt ako `latte-files`:

- panel od horného okraja pracovného obsahu;
- priehľadnejšie pozadie než hlavná pracovná plocha;
- rovnaká šírka, okraj a vnútorné odstupy;
- rovnaký aktívny riadok, hover, ikonografia a stavový bod;
- rovnaký navigačný pruh so šípkami a spätnou navigáciou;
- rovnaký informačný alebo stavový pruh pri spodnom okraji.

Výsledkom má byť **Gwenview v LatteOS štýle**, nie vložené okno Gwenview do Správcu súborov a ani prekreslenie cudzieho obsahu filtrom. Qt/KDE adaptér môže upraviť jeho `QMainWindow`, `QToolBar`, `QDockWidget` alebo ekvivalentný navigačný panel. Pri Flatpaku sa adaptér dodá cez KDE/Qt tému, portál a balík kompatibility; samotné obrázky a funkcie Gwenview zostanú nezmenené.

Tento vzor sa má použiť aj pre ďalšie aplikácie s podobnou stavbou:

- **Dolphin** - zariadenia, miesta, záložky a hlavný zoznam;
- **Kate** - projektový panel, dokumenty a hlavná pracovná plocha;
- **Okular** - navigačný panel dokumentu a hlavný obsah;
- **Gwenview** - priečinky, obrázky, metadata a úpravy.

Kompatibilita sa má evidovať v profiloch aplikácií ako napríklad `sidebar = "aligned"`, `navigation = "aligned"`, `status_bar = "aligned"`. Aplikácia, ktorá má vlastný panel, sa nesmie označiť ako „bez podpory“ len preto, že nepoužíva LatteOS widgety. Stačí, ak jej existujúce štruktúry vieme vizuálne zosúladiť.

### Odporúčaný kontrakt pre natívne aplikácie

Spoločné LatteOS okná majú používať tieto voliteľné triedy a komponenty:

- `latte-titlebar` - spoločná výška a vzhľad titulkového pruhu;
- `latte-navigation-bar` - späť, dopredu, cesta alebo kontextová navigácia;
- `latte-sidebar` - bočný panel od horného okraja pracovného obsahu;
- `latte-status-bar` - trvalá informácia o aktuálnom obsahu;
- `latte-info-bar` - dočasné upozornenie alebo stavová správa;
- `latte-area-card` - oblasť Softvér, Dáta, Hardvér, Prihlásenie alebo Vzhľad;
- `latte-layered-navigation` - vrstvené skupiny a odkrytie kariet aktívnej oblasti.

App Manager otvorený z hlavného Nastavenia teda môže využiť presne rovnaký bočný panel a pruhy ako Nastavenia. Cudzia kontajnerová aplikácia môže dostať rovnakú tému a štandardné ovládacie prvky; presné LatteOS rozhranie použije iba vtedy, keď sa k integrácii prihlási.

Voľby pre tieto adaptéry sú v **Vzhľad > Integrácia aplikácií**. Používateľ tam môže samostatne zapnúť alebo vypnúť zosúladenie GTK a Qt/KDE. Portálové hodnoty zostávajú spoločnou systémovou vrstvou pre aplikácie, ktoré ho podporujú.

LatteOS nemá cudzej aplikácii prepisovať jej vlastné grafiky filtrom ani vkladať neviditeľné ovládacie prvky. Namiesto toho má aplikácii ponúknuť verejnú knižnicu, CSS tokeny, portály a jasnú úroveň kompatibility. Tak aplikácia, ktorá podporu využije, vyzerá natívne, a aplikácia bez podpory zostane čitateľná a funkčná.

## Čo nepatrí do hlavného Nastavenia

- celý katalóg aplikácií a obchodný obsah
- živý hardvérový strom s ovládačmi a kernelovými detailmi
- správca súborov
- terminálové príkazy a editovanie konfiguračných súborov
- pokročilý firewall a sieťové pravidlá pre administrátorov
- podrobné logy služieb, ktoré patria do Diagnostiky
- voľby konkrétnej aplikácie, ktoré aplikácia sama vlastní
- interný stav komponentov, ktorý používateľ nemá dôvod meniť

## Premietnutie do `index.toml`

Register stránok môže mať technické `group` id, ale používateľské rozhranie ich musí vykresliť ako päť vrstiev z kanonického stromu. Tým sa nemusí naraz meniť interné API registra.

| Vrstva v rozhraní | Technické skupiny v registri | Hlavné stránky |
|---|---|---|
| Softvér | `apps`, `updates`, časť `system` | App Manager, Aktualizácie, Systémové služby a relácia |
| Dáta | časť `system`, `updates` | Súbory a priečinky, Úložisko a zväzky, Zálohovanie a obnova, Synchronizácia |
| Hardvér | `devices`, `network`, časť `system` | Obrazovky, Zvuk, Sieť, Bluetooth a periférie, Napájanie, Tlač a skenovanie |
| Prihlásenie | `accounts`, časť `personalization` | Účet a používatelia, Heslo a bezpečnostné metódy, Prihlasovanie a uzamknutie |
| Vzhľad | `personalization`, `accessibility` | Motív a farby, Písmo a mierka, Pozadie, Okná, Lišta, Prístupnosť, Kontinuita |

Technické skupiny teda nemusia byť jeden ku jednej s vizuálnymi vrstvami. Dôležité je, aby sa jedna stránka v používateľskom strome zobrazila iba raz. Napríklad **Aktualizácie** nebude zároveň pod Aplikáciami aj pod Aktualizáciami a **Kamera a mikrofón** nebude zároveň pod Zariadeniami aj Súkromím. Na druhom mieste sa zobrazí len stav alebo odkaz na primárnu stránku.

Pri implementácii treba z existujúceho registra odstrániť alebo zlúčiť tieto zdvojené vstupy:

- `updates` + aktualizácie aplikácií -> jedna stránka **Aktualizácie** s oddielmi;
- `storage` + úložisko v dátach -> jedna stránka **Úložisko a zväzky**;
- `wifi` + samostatné sieťové stránky -> jedna oblasť **Sieť** s podstránkami;
- `lockscreen` + účty/prihlásenie -> oblasť **Prihlásenie**;
- `permissions` + kamera/mikrofón/súkromie -> jedna stránka **Súkromie a bezpečnosť** pod Softvérom, s odkazom z App Managera;
- `appearance` + vizuálne časti systémových stránok -> oblasť **Vzhľad**;
- `clock` + jazyk -> **Všeobecné systémové nastavenia** pod Softvérom.

Takto zostane v registri jeden cieľ pre každú funkciu a prekrývajúce sa manažéry budú používať navigáciu na tento cieľ, nie druhú stránku.

## Odporúčané MVP

Aby aplikácia nevznikla ako prázdny katalóg, prvá použiteľná verzia má obsahovať:

1. Prispôsobenie, ktoré už má hotovú doménu `appearance`.
2. Obrazovku s použitím existujúcej detekcie monitorov.
3. Zvuk s PipeWire stavom a predvoleným výstupom.
4. Wi-Fi, Bluetooth a úložisko ako stavové stránky s otvorením Správcu zdrojov.
5. Účty a čas/jazyk s polkit autorizáciou.
6. Aktualizácie systému cez `latte-updated`, oddelené od App Managera.
7. App Manager ako samostatnú aplikáciu, na ktorú Nastavenia odkazujú.
8. O LatteOS a softvérovú diagnostiku; hardvérovú diagnostiku ponechať Správcovi zdrojov.

## Záver

LatteOS nemá kopírovať Windows tým, že vloží všetky operácie do jednej obrovskej aplikácie. Má kopírovať jeho dobrú vlastnosť: používateľ nájde systémové voľby na jednom mieste. KDE a GNOME zároveň ukazujú, že modulárne vlastníctvo funguje lepšie než jeden vševediaci správca.

Preto je správne riešenie **integrovať kategórie a stav, nie implementácie**. Nastavenia sú jednotný katalóg a navigácia. App Manager, Správca zdrojov, Správca účtov a `latte-updated` zostávajú odbornými vlastníkmi svojich operácií.

## Zdroje

- [Microsoft: Windows 11 overview for administrators](https://learn.microsoft.com/en-us/windows/whats-new/windows-11-overview) - kategórie a hranice Windows 11, aktualizácie, aplikácie, bezpečnosť; kontrolované 2026-09-20.
- [GNOME Help](https://help.gnome.org/users/gnome-help/stable/) - oblasti používateľských a hardvérových nastavení GNOME; kontrolované 2026-09-20.
- [KDE System Settings](https://systemsettings.kde.org/) - modulárne členenie KDE Plasma; kontrolované 2026-09-20.
- [Fedora Magazine: What's New in Fedora Workstation 42](https://fedoramagazine.org/whats-new-fedora-workstation-42/) - Fedora Workstation, GNOME, aktualizácie a systémové služby; kontrolované 2026-09-20.
- [Nektony: Where to find System Settings on Mac](https://nektony.com/how-to/change-mac-settings) - macOS Ventura/System Settings, všeobecné nastavenia, login items, kontinuita, batéria, heslá, vzhľad, súkromie a zariadenia; kontrolované 2026-09-20.
- [Existujúci strom LatteOS](data/settings/index.toml) - aktuálne kategórie a plánované komponenty.
- [Architektúra nastavení LatteOS](docs/nastavenia.md) - domény, schémy, vlastníctvo a vrstvy hodnôt.
