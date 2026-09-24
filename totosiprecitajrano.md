# Toto si prečítaj ráno ☕

Denník práce, kým si spal. Najnovšie hore. Na konci sú **veci, ktoré čakajú na tvoje rozhodnutie**.

> Stav 24. 9. ráno: VM beží, tvoja relácia (Hyprland + Noctalia) tiež a nová lišta sa v nej ukázala
> sama, lebo Noctalia načíta zmeny za behu. Jedna vec sa pokazila a je opravená: počas inštalácie sa
> Hyprland na chvíľu dostal do núdzového režimu (červený rámik hore). Viac v denníku.

---

## Zadanie 24. 9. popoludní (tvoje pripomienky) — poradie práce

Odpovede:
- **kitty:** nie je náš, prišiel ako závislosť. Pod Hyprlandom nemá žiadne okenné tlačidlá, ani žiadne
  iné okno ich teraz nemá. Zavrieš ho Super+Q alebo Ctrl+Shift+W. Riešenie je bod 1 nižšie.
- **KDE Connect:** oznámenia z mobilu na PC (aj odpoveď na SMS), spoločná schránka PC ↔ mobil,
  posielanie súborov oboma smermi, ovládanie hudby, „nájdi mobil“, mobil ako touchpad a prezentér.
  Potrebuje aplikáciu na mobile a rovnakú sieť, na PC ~150 MB knižníc KDE.
- **Gestá 4 prstami** sú teraz iba pre touchpad. Dotykový monitor potrebuje plugin hyprgrass (swipe,
  dlhé podržanie); príde s reálnym HW (VirtualBox dotyk nepreposiela).
- **Ikony na ploche** zatiaľ nie sú (Noctalia to nemá). Príde vlastná vrstva plochy s Košom.

Poradie (začnem od 1):
1. **Okná:** jednotná lišta vpravo pre všetky aplikácie: NET (iba ak aplikácia použila internet), minimalizovať,
   zväčšiť, zavrieť; Electron cez pripnutý pruh zvonku. Všetky popupy „vyrastajú“ z lišty (L-tvar).
2. **Lišta:** široká šálka; dlaždica aplikácií iba normálny klik (App Manager, bez duplicity so spúšťačom);
   Hodiny = hodiny, zóny, stopky, budík, časovač; Dátum = kalendár + úlohy, počet úloh „št 24. 9. (3)“;
   medzi nimi zvonček s počtom oznámení; Zariadenia úplne vpravo.
3. **Ovál pásky za šálkou:** živý obraz otvorených okien (páska / dlaždice / vedľa seba) s ikonou aplikácie,
   náhľad pri prejdení myšou, ľavý klik prepne, pravý kontextové menu (ako Windows).
4. **Šálka popup:** hore účet + typ + Odhlásiť vedľa; Nastavenia; Monitor; rýchly stupeň výkonu a režim okien
   (dajú sa vypnúť v Nastaveniach); Nastavenia shellu presunúť do Nastavení.
5. **Text Bar:** širší riadok s textom, ikona režimu na okraji (koliesko/šípky prepínajú), pravý klik rýchle voľby.
   AI odpoveď v popupe s **pinom** → pripnuté sa zmení na okno. AI cez prihlásenie (ako widget Claude/ChatGPT
   na mobile, bez API kľúča) a voľba **„Bez AI“** už v Baristovi (potom sú AI voľby skryté).
6. **Kapsa:** široká plocha ako hodiny, hore „kontajner“ na jeden odložený súbor (drag & drop, živá ikona),
   dole 8 slotov schránky (nastaviteľné), náhľad pri prejdení myšou.
7. **Súbory:** 2 režimy — Forklift (náhľad vpravo vypínateľný, veľkosť ikon ako Win11, nový súbor/priečinok,
   „Otvoriť v…“ s odporúčanými aplikáciami z App Managera) a **Total Commander** (plná funkčnosť, FTP/SFTP).
   Kôš na ploche a v bočnom menu.
8. **Heidelberg:** plnohodnotný editor (písma, formátovanie, príprava pred tlačou, kontrola textu), pandoc v základe.
9. **Greeter:** varovania Caps Lock / Num Lock, zobraziť heslo, písma ako v systéme.
10. **Monitor:** ako Správca úloh Win11 + Autoruns + CPU-Z/HWiNFO.
11. **Maskot:** Cthulhu mačka s chápadlami cez lištu, pet uniká pri nečinnosti (vypínateľné).
12. **Živá tapeta:** ako Live Wallpaper (video/animované tapety); textúry naviazané na tému (para zo šálky ikonky…).

## Odpovede na tvoje otázky (24. 9.)

### Dajú sa položky lišty prerozdeliť inam, ako súčasť iných menu?
Áno. Lišta je z **ostrovov** (`[[bar.main.capsule_group]]` v `session/noctalia/config.toml`). Každý
ostrov je zoznam widgetov, dajú sa presúvať medzi ostrovmi a ostrovy medzi ľavou, strednou a pravou
časťou. Panely sa dajú zlučovať: oznámenia sú teraz aj záložkou v paneli Čas. Zvonček v ostrove času
som nechal ako rýchly vstup, dá sa odobrať jedným riadkom. Grafický editor rozloženia zatiaľ nie je
(ťahanie myšou); dovtedy to zmením podľa tvojho slova.

### Kde je mačka? 🐱
Na lište vpravo, pred schránkou. Bongocat z Caelestie som **nepoužil**: je to cudzia kresba pod GPL-3
a pôvodný „bongo cat“ má vlastného autora. Nakreslil som vlastných pixel maskotov:
**Latte mačka**, **Mokka** (čierna) a **Zrnko** (kávové minimonštrum). Keď hrá hudba, ťukajú labkami
do rytmu, inak sedia a žmurkajú a v noci či pri Nerušiť spia. Klik ich pohladká, pravý klik prepne
maskota. Voľba je aj v Nastaveniach › Prostredie › Lišta.

### Svetlá/tmavá verzia každej témy, automaticky podľa slnka
Hotové. Všetkých 14 tém má tmavú aj svetlú paletu. V Nastaveniach › Prostredie › Motív a farby si
vyberieš **Podľa témy / Tmavá / Svetlá / Automaticky (slnko)**. Automatický režim prepína Noctalia
podľa východu a západu slnka pre polohu. Predvolená poloha je stred Slovenska; zmena je v Systém ›
Dátum, čas a poloha (mestá SK, CZ a okolie).

---

## Denník

## Zadanie 24. 9. večer (22:04): Monitor ako HWiNFO/CPU-Z, pohoda ako Pulse, maskot ako tamagoči s útekmi
Poradie: 1. Monitor (hotové nižšie) → 2. Digitálna pohoda podľa Pulse → 3. maskot (nové postavy, potreby, útek z ostrova).

**Doplnené 25. 9. (tvoje odkazy):**
- **Kolekcia maskotov** (tvoj návrh „LatteOS Pet Collection“), každý s vlastnou osobnosťou:
  Coffee Dragon, Homebrew (kávový sliz v šálke), Meow of Cathulhu, Firefly, Little Fox, Pixel Maid, Mini Robot, Raccoon,
  Void Baby Dragon a Capybara. Každý má animácie v pokoji, v pohybe a pri spánku.
  - **Režimy** prevezmem z návrhu:
    - **OFF**;
    - **SLOT** (sedí vo svojom ostrove na lište);
    - **WORLD** (občas vybehne z brlohu: chodí po lište, sadá na titulky okien, lezie po okrajoch, pri nečinnosti spí alebo sa zaujíma o kurzor);
    - **CHAOS** (voľne po celej ploche, hrá sa s kurzorom).
  - **Bezpečnosť:** maskot je iba obrázok vo vrstve nad plochou, bez prístupu k súborom. Balíčky od komunity
    budú iba dáta (sprity + JSON s osobnosťou), žiadny kód.
  - **Technika úteku:** samostatná priehľadná vrstva (layer-shell) nad oknami, ktorá prepúšťa kliky okrem samotného maskota.
    Polohy okien zistí z `hyprctl clients` (titulky, okraje). Pri softvérovom vykresľovaní pobeží pomaly (4 obr/s),
    s GPU plynulo.
- **Živé tapety — [aura](https://github.com/antwny/aura):** Rust + mpv, pauza pri hre a zakrytej ploche, farby z videa.
  Je však napísaná pre COSMIC (libcosmic) a má licenciu GPL-3.0. Prevezmem **princíp** (mpv vo vrstve pozadia a pauza,
  keď je plocha zakrytá alebo beží hra na celú obrazovku) do našej tapety, nie celú aplikáciu. Do resources si ju naklonujem
  ako vzor.
- **[skwd-wall](https://github.com/liixini/skwd-wall):** je postavený na Quickshelli ako my, takže sa dá dobre prevziať.
  Ponúka 4 výbery tapiet vykresľované na GPU, 39 prechodov (až po „piesok“), obrázky, videá aj scény Wallpaper Engine
  a farby cez matugen. Pri nečinnosti nekreslí. Režim prezentácie tapiet vyzerá použiteľne pre Nastavenia › Tapeta.
- **Efekty aj na okná a popupy?** Áno, ale iba na reálnom HW s GPU:
  - **popupy a panely LatteOS** sú v Quickshelli, takže rovnaké shadery (ShaderEffect) sa dajú použiť priamo;
  - **okná aplikácií** kreslí Hyprland, teda treba plugin so shaderom na okno (vzor hypr-darkwindow, už je v resources)
    alebo animácie Hyprlandu;
  - pri stupni Softvér ostanú vypnuté (pravidlo „každý prvok má variant bez shaderov“).

### 25. 9. 2026: Maskoti — 12 postáv, potreby ako tamagoči, výbehy z ostrova ✅ (panel po ďalšom prihlásení)
- **Nové postavy** (vlastná pixel-art, ručne kreslené predlohy):
  - Homebrew (kávový sliz pod prevrátenou šálkou, s lyžičkou);
  - Kávový drak v šálke;
  - Líška, Mýval, Mini robot, Svetluška, Kapybara s kačičkou a Void drak;
  - k tomu pôvodné Latte mačka, Mokka, Zrnko a Ktulu.

  Každá postava má snímky sedí, žmurkne, spí, radosť, smutná, ťukanie do hudby, odchod a chôdzu doľava aj doprava.
- **Podrobnejší pixel-art** (tvoja pripomienka): generátor po novom tieňuje (svetlá horná hrana, tieň dole) a zväčšuje
  cez scale2x, teda so zaoblenými šikminami namiesto kociek. Úroveň tvojej kolekcie (ručne kreslené asi 64 px)
  z ASCII predlôh nedosiahne. Ďalší krok preto bude **balíček PNG**: priečinok s podrobnými snímkami a `pet.json`
  (meno, lieta alebo chodí, osobnosť). Tak sa dajú použiť sprity vyrezané z tvojej kolekcie alebo od komunity,
  bez kódu, iba dáta.
- **Potreby:** káva, nálada a energia plynú v čase. V noci, pri Nerušiť alebo po uložení spať si maskot dobíja energiu.
  Keď chce kávu, je smutný a tooltip to povie. Starostlivosť počíta „deň N s tebou“.
- **Panel maskota** (pravý klik):
  - podoba, potreby s pruhmi;
  - akcie Dať kávu, Pohladkať, Hrať sa a Spať;
  - **režim:** Vypnutý / Ostrov (iba na lište) / **Výbehy** (predvolené) / Chaos;
  - mriežka všetkých 12 postáv.
- **Výbehy** (`apps/maskot.qml`, malé okno nad oknami, kliky mimo maskota prechádzajú):
  - Maskot občas alebo po „Hrať sa“ odíde z ostrova (widget prehrá odchod a ostrov ostane prázdny).
  - Chodí po hornej hrane lišty a **sadá na titulky okien**, ktoré šplhá hore. Lietajúce postavy (drak, svetluška,
    robot, void) letia rovno. Keď sa okno pohne, maskot sa vezie s ním, keď zmizne, zoskočí.
  - Po chvíli sa vráti domov.
  - Keď si 3 min nečinný, príde **zdriemnuť si ku kurzoru** a po tvojom návrate sa zobudí a ide domov.
  - V Chaose a pri hre naháňa kurzor. Pri hre alebo okne na celú obrazovku sa hneď schová.
  - Klik ho pohladká, pravý klik ho pošle domov. Klik na prázdny ostrov ho zavolá domov.
  - Pri stupni Softvér sa hýbe 4 krokmi za sekundu, s GPU 20.
- Otestované naživo: výbeh s naháňaním kurzora, návrat do ostrova a panel v headless Noctalii.
  **Panel na pravý klik uvidíš až po ďalšom prihlásení**, rovnako ako pri iných nových widgetoch.
  Výbehy už bežia aj teraz.
- **Pixel Maid** som nespravil: je to zjavne postava Asuka z Evangelionu, čiže cudzia chránená postava.
  Vlastnú podobnú „čašníčku“ viem nakresliť, ak chceš.

**Tvoje otázky z 25. 9.:**
- **Sklo (priehľadnosť s rozmazaním):** nie je to zámer, ktorý by si mal vidieť ako zhoršenie.
  - Stará vetva ho kreslila **softvérovo**: tapetu rozmazala raz pri štarte a panely mali za sebou jej výrez.
  - V novej vetve ho robí Hyprland (blur), a to iba pri stupňoch Plný a Štandard, teda s GPU. Vo VM s llvmpipe
    rozmazanie spôsobovalo pády (denník 23. 9., 21:40), preto je pri stupni Softvér vypnuté a náhrada chýba.
  - **Do plánu:** softvérové sklo ako v starej vetve pre panely a popupy LatteOS (Quickshell), ktoré majú pevnú
    polohu a rozmazaný výrez tapety pod sebou. Pri pohyblivých oknách aplikácií to softvérovo nejde, tam ostane GPU blur.
- **Súbory ako Total Commander:** súhlasím, že to ešte nie je plná náhrada. Do plánu som dal zoznam, čo chýba:
  - F-lišta (F3 zobraziť, F4 upraviť, F5 kopírovať, F6 presunúť, F7 priečinok, F8 zmazať);
  - karty v každom paneli;
  - výber maskou (+ / − / *), rýchly filter písaním;
  - hromadné premenovanie s náhľadom;
  - porovnanie a synchronizácia priečinkov;
  - archívy ako priečinky (zip/7z/rar), balenie a rozbalenie;
  - hľadanie aj v obsahu súborov;
  - obľúbené priečinky (hotlist) a riadok príkazu;
  - Lister (rýchly náhľad), výpočet veľkosti priečinkov;
  - kontrolné súčty, rozdelenie a spojenie súborov.

  Povedz, ktoré z nich používaš najviac, a začnem nimi.

### 25. 9. 2026: Digitálna pohoda podľa Pulse ✅
Monitor › Čas v aplikáciách má karty:
- **Prehľad:** „Dobré popoludnie“, kruh s dnešným časom voči dennému cieľu, rozdelenie medzi aplikácie,
  práve používaná aplikácia, týždeň, najviac dnes s osou dňa, karta Sústredenie, denný cieľ (2–8 h), sluch a kategórie.
- **Čas obrazovky:** aktívny čas na osi dňa, sedenia (delí ich prestávka ≥ 5 min), najdlhší úsek, prestávky,
  prepnutia aplikácií, priemerné a najdlhšie sústredenie v jednej aplikácii.
- **Aplikácie:** doterajší pohľad (deň, týždeň, mesiac, limity).
- **Sústredenie:** sedenie 15–90 min a spôsob riešenia rozptýlení.
  - **Upozorniť:** oznámenie, najviac raz za minútu.
  - **Odsunúť:** okno sa minimalizuje a vrátiš ho z lišty.
  - Rozptýlenie je aplikácia z kategórie **Zábava**. Kategórie (Práca, Zábava, Neutrálne) prepneš pri každej
    aplikácii, predvolene sa určia podľa .desktop (hry, video, hudba, Discord = zábava; vývoj, kancelária = práca).
  - Ukazuje históriu sedení týždňa (dokončené alebo prerušené, počet rozptýlení).
- **Sluch:** čas počúvania a hlasného počúvania v slúchadlách (hlasitosť ≥ prah 60–90 %) na osi dňa
  a odporúčanie WHO. Je to odhad podľa hlasitosti systému, nie meranie decibelov.
- **Prehľady:** denný priemer, týždeň spolu oproti minulému, práca vs zábava, top aplikácie a počet sedení sústredenia.

Tracker (`pohoda.qml`) po novom zapisuje aj úseky aktivity, prepnutia, sústredenie, sluch a sedenia.
Sústredenie ovláda cez IPC (`fokusStart`, `fokusStop`). Otestované: sedenie 1 min sa dokončilo a v režime Odsunúť
sa foot označený ako zábava presunul medzi minimalizované okná. Testovacie záznamy som zo tvojho dňa vymazal.

### 25. 9. 2026: Monitor › Hardvér ako CPU-Z a Senzory ako HWiNFO ✅
- **Hardvér** má karty ako CPU-Z:
  - **Procesor:** kódové meno (napr. Rocket Lake), technológia v nm, rodina/model/stepping, inštrukcie
    (SSE…AVX2, AES, SHA), takty, násobič, cache a živé takty a záťaž jadier.
  - **Cache:** L1d/L1i/L2/L3 s počtom, asociativitou a dĺžkou riadku.
  - **Doska:** čipová sada, BIOS/UEFI, Secure Boot, PCIe linka grafiky.
  - **Pamäť** a **SPD:** sloty, typ, rýchlosť, výrobca, číslo dielu a časovania, ak sú dostupné.
  - **Grafika:** ovládač, VRAM, OpenGL a Vulkan.
  - **Disky:** SMART, teplota, hodiny, zapísané dáta, opotrebenie.
  - **Systém.**
- **Podrobnosti so správcom:** heslo raz, výsledok (dmidecode, smartctl) sa uloží do `~/.cache/latteos/hw-root.json`
  a nabudúce heslo netreba. **Uložiť správu** vytvorí textovú správu v Dokumentoch ako „Save Report“ v HWiNFO.
- **Senzory** (nová stránka) fungujú ako okno Sensor Status v HWiNFO:
  - skupiny Procesor (záťaž a takt každého jadra, výkon RAPL), všetky čipy hwmon (teploty, ventilátory, napätia,
    výkon), Pamäť, Disky (čítanie, zápis, aktivita), Sieť, Grafika (záťaž, VRAM, takty), Batéria a Systém;
  - stĺpce **Aktuálne, Minimum, Maximum, Priemer**;
  - klik na senzor pridá **graf** dole;
  - **pravý klik:** Zobraziť graf, **Pridať na lištu**, Premenovať, Skryť, Kopírovať, Vynulovať;
  - tlačidlá **Záznam do CSV** (Dokumenty) a Vynulovať.
- **Senzory na lište:** vybrané hodnoty sa ukážu v ostrove zariadení, napr. „14,5 % · 3214 MB“.
  Rovnako ako indikátor mikrofónu sa objavia až po ďalšom prihlásení. Overené v headless Noctalii.
- Vo VM je senzorov málo (bez teplôt a ventilátorov) a dmidecode nevracia moduly. Parser som overil
  na vzorovom výpise z reálnej dosky. Na skutočnom PC sa ukážu teploty, napätia, ventilátory aj moduly.
- Nové balíky v install-session: smartmontools, dmidecode, mesa-demos, vulkan-tools, i2c-tools.

### 24. 9. 2026, 21:50: Setup Plan aj pre natívne aplikácie (RPM) — izolácia bubblewrap ✅
- **Pravý klik › Setup Plan** funguje aj pri aplikáciách z Fedory, napr. Foot a kitty. Natívna aplikácia si nič
  nežiada, preto plán navrhuje LatteOS. Obsahuje položky Internet, Celý domov (inak súkromný), Stiahnuté, Zvuk a mikrofón,
  Kamera a zariadenia, Grafická karta a Okná (nutné).
- Nový `latte-sandbox run APP -- príkaz` spustí aplikáciu v **bubblewrape** podľa plánu:
  - bez siete ostane iba lo;
  - namiesto domova dostane súkromný priečinok (`~/.local/share/latteos/sandbox/APP`), voliteľne so Stiahnutými,
    a písma a vzhľad iba na čítanie;
  - bez zvuku sú skryté sockety PipeWire;
  - bez zariadení má minimálny /dev, grafická karta ostáva.

  Spúšťa sa to cez prekrytie .desktop, takže to platí pre lištu, Text Bar aj App Manager. Bez zamietnutí sa prekrytie zmaže.
- **Tlačidlo NET** pri natívnych aplikáciách teraz zapisuje do toho istého plánu, takže nevznikajú dva obaly.
  Staré prekrytia NET sa prečítajú správne.
- Otestované na Foot s profilom Nedôveryhodná, spusteným cez .desktop:
  - bežal pod bwrap vo vlastnom sieťovom aj mount mennom priestore;
  - domov obsahoval iba Stiahnuté, pactl sa nepripojil a okno sa normálne otvorilo.

  Potom som všetko vrátil: plán, prekrytie aj súkromný priečinok som zmazal.
- **Filter zbernice D-Bus** (21:55): položka „Celá zbernica relácie“, ktorú profil Nedôveryhodná vypne.
  Aplikácia potom cez `xdg-dbus-proxy` vidí iba portály (Desktop, Documents), oznámenia, tray, šetrič
  obrazovky, prístupnosť a vlastný názov, takže neovláda iné aplikácie ani služby.
  Ak sa filter nespustí, aplikácia nedostane zbernicu vôbec (nie celú). Proxy skončí spolu s aplikáciou.
  Otestované: `busctl` v sandboxe videl iba 9 povolených služieb, `notify-send` prešiel a Foot sa otvoril.
- Chýbajú profily pre Windows aplikácie (Proton/Wine), ktoré prídu s inštaláciou hier.

### 24. 9. 2026, 21:45: indikátor mikrofónu a kamery na lište ✅ (ukáže sa po ďalšom prihlásení)
- Kým niektorá aplikácia používa **mikrofón alebo kameru**, v ostrove zariadení svieti **červená kapsula**
  s ikonou, ako bodka v iOS a Androide. Inak je neviditeľná. Tooltip povie ktorá aplikácia
  (napr. „Mikrofón: Discord“), klik otvorí Monitor › Procesy. Kontroluje sa raz za 3 s (`latte-sysmon sukromie`, ~90 ms).
- Zvukový server (PipeWire) sa nepočíta, pretože zariadenia drží stále otvorené. Počítajú sa jeho klienti.
- **V tvojej relácii ešte nie je vidieť.** Noctalia načíta nové widgety lišty iba pri štarte a reštart lišty
  som ti na diaľku nechcel robiť. Objaví sa po ďalšom prihlásení. Otestované v headless Noctalii s bežiacim
  `parecord` (snímka: červený mikrofón pred ikonou súborov).

### 24. 9. 2026, 21:35: Monitor › Procesy podľa aplikácií ✅
- Procesy sú predvolene zoskupené **podľa aplikácií**, ako v Správcovi úloh vo Windows. Každá aplikácia ukazuje
  súčet CPU a RAM. Klik ju rozbalí na procesy, detail ukáže súčty a tlačidlo **Ukončiť aplikáciu**
  (s potvrdením). Pravý klik ponúka Rozbaliť, Ukončiť aplikáciu a Detail v App Manageri.
- Príslušnosť k aplikácii sa zistí tromi spôsobmi:
  - Flatpak podľa cgroup (`app-flatpak-ID`), takže Discord má všetkých 23 procesov vrátane izolácie;
  - scope systemd;
  - najbližší predok s oknom.
  Aplikácie LatteOS sa rozlíšia podľa titulku. Procesy bez aplikácie sú v „Ostatné procesy“.
- Aplikácia bez okna má pri názve „· na pozadí“ (napr. Discord v tray). Detail procesu ukazuje, ku ktorej aplikácii patrí.
- Tlačidlo „Strom“ ostáva; prepína sa medzi stromom a zoskupením.
- **Zariadenia:** pri aplikácii a procese sa ukazuje, čo práve používa:
  - mikrofón a kamera sú červené (súkromie), prehrávanie zvuku je oranžové, grafická karta sivá;
  - detail ukazuje riadok „Práve používa“.
  Zisťuje sa z otvorených /dev zariadení a streamov PipeWire (pactl), raz za 5 s (~55 ms).
  Otestované: `parecord` vo `foot` ukázal mikrofón pri Foot, Discord ukazuje GPU.

### 24. 9. 2026, 21:30: Setup Plan pred inštaláciou (F6, vzor Flatseal) ✅
- **Inštalovať** v obchode najprv otvorí **Setup Plan** so zoznamom toho, čo si aplikácia žiada, v zrozumiteľnej reči
  a po skupinách: Internet, Súbory, Zariadenia, Zvuk, Tajomstvá (SSH/GPG kľúče, kľúčenka), Systém, Okná.
  Bodka pri položke ukazuje riziko: sivá nízke, oranžová stredné, červená vysoké (napr. „celý počítač“, „všetky zariadenia“).
- Plán schváliš celý, vypneš jednotlivé položky prepínačom alebo zvolíš profil:
  - **Dôveryhodná:** všetko, čo si žiada;
  - **Nedôveryhodná:** bez internetu, domova, mikrofónu a citlivých prístupov;
  - **Vlastná:** podľa prepínačov.
  Ukáže sa aj veľkosť a to, či sa stiahne runtime.
- Po inštalácii sa zamietnuté oprávnenia zapíšu do izolácie Flatpaku (`flatpak override --user`) a plán sa uloží
  do `~/.config/latteos/plany/`. Pri opätovnej inštalácii sa ponúkne rovnaký plán.
- Pre nainštalované Flatpaky je **pravý klik › Setup Plan (čo smie)** v Nainštalovaných, na kartách obchodu
  a v detaile. Plán vychádza z aktuálneho stavu, takže vypnutý NET alebo úpravy z Flatseal sa nestratia.
- Otestované: Papers s profilom Nedôveryhodná. Override bol `!pulseaudio`, `!home` a plán sa po inštalácii
  načítal späť správne. Papers som potom odinštaloval a override aj plán zmazal. Discord ostal nezmenený.
- Ďalší krok (F6): trusted/untrusted aj pre natívne a Windows aplikácie (bubblewrap/Proton). Zatiaľ platí iba pre Flatpak.

### 24. 9. 2026, 21:25: Text Bar /cmd lepšie rozozná nebezpečné príkazy ✅
- Predtým sa chytalo iba `rm -r/-f`, `sudo` na začiatku a pár ďalších príkazov. Teraz sa kontroluje prvé slovo
  **každej časti** príkazu, teda aj za `;`, `&&`, `|` a `$(`. Takto sa chytí napr. `ls; rm x` alebo `/usr/bin/rm`.
- Pribudli: obyčajné `rm`, `shred`, `truncate`, `find -delete`, `kill`/`killall`/`pkill`, reštart a vypnutie,
  `pkexec`/`su`, `rpm -e`, `flatpak uninstall`, `git reset --hard`/`clean`/`push --force`, `curl … | sh`,
  prepis `> /etc/…`, `/boot`, `/usr` a presun do koreňa.
- Falošné poplachy sa neukazujú: `grep rm súbor`, `man kill` aj `echo removal` prejdú bez varovania.
  Otestované 25 nebezpečnými a 19 bezpečnými príkazmi a naživo v Text Bare.

### 24. 9. 2026, 21:20: Heidelberg otvára PDF ✅
- PDF sa otvorí na úpravu (text, tučné písmo, zlomy strán). Riadky zalomené uprostred vety sa spoja do odsekov.
  Používa sa `pdftohtml` z balíka poppler-utils; na VM som ho doinštaloval, je aj v install-session.
  Ak chýba, Heidelberg ponúkne tlačidlo „Doinštalovať otváranie PDF“.
- Originál sa nikdy neprepíše. Ctrl+S uloží úpravy vedľa ako „názov (upravené).html“.
  Nové PDF vytvoríš tlačidlom PDF (Export).
- Heidelberg je v „Otvoriť pomocou“ pre PDF, hneď za prehliadačom Papers.
- Obmedzenie: naskenované PDF (iba obrázky) nemajú text, takže sa v nich upravovať nedá.
  Na také PDF by bolo treba OCR (tesseract), ktoré zatiaľ nie je.
- Otestované na príručke bzip2 (18 609 slov): otvorenie aj uloženie fungujú, testovacie súbory som zmazal.

### 24. 9. 2026, 21:15: pravý klik aj tam, kde chýbal (prechod všetkými aplikáciami) ✅
- **Plocha:** pravý klik na prázdne miesto: Nový priečinok, Nový textový súbor, Otvoriť Plochu v Súboroch,
  Terminál tu, Zmeniť tapetu, Živá tapeta, Obrazovky, Skryť ikony. Súbor sa dá pustiť kdekoľvek na plochu.
- **Heidelberg:**
  - v texte Vystrihnúť, Kopírovať, Vložiť, Vybrať všetko, Tučné, Kurzíva, Vymazať formát; pri slove
    **návrhy pravopisu** (klik = náhrada), „Pridať do slovníka“, Hľadať na webe;
  - na dokumente v bočnom paneli Otvoriť, Priečinok, Kopírovať cestu, Odstrániť z nedávnych, Do koša.
- **AI rozhovor:** na správe Kopírovať, Uložiť do Heidelbergu, Poslať znova, Vymazať rozhovor.
- **Správca zariadení:** podľa zariadenia disk (Otvoriť v Súboroch, Bezpečne odobrať USB), sieť
  (Odpojiť/Pripojiť), profil výkonu (Úsporný/Vyvážený/Výkonný), grafika a počítač (Hardvér v Monitore),
  klávesnica. Pri každom Kopírovať informácie.
- **Monitor › Po štarte:** Zapnúť/Vypnúť, Otvoriť súbor v Heidelbergu, Ukázať v Súboroch, Kopírovať príkaz,
  Hľadať na webe.
- **Nastavenia:** na stránke Otvoriť, Skratka na ploche, Kopírovať príkaz; na tapete Nastaviť, Aj na
  prihlasovaciu obrazovku, Ukázať v Súboroch, Kopírovať cestu.
- Oprava: pri pustení súboru na plochu sa cesta Plochy vkladala do príkazu shellu, teraz ide ako argument.

### 24. 9. 2026, 21:00: Čas v aplikáciách vo vzhľade serpantinum ✅
- Podľa tvojho rozhodnutia (AGPL nevadí, OS nebude platený) som prostredie Digitálnej pohody prevzal zo
  serpantinum a upravil na LatteOS. Je v samostatnom súbore `session/apps/data/PohodaView.qml` pod
  **AGPL-3.0-or-later** s uvedením pôvodu, zapísané aj v resources/MANIFEST.md. Zvyšok LatteOS tým nie je dotknutý.
  - Pozor pri doplnkových službách: ak by upravený AGPL kód bežal na serveri, ku ktorému sa ľudia pripájajú,
    jeho zdrojový kód musí byť pre nich dostupný.
  - LatteOS zatiaľ **nemá vlastnú licenciu** (v repozitári chýba LICENSE). Pridal som to do „Čaká na tvoje
    rozhodnutie“.
- **Deň:**
  - hlavička s dňom a šípkami (aj klávesy ←/→), Týždeň, Späť;
  - karty **denný priemer | veľký súčet dňa | oproti včerajšku** (▲ oranžová / ▼ zelená);
  - **týždeň** v stĺpcoch s gradientom na vybranom dni, klik prepne deň;
  - **mesiac ako teplotná mapa**, klik = deň;
  - **aplikácie** so štvorcovou ikonou, pruhom a časom. Klik = **deň aplikácie po polhodinách**,
    pravý klik = denný limit.
- **Týždeň:** mapa 7 dní × 24 hodín, denný priemer, **najčastejšie hodiny** (napr. 19:00 – 21:00), aplikácie týždňa.
- Nábehové animácie (hlavička → karty → stred → zoznam, pružné stĺpce) sú zapnuté iba s GPU. Vo VM sa stránka
  ukáže hneď.
- Meranie teraz zapisuje aj polhodiny. Staršie záznamy (iba hodiny) sa rozdelia na polovice.

### 24. 9. 2026, 20:50: Digitálna pohoda — koľko času v ktorej aplikácii ✅
- **Meranie** (latte-app pohoda, na pozadí): každých 5 s pripočíta čas aktívnemu oknu. Keď si 5 minút
  nečinný, nepočíta, ale prehrávané video sa ráta. Aplikácie LatteOS rozlišuje podľa názvu (Súbory, Monitor…).
  Raz za minútu zmeria pamäť aplikácie aj s podprocesmi. Údaje ostávajú v PC (~/.local/share/latteos/pohoda).
- **Monitor › Čas v aplikáciách** (inšpirované videom a serpantinum, kód vlastný — serpantinum je AGPL):
  - **Dnes**, porovnanie so včerajškom, **7 dní** s denným priemerom, **najviac používaná** aplikácia;
  - **časová os dňa po hodinách** farebne podľa aplikácií (podržanie myši = čas v hodine);
  - **koláč dňa** s legendou, **stĺpce za 7 dní**, zoznam aplikácií s ikonou (dnes, 7 dní, obvykle v RAM);
  - **pravý klik = denný limit** 15 min – 3 h: 5 minút pred limitom a pri ňom príde oznámenie ako v Androide;
  - prepínač na pozastavenie merania.
- **App Manager › Nainštalované:** klik na aplikáciu ukáže aj **čas v aplikácii** (dnes, 30 dní), **v pamäti
  obvykle / najviac** a **miesto na disku**.
- **Animácie ako vo videu:** okná a plochy už majú pružinové krivky Hyprlandu a panely Noctalie sa animujú.
  Vo VM (stupeň Softvér) sú však vypnuté, lebo by sa trhali. Rýchle spustenie sa teraz pri stupni s GPU
  vysunie z dlaždice a prelína. Rovnako doplním ďalšie panely, keď budeme na reálnom HW (ROADMAP).

### 24. 9. 2026, 20:30: šípky Späť / Dopredu iba keď sa dajú použiť ✅
- **Pravidlo pre všetky aplikácie LatteOS** (spoločná hlavička): šípka Späť je vidieť iba vtedy, keď je kam
  sa vrátiť, Dopredu iba po návrate. Aplikácie bez prechádzania (Monitor, Heidelberg, AI, Správca zariadení)
  ich nemajú vôbec. Neaktívne sivé šípky už nikde nie sú. Klávesy Alt+← a Alt+→ robia to isté.
- Históriu si pamätajú Súbory (priečinky), Nastavenia (stránky) a teraz aj **App Manager**
  (obchod → kategória → detail aplikácie, sekcie).
- Tlačidlo „‹ Späť do obchodu“ som odstránil, aby Späť nebolo dvakrát.

### 24. 9. 2026, 20:15: pravý klik, ukazovateľ rolovania, Discord 1×, inštalácia zo zložky ✅
- **Pravý klik na ikonu aplikácie** v rýchlom spustení je ponuka ako v ponuke Štart vo Windows 11:
  - Otvoriť a **úlohy aplikácie** (Firefox: Nové okno, Nové súkromné okno…);
  - **Pripnúť medzi obľúbené** (sekcia PRIPNUTÉ navrchu), **Odsunúť na koniec zoznamu** (aplikácie, ktoré ťa
    nezaujímajú, sú úplne dole v sekcii ODSUNUTÉ, dajú sa vrátiť);
  - Pridať na plochu (spúšťač s ikonou), Otvoriť umiestnenie súboru, Detail v App Manageri, Odinštalovať.
  - Karty v obchode majú tiež pravý klik: detail, inštalovať/otvoriť, oprávnenia, Flathub, odinštalovať.
  - Máš pravdu, že na kontextové ponuky zabúdam. Zapísal som si to ako trvalé pravidlo.
- **Ukazovateľ rolovania** je teraz pri každom zozname vo všetkých aplikáciách LatteOS (21 miest). Je to tenký
  pás pri okraji, pri rolovaní a pod myšou výraznejší, dá sa potiahnuť. Pri pásoch v obchode je vodorovný.
- **Discord 2×:** bol raz v oblasti oznámení a raz medzi bežiacimi Flatpakmi. Flatpak s ikonou v oblasti
  oznámení sa už druhýkrát neukáže.
- **Bude to fungovať? pre hry a programy mimo obchodu** (inštaláciu odkladáme, teraz iba overujeme rozpoznanie):
  - **zložka s inštalátorom** (setup.exe + fg-01…06.bin ako tvoj repack, MD5, „Verify BIN files“) aj CD/DVD
    s autorun.inf: plán overiť .bin, vytvoriť samostatný sandbox (Wine prefix v ~/Hry/<hra>), spustiť setup
    a nakoniec vytvoriť spúšťač;
  - **prenosná hra** (iba napr. RA95.exe, bez inštalátora): hlavný program, sandbox, spúšťač;
  - **archív** .zip (už teraz), .rar/.7z/.iso (po doinštalovaní 7-Zip): rozbaliť do ~/Hry a potom ako zložka;
  - hra pre Linux (GOG .sh, .x86_64) → priamo; redist knižnice sa preskočia; počíta potrebné miesto
    (repack ~2,5×); upozorní na anti-cheat.
  - Súbory: pravý klik na **zložku** alebo archív › Bude to fungovať?
  - umu-launcher (Proton mimo Steamu) vo Fedore nie je. Zatiaľ ponúkne Wine z Fedory, Proton cez umu pridám
    s hernou vrstvou zo zdroja v resources.

### 24. 9. 2026, 19:50: plný App Manager — obchod a všetky aktualizácie ✅ (zadanie 24. 9. večer, časť 2)
- **Obchod** (namiesto krátkeho zoznamu), ako GNOME Software alebo Bazaar, z Flathubu:
  - úvodný banner s trendovou aplikáciou a jej snímkou;
  - kategórie (Hry, Internet, Hudba a video, Grafika, Kancelária, Vývoj, Vzdelávanie, Veda, Systém, Nástroje);
  - pásy Trendy, Obľúbené, Nové na Flathube, Nedávno aktualizované; na kartách je overený vývojár
    a inštalácie za mesiac;
  - **detail aplikácie:** snímky obrazovky, veľkosť na stiahnutie a po inštalácii, celkové inštalácie, verzia,
    licencia, popis a história verzií, tlačidlá Inštalovať / Otvoriť / Odinštalovať / Web;
  - hľadanie cez Flathub aj systémové balíky Fedory. Výber LatteOS ostal dole.
  - Popisy sú z Flathubu po anglicky, slovenské preklady Flathub neposkytuje. Bez internetu sa ukáže
    posledná známa ponuka (cache 6 h).
- **Aktualizácie v jednom zozname:**
  - **Systém** (dnf, teraz 373 balíkov);
  - **Aplikácie** (Flatpak);
  - **Súčasti LatteOS:** porovná nainštalovanú verziu s repozitárom a ukáže, čo je nové. Aktualizácia beží
    v Inštalátore s heslom, ako `git pull` a inštalácia;
  - **Ovládače a firmvér:** fwupd a grafika s odporúčaním (NVIDIA → akmod-nvidia, AMD/Intel sú v jadre,
    vo VM netreba nič).
- Pravý panel s detailom je iba pri Nainštalovaných a Oprávneniach, obchod má celú šírku.
- Poznámka: maskot je znova Ktulu. Ak si to prepol ty (pravý klik na maskota), je to v poriadku, nechal som ho tak.

### 24. 9. 2026, 19:20: App Manager — rýchle spustenie z rohu ✅ (zadanie 24. 9. večer, časť 1)
- **Klik na dlaždicu aplikácií** otvorí vyskakovacie okno nad ňou. Klik na aplikáciu ju spustí a okno zavrie,
  klik mimo alebo Esc ho zavrie. Písaním sa hľadá, Enter spustí prvý výsledok.
- **Vnútri ako v mobile:** často používané a všetky aplikácie v skupinách (LatteOS, Hry, Internet a komunikácia,
  Hudba a video, Grafika, Kancelária, Vývoj, Nástroje, Systém…), A–Z so skutočnými ikonami.
- **Záložka „Na pozadí“:** aplikácie z oblasti oznámení ako skryté ikony vo Win11 (Discord, Steam, KDE Connect…).
  Klik otvorí, pravý klik ukáže ich ponuku. Pod tým sú bežiace Flatpaky s tlačidlami Otvoriť a Ukončiť.
  Tray som z pravého ostrova lišty odstránil, aby nebol dvakrát.
- **📌 Pripnúť** (vpravo hore) aj tlačidlo **App Manager** dole otvoria plný App Manager ako klasické okno
  s – □ ✕. Kým je otvorený, klik na dlaždicu ho iba vytiahne dopredu.
- Spúšťač beží skrytý na pozadí, aby sa otváral hneď (latte-spustac, IPC Quickshellu).
- Ďalej: plný App Manager (lepší prehliadač aplikácií, aktualizácie systému, Flatpakov, LatteOS, ovládačov).

### 24. 9. 2026, 18:25: živá tapeta — video/GIF ako X Live Wallpaper, para zo šálky pri Mraze ✅ (bod 12)
- **Video alebo animácia ako tapeta:** MP4, WebM, MKV, GIF, WebP, bez zvuku, v slučke. Pri hre a okne na celú
  obrazovku sa pozastaví. Zapína sa v Nastaveniach › Animácie a efekty (pole s cestou) alebo v Súboroch:
  pravý klik na video › **Nastaviť ako živú tapetu**.
  - Vo VM (stupeň Softvér) ide **iba GIF/WebP**. Video potrebuje grafickú akceleráciu, preto sa nespustí
    a príde vysvetľujúce oznámenie (predtým by len pálilo 50 % CPU bez obrazu). GIF som overil, animuje sa.
- **Textúra naviazaná na tému:** pri **Mraze** stúpa **para zo šálky** na tapete, poloha šálky je pre každú
  tapetu LatteOS. Keď je logo šálky orezané pri hornom okraji, para ide zo skutočnej šálky v strede.
  Na výber je aj ručne („Para zo šálky“). Para je vždy biela, aby bola vidieť aj na tmavých zrnách.
- Živá tapeta je teraz vo vrstve tapety (nad tapetou Noctalie, pod ikonami plochy). Pri reštarte Noctalie
  sa sama preusporiada navrch.
- Živú tapetu som po teste znova vypol (tak ako bola).

### 24. 9. 2026, 18:20: Ktulu (Cthulhu mačka) a maskoti, čo utekajú ✅ (bod 11)
- **Ktulu:** zelenkavá mačka so žiariacimi očami a chápadlami pod bradou. Občas jej **z hrany lišty
  vyrastú chápadlá** a chvíľu sa vlnia. Nový maskot: pravý klik na maskota alebo Nastavenia › Lišta.
- **Útek:** keď si 5 minút preč (nepohneš myšou a nezmeníš okno), maskot po krokoch odíde z ostrova
  a vráti sa, keď sa vrátiš. Keď ho dlho nepohladkáš, občas sa znudí a odíde na chvíľku. Klik ho zavolá späť.
- **Vypnutie:** maskot „Žiadny“ skryje všetko. Samostatná voľba „Zostáva na lište“ vypne iba útek.
- Tvojho maskota som nechal na Latte mačke. Ktulu som vyskúšal a vrátil.

### 24. 9. 2026, 18:10: Monitor — Win11 Správca úloh + Autoruns + CPU-Z/HWiNFO ✅ (bod 10)
- **Prehľad (Výkon):** grafy procesora, pamäte, siete, **disku** a **grafiky** (keď ju ovládač hlási),
  súhrn ako vo Win11: rýchlosť procesora, procesy, vlákna, záťaž, doba behu, swap. Ďalej jadrá, disky a teploty.
- **Hardvér (nové):**
  - procesor: názov, jadrá/vlákna, frekvencia, rodina/model/stepping, mikrokód, cache L1d/L1i/L2/L3,
    inštrukcie (AVX2, AES…), virtualizácia;
  - doska a BIOS, UEFI, Secure Boot, pamäť, grafika s ovládačom, disky;
  - senzory (teploty, ventilátory, napätia, výkon), batéria so zdravím a cyklami, systém.
  - Tlačidlo „Kopírovať ako text“. Všetko bez práv správcu (typ RAM modulov by potreboval dmidecode).
- **Po štarte (Autoruns):** okrem autoštartu, služieb, časovačov a cronu aj **štart relácie LatteOS**,
  **prihlásenie a prostredie** (.bash_profile, environment.d) a **moduly jadra**. Položka, ktorej program
  neexistuje, je označená „⚠ súbor chýba“. Hľadanie v hlavičke filtruje zoznam.

### 24. 9. 2026, 18:00: greeter — Caps Lock, Num Lock, zobrazenie hesla, písma ✅ (bod 9)
- Pod heslom sa ukáže **„⇪ Caps Lock je zapnutý“** alebo **„Num Lock je vypnutý“**. Stav sa berie z LED
  klávesnice a zároveň z písaných znakov: veľké písmeno bez Shiftu znamená Caps Lock, kláves vpravo bez
  číslice znamená vypnutý Num Lock.
- **Oko** v poli hesla heslo ukáže alebo skryje.
- **Písma ako v systéme:** hodiny a dátum sú v Manrope ako na lište (predtým pätkové Fraunces). Nadpisy
  ostali vo Fraunces ako v aplikáciách. Uvidíš to pri najbližšom odhlásení.

### 24. 9. 2026, 17:55: Heidelberg ako plnohodnotný editor ✅ (bod 8)
- **Režim Dokument** (docx, odt, rtf, epub, html a každý nový dokument) je **WYSIWYG na strane papiera**:
  - písmo (výber s náhľadom v danom písme), veľkosť, **B** *I* U S, farby;
  - zarovnanie vľavo, na stred, vpravo a do bloku, nadpisy H1–H3, odrážky, číslovaný zoznam, citát;
    tlačidlo „Tx“ zruší formát.
- **Príprava na tlač:** strana A4/A5/Letter, na výšku alebo na šírku, okraje 15–30 mm, lupa Ctrl+/−,
  orientačné zlomy strán. **Ctrl+P = Tlačiť:** vyrobí PDF presne podľa strany a pošle ho na tlačiareň.
  Ak tlačiareň nie je (VM nemá CUPS), otvorí PDF v prehliadači.
  **PDF** robí weasyprint: prvýkrát tlačidlo „Doinštalovať PDF a tlač“ (Inštalátor). Vo VM som ho neinštaloval.
- **Kontrola textu (F7):** slovenský a anglický slovník (hunspell). Ukáže preklepy s návrhmi (klik = oprava
  všetkých výskytov), zdvojené slová, dvojité medzery a medzeru pred interpunkciou. Skratky a názvy ako
  LatteOS nehlási. Tlačidlo „Do slovníka“ ukladá do ~/.config/latteos/slovnik.dic.
- **Režim Text** (md, txt) zostáva: zdroj vľavo, náhľad vpravo. Ctrl+Shift+N = nová poznámka.
- **Pandoc a hunspell-sk** sú v základnej inštalácii. Export DOCX som overil pandocom.
- Obmedzenie: DOCX/ODT cez pandoc nezachovajú písma a farby. Presne ich zachová HTML (vlastný formát
  Heidelbergu) a PDF.

### 24. 9. 2026, 17:40: Súbory — Forklift a Total Commander, FTP/SFTP, Otvoriť v…, Kôš na ploche ✅ (bod 7)
- **Dva režimy** (tlačidlo v hlavičke):
  - **Forklift:** panel náhľadu sa dá skryť (Alt+P). **Zobrazenie ako vo Win11:** extra veľké, veľké, stredné
    a malé ikony (obrázky s náhľadom), zoznam, podrobnosti. Tlačidlo **+ Nový** vytvorí priečinok, textový
    súbor, dokument Heidelberg alebo prázdny súbor.
  - **Total Commander:** dva panely a lišta **F3 Zobraziť · F4 Upraviť · F5 Kopírovať · F6 Presunúť ·
    F7 Nový priečinok · F8 Do koša · F9 Server**.
- **FTP/SFTP:** „Pripojiť server…“ (F9) otvorí `sftp://meno@server` alebo `ftp://…` ako priečinok v ~/Siet
  (bočná lišta › Sieť, pravý klik = Odpojiť). Heslo ide iba cez stdin, SFTP bez hesla použije SSH kľúče.
  Otestované proti vlastnému SSH serveru VM (dočasný kľúč som potom z authorized_keys odstránil).
- **Otvoriť v…:** aplikácie pre typ súboru (predvolená, odporúčané), „Vždy otvárať v…“ a odporúčané
  aplikácie z App Managera na inštaláciu (napr. obrázok → GIMP, Krita). PDF v Heidelbergu zatiaľ nie
  (príde s bodom 8).
- **Kôš na ploche:** ikony na ploche (Kôš vždy, pod ním súbory z ~/Plocha). Súbor pretiahnutý na Kôš ide do
  koša, na koši je počet položiek. Dá sa vypnúť v Nastaveniach › Pozadie.
- **Oprava:** „Vysypať kôš“ a „Obnoviť“ nefungovali, lebo `gio` bez gvfs to nevie. Kôš teraz spravuje
  `latte-kos` podľa freedesktop, pôvodné miesto sa pri obnovení zachová.

### 24. 9. 2026, 17:25: Text Bar, AI cez prihlásenie, Bez AI ✅ (bod 5)
- **Text Bar** je širší riadok s textom. Ikona režimu je na okraji, režim sa mení **kolieskom** alebo
  **šípkami ‹ ›** (bodky ukazujú, kde si). Klik na text otvorí hľadanie v danom režime.
  **Pravý klik = rýchle nastavenia**: režim, kde beží AI, ktorá webová AI.
- **Odpoveď AI** z Text Baru: Enter ju otvorí vo **vyskakovacom okne** (panel AI) a **pripínačik 📌** z neho spraví
  samostatné okno „AI rozhovor“. Rozhovor pokračuje, panel aj okno ho zdieľajú.
- **AI cez prihlásenie** (ako widget Claude/ChatGPT v mobile): voľba „Prihlásenie v prehliadači“ otvorí otázku na
  claude.ai / chatgpt.com / perplexity / copilot, kde si prihlásený. Nepotrebuje žiadny kľúč.
- **Bez AI** (ako „No AI“ v LibreOffice) je v Baristovi, v Nastaveniach aj v rýchlych nastaveniach. Režim AI
  potom zmizne z Text Baru a panel Super+I nič neponúka.
- ⚠ **Tvoj kľúč Mistral** (Veľké AI) vracia chybu 401 „Invalid API Key“. Vymeň ho v Nastaveniach › AI, alebo
  prepni na Domáci server (LM Studio beží a odpovedá) či na prihlásenie v prehliadači. Nastavenie som ti nemenil.

### 24. 9. 2026, 17:15: ponuka šálky ✅ (bod 4)
- Navrchu je **účet**: meno, **typ účtu** (Správca / Štandardný) a hneď vedľa **Odhlásiť** a zámok. Pod tým
  **Nastavenia** a **Monitor**, **Rýchlo** (stupeň výkonu, režim okien, stav NORMAL/SAFE) a **Napájanie**.
- Rýchle voľby sa dajú skryť v Nastaveniach › Lišta a systémové menu. Tam sú aj „Ďalšie voľby lišty (Noctalia)“,
  teda bývalé „Nastavenia shellu“. Témy sú v Nastaveniach › Motív. App Manager a Správca zariadení už
  v šálke nie sú, majú vlastné ostrovy.

### 24. 9. 2026, 17:10: ovál okien vedľa šálky ✅ (bod 3)
- Ovál zrkadlí **otvorené okná ikonami aplikácií** (aplikácie LatteOS majú svoje glyfy). Aktívne okno je
  zvýraznené, minimalizované sú tlmené na konci. Na začiatku je ikona **režimu okien** (páska / dlaždice /
  plávajúce), klikom sa prepína.
- **Podržanie myši** nad ikonou ukáže **živý náhľad okna** nad kurzorom. Vo VM sa obnovuje 4× za sekundu,
  aby šetril CPU. Klik na ikonu alebo na náhľad prepne na okno a minimalizované vráti.
- **Pravý klik** otvorí ponuku okna ako vo Windows: prepnúť, minimalizovať/obnoviť, zväčšiť,
  plávať/ukotviť, presunúť na plochu 1–4, NET aplikácie, zavrieť.
- Oprava: aplikácie LatteOS pri zavretí z titulku (✕, Super+Q) nechávali bežať proces. Teraz skončia,
  Inštalátor počas inštalácie počká, kým dnf dobehne, a výsledok oznámi.

### 24. 9. 2026, 17:00: Kapsa podľa tvojho náčrtu ✅ (bod 6)
- **Široký kontajner vedľa hľadania:** vľavo **jamka (výrez)**, vpravo **8 slotov** schránky. Plný slot je v
  akcentovej farbe, prázdny sivý. Podržanie myši ukáže obsah, klik ho vytiahne navrch. Počet slotov určuje
  `~/.config/latteos/kapsa-sloty` (4–12).
- **Súbor pretiahnutý na jamku** v nej zostane: ikona podľa typu (Word, PDF, obrázok ako náhľad) je naklonená,
  **čiastočne zapadne do jamky a presahuje nad lištu**. Klik súbor otvorí, potiahnutím ho presunieš ďalej,
  pravým klikom ho vyberieš. Nová vec posunie predošlú do slotov.
- Technicky: Noctalia neprijme súbor z iného okna, preto jamku obsluhuje malá vrstva `latte-app kapsavyrez`.
  Kapsa preto sedí pri hľadaní, kde má stálu polohu; tú si zistí pri prvom prechode myšou nad Kapsou.

### 24. 9. 2026, 16:50: lišta — hodiny, zvonček, dátum s úlohami, App Manager, šálka ✅ (bod 2)
- **Ostrov Čas** má tri časti: **hodiny** · **zvonček s počtom nových oznámení** · **dátum s počtom úloh** („št 24. 9. (2)“).
  - Klik na hodiny: časové pásma, **stopky** (medzičasy), **minútka** (1/5/10/25 min alebo vlastná), **budíky**
    a počasie. Zvonia aj pri zatvorenom paneli, bežiace stopky a minútka sú vidieť na lište.
  - Klik na zvonček: **zoznam oznámení** priamo v našom paneli (nie v Noctalii) a Nerušiť. Pravý klik prepne Nerušiť.
  - Klik na dátum: kalendár, udalosti a **úlohy**. Úloha začínajúca „!“ sa naviaže na vybraný deň.
- **Panely sa otvárajú pri kliknutom ostrove.** Tvar L (panel zrastený s lištou) vyžaduje viditeľný pás lišty.
  Skúsil som ho, ale podľa teba ostávajú **ostrovy oddelené, len s menšími medzerami** (6 px namiesto 12).
  Panely preto „vyrastajú“ tesne nad svojím ostrovom.
- **Dlaždica aplikácií** = iba App Manager (spúšťanie je v Text Bare). App Manager sa otvorí vľavo dole
  nad dlaždicou, Správca zariadení vpravo dole. **Správca zariadení** je teraz úplne vpravo. **Šálka** je širšia.
- **Oprava NET:** pri Discorde klik na NET (tvoj o 16:06) nič nevypol, lebo trieda okna „discord“ ≠ Flatpak
  „com.discordapp.Discord“. Teraz sa trieda preloží na aplikáciu a pri neúspechu príde chybové oznámenie.
- **Kapsa (tvoj náčrt):** široký kontajner s 8 slotmi (plné/prázdne podľa histórie schránky), navrchu výrez
  priamo v okne, do ktorého čiastočne zapadne ikona odloženého súboru. Robím to ako bod 6.

### 24. 9. 2026, 16:10: jednotné okenné tlačidlá, NET až pri sieti, opravené portály ✅ (bod 1)
- **– □ ✕ všade:** okná bez vlastnej hlavičky (terminál, Qt/KDE, VLC…) dostanú titulok od kompozitora
  (plugin hyprbars, farby podľa témy a svetlého/tmavého režimu). GTK/GNOME aplikácie a Firefox majú vlastnú
  hlavičku, teraz tiež s – □ ✕ (predtým iba ✕). Aplikácie LatteOS majú rovnaké okrúhle tlačidlá.
  Minimalizovať = okno sa skryje (Super+N), späť Super+Shift+N; neskôr z oválu okien v lište (bod 3).
- **NET** sa ukáže, **až keď aplikácia otvorí spojenie von** (nie iba lokálne). Pri cudzích oknách je to malý
  znak v titulku vedľa – □ ✕, pri oknách s vlastnou hlavičkou (Firefox, Electron) prilepený jazýček nad
  horným okrajom okna. Klik vypne/zapne NET (platí od ďalšieho spustenia aplikácie).
- **Opravená chyba, ktorú nebolo vidieť:** portály (xdg-desktop-portal) sa v relácii vôbec nespúšťali.
  Flatpak aplikácie preto nemali výber súborov, zdieľanie obrazovky ani nastavenia systému. Relácia má
  teraz vlastný systemd target, ktorý sa spustí po štarte Hyprlandu a skončí s ním.
- Zostáva z bodu 1: vyskakovacie okná vyrastajúce z lišty (L-tvar) spravím spolu s bodom 2 (lišta).

### 24. 9. 2026, 15:30: grafický Inštalátor, Barista ukazuje inštaláciu, počasie v paneli Čas ✅
- **Inštalátor** (`latte-app instalator`) namiesto terminálu: názov a popis balíka, veľkosť, pole na heslo
  správcu (ide iba cez stdin do sudo), pruh priebehu s krokmi, log pod „Podrobnosti“. Zlé heslo ohlási
  hneď. Používa ho App Manager (inštalácia, odinštalovanie, Aktualizovať všetko, .rpm z „Bude to
  fungovať?“), Heidelberg (pandoc), jazyky a KDE Connect v paneli Čas.
- **Barista:** tvoje aplikácie sa **nainštalovali** (Firefox, VLC, Steam, Discord, z Flathubu o 15:04).
  Barista ich však inštaloval potichu až po zatvorení, takže to vyzeralo, že nič neurobil. Teraz
  inštaluje v poslednom kroku a pri každej aplikácii ukáže stav; ak ho zavrieš skôr, zvyšok dobehne
  na pozadí s oznámením. `latte-session` pripraví priečinok Flatpak spúšťačov, aby ich lišta videla hneď.
- **Počasie** v paneli Čas (teraz + 3 dni), poloha z Nastavení.
- Poznámka k Noctalii (Super+A): jej riadiace centrum má vlastné oznámenia, kalendár a počasie. Naše
  panely ich postupne nahradia; Super+A ostáva ako záloha, kým nebude hotový bod 2 zo zadania.

### 24. 9. 2026, 12:15: zvuk v Správcovi zariadení, strom procesov ✅
- **Správca zariadení › Zvuk:** výber predvoleného výstupu a mikrofónu, hlasitosť −/+, stlmenie a
  **hlasitosť jednotlivých aplikácií**, ktoré práve hrajú. Overené na tvojej relácii; hlasitosť som
  nemenil (ostala 40 %).
- **Monitor › Procesy › Strom:** procesy ako strom rodič → deti.

### 24. 9. 2026, 12:10: živá tapeta (pohyblivé textúry) ✅
- Z tvojho zoznamu „pohyblivé textúry“: **živá tapeta** nad tapetou, pod oknami, bez shaderov (beží aj
  pri softvérovom kreslení).
  - Podľa materiálu témy: Latte = **para** stúpajúca od šálky, Jantár = **bublinky**, Mráz = **sneh**,
    kovy = **iskry** (lesk prebehne cez plochu), drahokamy = **trblietky**, kameň = **prach**.
    Scénu si vieš aj vybrať.
  - Nedá sa na ňu kliknúť (kliky idú na plochu) a v hernom režime stojí.
  - Stojí asi 2 % jedného jadra, preto je vo VM predvolene vypnutá. Zapína sa v Nastaveniach ›
    Prostredie › Animácie a efekty.
  - Vyskúšal som sneh na tvojej relácii pár sekúnd a potom ho vypol. Screenshot:
    `setup/f1/results/f3-ziva-*.png`.
- Materiály priamo na paneloch a oknách (mráz na skle, kovový lesk) potrebujú shadery a GPU; počkajú na
  reálny HW.

### 24. 9. 2026, 12:00: Text Bar hľadá súbory, Heidelberg otvára Word/ODT ✅
- **Text Bar (Super+Medzerník)** v bežnom hľadaní ukazuje aj **súbory a priečinky** z tvojho domova
  (rýchlo cez index plocate). Klik otvorí súbor, pri priečinku Súbory.
- **Heidelberg** otvorí **.docx, .odt, .rtf a .epub**:
  - Upravujú sa ako Markdown s náhľadom a uložia sa späť do pôvodného formátu. Pri prvom uložení
    ostane originál ako `súbor~`, lebo zložité formátovanie Wordu sa zjednoduší.
  - Nové tlačidlá **Export: DOCX, ODT, EPUB, HTML**.
  - Nainštaloval som `pandoc-cli` (204 MB). Na PC bez neho Heidelberg ponúkne doinštalovanie.
  - Overené: otvorenie .docx, úprava, uloženie a znovu načítanie.

### 24. 9. 2026, 11:55: Cloud a synchronizácia ✅
- **Nastavenia › Dáta › Cloud a synchronizácia:** Google Drive, OneDrive, Dropbox, Nextcloud/WebDAV,
  domáci server cez SFTP a ďalšie (rclone):
  - „Pridať účet“ otvorí sprievodcu rclone (prihlásenie v prehliadači).
  - Účet sa pripojí ako priečinok **~/Cloud/<názov>**, voliteľne automaticky po prihlásení.
  - Pripojené účty sú v Súboroch v novej sekcii **Cloud**.
  - Overené na testovacom účte (pripojenie, čítanie, odpojenie), test som potom zmazal.
- Nainštaloval som `rclone` (Fedora, 109 MB).

### 24. 9. 2026, 11:50: greeter s počasím a novinkami, NET v hlavičkách, hľadanie všade ✅
- **Ľavý panel obrazovky prihlásenia** má teraz aj režimy **Počasie** (teraz + 3 dni, Open-Meteo bez
  účtu, mesto z Dátum, čas a poloha) a **Novinky (RSS)** (Aktuality.sk, STVR, Root.cz, Phoronix alebo
  vlastný odkaz). Prepína sa v Nastaveniach › Účet › Prihlasovanie; vo vývojárskej verzii ostáva
  predvolený log pádu. Screenshoty: `setup/f1/results/f1-greeter-pocasie.png`, `…-rss.png`.
  SELinux greeter na internet pustí (politika: `allow xdm_t port_type:tcp_socket name_connect`, overené
  cez sesearch). Bez siete panel napíše „bez siete?“.
- **Tlačidlo NET** v hlavičke každej aplikácie LatteOS teraz naozaj vypína internet (od ďalšieho spustenia).
- **Súbory:** Enter v hľadaní = **hľadať všade** (aj v podpriečinkoch), klik otvorí priečinok s nájdenou položkou.
- **Hra má prednosť:** hra z Herne dostane viac CPU (vlastný systemd scope) a profil Výkon; po hre sa všetko vráti.
- Nové kontroly bez obrazovky: `setup/f1/apps-check.sh` (8 aplikácií) a `setup/f1/plugins-check.sh`
  (11 pluginov), oba prešli bez chýb. Prehľad komponentov: `session/README.md`.

### 24. 9. 2026, 11:55: F6 — NET pre každú aplikáciu ✅
- V **App Manageri › Oprávnenia a NET** má každá aplikácia vypínač internetu. Doteraz to fungovalo iba
  pre Flatpak, teraz aj pre bežné aplikácie:
  - Vypnutím vznikne prekrytie spúšťača a aplikácia beží v **bubblewrape bez siete**. Okno, zvuk a
    schránka fungujú, internet nie.
  - Overené: okno sa otvorilo, sieť nebola dostupná.
  - Platí pre každé spustenie z LatteOS (lišta, Text Bar, App Manager). Aplikácia spustená ručne z
    terminálu sieť má; na to bude treba systémovú službu s firewallom (zapísané v ROADMAP).
- Windows hry (Proton) prídu s hernou vrstvou.

### 24. 9. 2026, 11:40: Herňa, Používatelia ✅
- **Super+G = Herňa:** knižnica hier zo **Steamu** (aj Flatpak verzie) a **Heroicu** (Epic, GOG, Amazon)
  s obalmi a filtrom. Klik spustí hru v **hernom režime** a po zatvorení hry sa efekty vrátia.
  Zatiaľ je prázdna (Steam nie je nainštalovaný), tlačidlo vedie do App Managera. Overené s
  napodobeninou Steam knižnice.
- **Nastavenia › Účet › Používatelia:** účty s obrázkom a rolou (správca/bežný). Pridať a odstrániť
  účet sa dá v termináli so sudo, aby bolo vidieť, čo sa deje.

### 24. 9. 2026, 09:15: Barista, Jazyk a región, Zálohovanie ✅
- **Barista**, sprievodca prvým spustením. Kroky: Vitaj → Vzhľad (všetkých 14 tém + svetlá/tmavá/podľa
  slnka) → Okná → Lišta a maskot → AI → Aplikácie (inštalujú sa z Flathubu na pozadí) → skratky.
  **Pri tvojom ďalšom prihlásení sa raz ukáže**; kedykoľvek ho spustíš znova z Text Baru („Barista“).
- **Nastavenia › Systém › Jazyk a región:** jazyk a formáty (dátum, čísla, meny) pre tvoj účet. Chýbajúci
  jazyk sa doinštaluje v termináli. Pozor: shell Noctalia nemá slovenský preklad (texty lišty od
  Noctalie sú anglicky), naše pluginy a aplikácie sú po slovensky.
- **Nastavenia › Dáta › Zálohovanie a obnova** (`latte-backup`):
  - Záloha domova na USB disk (objaví sa sám) alebo do priečinka, „Zálohovať teraz“ s priebehom,
    voliteľne denne automaticky.
  - Každá záloha vyzerá ako celá kópia, nezmenené súbory sa ukladajú iba raz (overené), drží sa 14
    najnovších.
  - Obnova: tlačidlo Otvoriť ukáže zálohu v Súboroch.

### 24. 9. 2026, 09:00: Môj účet, Kôš, Heidelberg ✅
- **Nastavenia › Účet › Môj účet:** meno, zmena hesla a **obrázok účtu**. Vyberieš si maskota LatteOS
  alebo obrázok z priečinka Obrázky. Obrázok sa ukáže aj na **obrazovke prihlásenia** v karte
  posledného účtu.
- **Súbory:**
  - **Kôš** je v Obľúbených s počtom položiek. Pravý klik na položku v koši ponúkne Obnoviť na pôvodné
    miesto alebo Odstrániť natrvalo, na koši Vysypať.
  - **F5 kopíruje s priebehom** (percentá a pruh v stavovom riadku, nič neprepíše).
- **Heidelberg**, editor dokumentov z tvojich nápadov (`old/IDEAS.md`):
  - Markdown, HTML a text s **živým náhľadom** vedľa editora.
  - Tlačidlá B, I, Nadpis, Zoznam, Citát, Kód a Odkaz; Ctrl+S uloží (nový dokument ide do
    ~/Dokumenty); nedávne dokumenty, hľadanie v texte, počet slov.
  - Je predvolený pre .md súbory. Otvorenie, úprava a uloženie sú overené.
  - rtf, odt, docx, epub a PDF prídu neskôr (cez pandoc).
- Systémové menu (šálka) má teraz aj Aplikácie a Správcu zariadení.

### 24. 9. 2026, 08:45: okná a Nastavenia doplnené ✅
- **Super+Z = rozloženie okna** ako vo Windows 11: mini obrazovky (polovice, štvrtiny, tretiny, stred,
  celá plocha). Klik presunie aktívne okno a lište nechá miesto. Overené na tvojej relácii.
- **Gestá 4 prstami:** hore = prehľad pásky, dole = prázdna plocha.
- **Tapeta podľa plochy** (voliteľné, Nastavenia › Pozadie). Predvolene je vypnutá, lebo každá zmena
  tapety stojí CPU.
- **Super+L** zamyká. Menu ho ukazovalo, ale skratka chýbala.
- Nové stránky v **Nastaveniach**:
  - **Klávesnica a skratky:** zoznam všetkých skratiek LatteOS.
  - **Oznámenia:** Nerušiť, poloha, počet naraz, obsah, test.
  - **Prístupnosť:** mierka rozhrania 100–150 %, vysoký kontrast, bez animácií (platí aj po hernom
    režime), veľkosť kurzora.
  - **Uzamknutie a nečinnosť:** zamknúť, vypnúť obrazovku a uspať po čase.
- Opravené tlačidlá +/− v Nastaveniach (odkazovali samy na seba, preto boli bledé).
- Pri teste som na chvíľu zapol animácie v tvojej relácii; `hyprctl reload` to hneď vrátil.

### 24. 9. 2026, 08:25: prehľad pásky, Kapsa, AI rozhovor ✅
- **Super+Tab = prehľad pásky:** všetky okná po plochách v poradí pásky. **Píš a filtruje**, Enter
  zameria prvé nájdené okno, klik zameria okno. Prepínač Noctalie ostal na Super+Shift+Tab.
- **Kapsa** (schránka, podľa radaru):
  - Na lište je **jediná odložená vec** navrchu (skrátená).
  - Klik otvorí kapsu: „Navrchu“ a pod tým sloty histórie (text aj obrázky). Klik na slot ho vytiahne
    navrch, × ho vyhodí, „Vysypať“ vymaže všetko.
  - Beží na cliphist a nahrádza ikonu schránky Noctalie.
  - Drag and drop do kapsy zatiaľ nie je: Noctalia nevie prijať súbory pretiahnuté z okien.
- **AI rozhovor (Super+I):**
  - Panel s bublinami, AI si pamätá predošlé správy, odpovede sú v markdowne.
  - Overené s tvojím LM Studio. Prvý pokus zlyhal na skrytom 5-sekundovom limite príkazov v Noctalii;
    chat teraz ide cez stream bez limitu.
  - Model si najprv vymyslel, že LatteOS je pre IoT 😄, preto dostal krátky popis LatteOS v
    systémovom prompte.
- Pri inštalácii nových pluginov treba reštartovať shell (Noctalia registruje nové panely iba pri štarte).
  Reštartoval som ho v tvojej relácii 3× na pár sekúnd; inštalátor na to teraz upozorní.

### 24. 9. 2026, 08:20: Monitor, Aplikácie, Správca zariadení ✅ (podľa starých dokumentov)
Prečítal som staré dokumenty (`old/IDEAS.md`, `old/main_setting_v2.md` §63–64, `old/docs/nastavenia.md`,
`old/docs/lista-a-rohy.md`). Nové prototypy na spoločnej kostre aplikácií:
- **Monitor** (Process Manager, **Ctrl+Shift+Esc**):
  - živý stav s grafmi (CPU, jadrá, RAM, sieť, disky, teploty),
  - **procesy** podľa druhu: aplikácia (má okno), prostredie (lišta, kompozitor, zvuk), pomocný, systém.
    Ukončiť a Vynútiť sa potvrdzujú druhým klikom a pri procesoch plochy je varovanie. Systémové procesy
    ukončí iba správca. Pravý klik otvorí ponuku.
  - **Po štarte:** XDG autostart, služby tvojho účtu, časovače, systémové služby a cron, s pôvodom a
    príkazom. Položky tvojho účtu sa dajú vypnúť jedným klikom.
  - **Telemetria** pre OLED displej chladenia a Stream Deck: `$XDG_RUNTIME_DIR/latteos/telemetry.json`.
- **Aplikácie** (App Manager), pravý klik na dlaždicu aplikácií na lište:
  - **Objavovať:** Flathub a Fedora, odporúčané Základ / Hry / Tvorba / Komunikácia a čas: Firefox, VLC,
    LibreOffice, Kalkulačka, Steam, Heroic, GZDoom, Quake II, GIMP, Krita, OBS, Kdenlive, Discord,
    Signal, Planify (úlohy), Kalendár. ID som overil na Flathube.
  - **Aktualizácie:** dnf aj Flatpak, „Aktualizovať všetko“.
  - **Nainštalované:** zdroj, veľkosť, odinštalovanie.
  - **Oprávnenia a NET:** Flatpak aplikácii vypneš internet jedným klikom (prvý kus F6).
  - **„Bude to fungovať?“** pre .rpm, .flatpakref, .AppImage, .exe, .apk a .deb. Dostaneš verdikt s
    dôvodmi (napr. .exe potrebuje Proton, .apk Waydroid, ktorý vo VM nepôjde). Je to aj v pravom kliku v
    Súboroch a App Manager je predvolená aplikácia pre tieto typy súborov.
  - Nainštaloval som **Flatpak** a pridal Flathub pre tvoj účet (inštalácia bez hesla, v izolácii).
- **Správca zariadení:**
  - Dlaždice po skupinách (veľká ikona v zaoblenom štvorci). Zariadenie je vždy v jednej skupine
    (USB myš je Vstup, nie USB).
  - **Obrazovky:** rozlíšenie a mierka, zmena sa vráti, ak ju do 15 s nepotvrdíš (Enter / Esc).
    Overené na tvojej relácii: 1600×900 a späť.
  - Poznámka: VM má výšku 967 px (prvočíslo), preto sa dá iba mierka 100 %; na reálnom monitore
    budú aj 125/150 %.
- Nastavenia › Softvér a Hardvér ukazujú stav a tlačidlo do príslušného manažéra, takže každá funkcia
  má jednu implementáciu (pravidlo zo starej špecifikácie).
- Screenshoty: `setup/f1/results/f4-monitor-*.png`, `f4-aplikacie-*.png`, `f4-zariadenia.png`.

### 24. 9. 2026, 07:50: F5, OOM politika ✅ a oprava inštalátora
- Pri nedostatku pamäte padne najprv **aplikácia**, nie lišta ani celá plocha (nápad z Ubuntu 26.10,
  `session/oom/`). Okná aplikácií dostanú +300, Hyprland a Noctalia ostávajú na 0, dbus, PipeWire a
  portály majú −500. Overené na tvojej relácii: nový terminál mal 300.
- **Chyba, ktorú som spravil:** inštalátor prepisoval súbory Lua modulu po jednom a tvoj bežiaci
  Hyprland sa pri zmene sám znovu načítal práve vo chvíli, keď `latte/mode.lua` chýbal. Prešiel do
  núdzového režimu (červený rámik hore, skratky iba Super+Q/R/M). Spravil som `hyprctl reload` a chyba
  zmizla. Inštalátor teraz vymieňa konfigurácie atomicky (dočasný súbor a premenovanie), takže sa to
  nezopakuje.

### 24. 9. 2026, 07:45: lišta: čas a dátum, dlaždica aplikácií, maskot ✅
- **Ostrov času:** na lište je čas aj dátum (`07:45 · št 24. 9.`). Klik otvorí panel s tromi záložkami:
  - **Čas:** veľké hodiny, dátum, týždeň, **časové pásma** (vyberieš v Nastaveniach).
  - **Oznámenia:** Nerušiť, história, **oznámenia z mobilu** cez KDE Connect (Android; iPhone
    obmedzene). KDE Connect nie je nainštalovaný, rozhodnutie je nižšie.
  - **Kalendár:** mesiac, **vlastný plánovač** udalostí s pripomenutím v čase udalosti, napojenie na
    Google Kalendár, iCloud, CalDAV (Nextcloud) a ICS odkazy (Outlook, Proton, Todoist, TickTick,
    Microsoft To Do). To poskytuje kalendár Noctalie, netreba písať vlastných klientov.
  - Pravý klik na čas otvorí rovno Kalendár.
- **Dlaždica aplikácií** podľa starej verzie (`old/docs/lista-a-rohy.md`): široká, bez textu, ikona nad
  pokojnou textúrou **Para** alebo **Matrix**. Klik otvorí spúšťač, pravý klik App Manager. Pohyb je
  najviac 10 obr/s a vo VM beží iba pod kurzorom (šetrí CPU); dá sa zmeniť v Nastaveniach › Lišta.
- Screenshoty: `setup/f1/results/f3-cas-*.png`, `f3-lista-v3.png`, `f3-nast2-lista.png`.

### 24. 9. 2026, 07:35: Nastavenia s kartami, AI, greeter, štítky v Súboroch ✅
- **Nastavenia** majú **vrstvené karty** ako v starej verzii (`old/main_setting_v2.md`):
  - Softvér · Dáta · Hardvér · Účet · Prostredie + Systém. Vždy je otvorená jedna karta, ostatné sú
    zmenšené „chrbty“ so súhrnom a stavom (● hotové, ◐ časť, ○ plán). Hlavné karty sa neposúvajú.
  - Domov je stavový prehľad (režim, grafika, disk, AI, téma, účet) a ukazuje nedávno použité stránky.
  - Nové stránky:
    - **AI**, **Úložisko**, **Diagnostika a pády** (log posledného pádu),
    - **Prihlasovanie** (greeter), **Motív** (svetlá/tmavá/auto), **Lišta** (hrúbka, šírka cez
      odsadenie od okrajov, odsadenie od spodku, medzery),
    - **Dátum a čas** (poloha, časové pásma), **O LatteOS**.
  - Plánované stránky ukážu, čo na nich bude.
- **AI** (`latte-ai`, Nastavenia › Softvér › AI, Text Bar /ai):
  - Kde beží AI: **tento počítač** (Ollama), **domáci server** (OpenAI API; predvolene tvoje LM Studio
    `http://192.168.56.1:1234`, voliteľne cez **SSH tunel** `pouzivatel@server`), alebo **veľké AI**
    v cloude (Claude, ChatGPT, Gemini, Mistral s API kľúčom, uložený s právami 0600).
  - Modely zo servera sa dajú vybrať kliknutím, pri každom je, či je načítaný. **Overené s tvojím LM
    Studio:** model `qwen3-4b-thinking` odpovedal „Hlavné mesto Slovenska je Bratislava.“ (~30 s,
    načítanie modelu).
  - Poznámka: LM Studio sám nič nenačíta. Text Bar použije model, ktorý máš načítaný, alebo ten,
    ktorý vyberieš v Nastaveniach.
- **Greeter:**
  - Nad menom sú **posledné dva prihlásené účty** na klik.
  - Vľavo je panel s **prvým logom z posledného pádu**: `latte-session` ho po páde zapíše do
    `/var/lib/latteos/greeter/last-crash.log`.
  - V Nastaveniach › Účet › Prihlasovanie sa dá prepnúť na **vlastný text** alebo **nič**; neskôr tu
    bude RSS, novinky a počasie.
  - Pozadie (tapeta alebo iba farba), farba a stmavenie sa nastavujú v Nastaveniach.
  - Screenshot: `setup/f1/results/f1-greeter-v2.png`, v teste bola ukážka logu, potom zmazaná.
- **Súbory:**
  - **Pravé kontextové menu:** Otvoriť, Otvoriť v druhom paneli, **Farba**, Premenovať, Kopírovať cestu,
    Do Obľúbených, Terminál tu, Do koša. Na prázdnom mieste: Nový priečinok, skryté súbory, Terminál.
  - **Farebné štítky** priečinkov: plná ikona v zázname aj v Obľúbených a bodka za názvom. Farba nie je
    jediný nosič, ikona sa zmení aj tvarom.
  - Vlastné Obľúbené cez pravý klik.
  - Screenshot: `setup/f1/results/f4-subory-menu.png`.

### 23. 9. 2026, 22:05: Zariadenia (riadiace centrum, plugin) + herný režim ✅
- `session/noctalia/plugins/devices/`: ikona na lište (pomaly sa strieda sieť, zvuk, ovládanie), klik
  otvorí **Zariadenia** podľa návrhu:
  - stupeň výkonu, dlaždice Sieť/Wi-Fi, Bluetooth, Nerušiť, Nočné svetlo,
  - posuvníky hlasitosti a jasu,
  - **herný režim** (vypne efekty, medzery, rohy a animácie; po vypnutí sa vráti stupeň), profil výkonu,
  - HDR/VRR/limit FPS sú sivé s poznámkou „na reálnom HW“, NET podľa aplikácií je „pripravujeme“.
- Herný režim je v Lua module ako `latte.game(true|false)` a prežije reload.
- Otestované v headless labwc aj s celou lištou LatteOS: `setup/f1/results/f3-zariadenia.png`.

### 23. 9. 2026, 22:00: Nastavenia LatteOS (aplikácia) ✅
- `session/apps/nastavenia.qml` (spúšťa `latte-app nastavenia [sekcia]`, systémové menu, Text Bar), na tej
  istej kostre ako Súbory, **presne podľa tvojho návrhu V2**:
  - vľavo sekcie s bodkou stavu (plná = hotové, prázdna = plán),
  - v strede nadpis Fraunces, úvod a karty,
  - vpravo **Stav · Oblasť · Uložené v**.
- Hotové sekcie:
  - **Domov:** režim, grafika, stupeň, téma, okná, pády,
  - **Vzhľad:** 14 tém ako karty, tapety s náhľadom,
  - **Okná:** páska / dlaždice / plávajúce,
  - **Výkon:** Automaticky / Plný / Štandard / Úsporný / Minimálny / Softvér,
  - **Štart a prihlásenie:** ďalší štart NORMAL/SAFE, počítadlo pádov s vynulovaním, typ greetera.
- Sekcie Softvér, Dáta, Zariadenia, Účet a Súkromie/NET sú zatiaľ „Zatiaľ len plán“ s odkazom na manažéra.
- Pôvodné nastavenia Noctalie ostali dostupné ako **„Nastavenia shellu“**.
- Screenshoty: `setup/f1/results/f3-nastavenia-*.png`.

### 23. 9. 2026, 21:55: F4, Súbory (Data Manager), prototyp ✅
- Podľa tvojho návrhu V2 (`inspo/forklift vzhlad.png`) a Forkliftu. **Spoločná kostra aplikácií**
  (`session/apps/common/`):
  - bočná lišta od vrchu až dole s rozkladacími sekciami,
  - hlavička ‹ › · názov · nástroje · hľadanie · **NET** · zavrieť,
  - farby z aktívnej témy (pri `latte-theme set` sa aplikácia prefarbí za behu), ikony Tabler ako v shelli.
- **Súbory** (`session/apps/subory.qml`, spúšťa sa `latte-app subory`, Super+E, tlačidlo na lište, Text Bar):
  - **Tento počítač:** disky z `lsblk` (voľné miesto, pruh využitia, USB). Obľúbené, Aplikácie (Flatpak
    priečinky, .desktop) a Systém Linux (/, /etc, pripojené médiá). Skutočná štruktúra ostáva, nič sa neskrýva.
  - Stĺpce Názov/Upravené/Veľkosť/Druh s triedením a slovenskými druhmi súborov, história ‹ ›, hľadanie.
  - **Dva panely** (F3, štýl Total Commander): F5 kopírovať, F6 presunúť, Tab prepína panel.
  - **Detail vpravo:** náhľad obrázka, veľkosť, dátum, cesta; akcie Otvoriť, Kopírovať cestu, Do koša
    (potvrdenie druhým stlačením).
  - Pamätá si dva panely a cesty (`~/.config/latteos/subory.json`). Je predvolený pre priečinky (`xdg-mime`).
- Chyba, ktorú som našiel: v QML sa vlastnosť `onSurface` berie ako obsluha signálu (vyšla čierna),
  premenované na `fg`/`fgDim`.
- Testované bez obrazovky VM cez `setup/f1/headless.sh` (labwc headless + pixman). Screenshoty:
  `setup/f1/results/f4-data-*.png`.
- NET prepínač v hlavičke je zatiaľ iba vizuál (bezpečnostný model F6).

### ⚠️ 21:40: Pády Hyprlandu vo VM (llvmpipe + vmwgfx)
- Hyprland (sw-gl) spadol **2×** (21:06 a 21:40) v softvérovom rasterizéri Mesa (`lp_rast_shade_*`).
  Oba razy tesne predtým jadro hlásilo `vmwgfx: vmw_msg_ioctl … Failed to open channel`. To je kanál
  VMware k hostiteľovi, ktorý VirtualBox nemá; volá ho ovládač Mesa `svga`. Potom ostal `vmwgfx`
  v zlom stave (GBM nevie alokovať buffer) až do reštartu.
- Umelo sa to vyvolať nepodarilo (100 cyklov otvárania okien, 12× Quickshell a panely Noctalie).
- **Zmiernenie:** ak Hyprland spadne po 60 s, `latte-session` ho spustí znova (najviac 3× za 10 minút,
  potom SAFE). Overené skutočným SIGSEGV. Aplikácie LatteOS vo VM kreslia Qt softvérovo (`latte-app`).
- Rozhodnutie nižšie (vypnúť 3D vo VirtualBoxe?).

### 23. 9. 2026, 21:35: F3, 14 tém LatteOS ✅ (materiály zatiaľ bez animácie)
- `session/themes/make-themes.py` vygeneruje **14 tém** podľa návrhu (farby vytiahnuté z náhľadov):
  Latte, Mráz, Brúsený hliník, Striebro, Zlato, Biely onyx, Onyx, Jantár, Rubín, Zirkón,
  Klasik – kancelária / herný launcher / svetlé sklo, Úsporná (FPS).
- Každá téma má paletu Noctalie, svetlý alebo tmavý režim, farbu okrajov okien v Hyprlande a voliteľne
  tapetu. Témy bez efektov (Úsporná, klasické) obmedzia aj efekty kompozitora.
- Prepínanie: `latte-theme set rubin`, v Text Bare „téma …“ alebo v systémovom menu → Téma.
  Overené naostro (Rubín, Kancelária, späť Latte).
- **Pohyblivé materiály** (mráz, ktorý rastie a topí sa pod myšou, odlesk kovu, žilky kameňa, iskrenie
  fazety, rozpad okna) zatiaľ **nie sú**. Potrebujú shadery vo vlastnom forku Noctalie (C++/GLES)
  a pluginy Hyprlandu pre okná. Vo VM by aj tak išli iba pri vynútenom stupni Plný. Téma má na ne
  pripravený kľúč `material`.

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

## Staršie odpovede (23. 9.)

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

## Čaká na tvoje rozhodnutie

- **Licencia LatteOS** (repozitár nemá LICENSE). Ak ju nechceš riešiť hneď, najjednoduchšie je GPL-3.0 alebo AGPL-3.0 celého projektu — potom sa s prevzatým serpantinum (AGPL) nič nebije. MIT/Apache by znamenali, že PohodaView.qml ostane výnimkou pod AGPL.

1. **Vypnúť 3D akceleráciu vo VirtualBoxe?** (Nastavenia VM → Obrazovka → „Zapnúť 3D akceleráciu“.)
   LatteOS vo VM aj tak kreslí softvérovo; so zapnutým 3D Mesa občas siahne na `svga` a kernel hlási
   `vmw_msg_ioctl Failed to open channel` (aj dnes ráno 4×). Odporúčam **vypnúť**.
2. **KDE Connect pre oznámenia z mobilu?** (čo dá: pozri „Zadanie 24. 9. popoludní“) Balík `kde-connect` z Fedory stiahne časť knižníc KDE
   (~150 MB). Alternatíva bez KDE je `valent` (GTK, menej zrelý). Nenainštaloval som nič; tlačidlo je
   v paneli Čas › Oznámenia.
3. **Cloudové AI:** ak chceš Claude, ChatGPT alebo Gemini, vlož API kľúč v Nastaveniach › Softvér › AI.
   Kľúč nikam neposielam, uloží sa iba do `~/.config/latteos/ai-keys`.
4. **Test zaplnenia RAM (F5):** OOM politika je nastavená a overená na skóre (okná +300, Hyprland a
   Noctalia 0). Samotný test („aplikácia zje všetku pamäť, relácia musí prežiť“) som na tvojej živej
   relácii nespustil: ak by systemd-oomd zabil celú reláciu, grafika VM sa môže znova dostať do stavu,
   ktorý treba riešiť reštartom. Mám ho spustiť, keď budeš pri PC? (`setup/f1/stress.sh` + sledovanie)
5. **Poradie ostrovov na lište:** maskot je vpravo pred schránkou a zvonček ostal v ostrove času.
   Chceš to inak?

Vybavené (24. 9.): distribúcia balíkov počká na HW a Atomic · AI ide cez tvoje LM Studio · režim okien
ostáva páska, ostatné sa prepnú z menu.
