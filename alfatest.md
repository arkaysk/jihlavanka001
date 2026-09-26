# Alfatest 2: Nastavenia LatteOS verzus Windows 11

26. 9. 2026 · porovnanie s Windows 11 25H2 (aplikácia Nastavenia vrátane novej stránky **Systém › Pre pokročilých**
a klasického okna **Rozšírené nastavenia systému**) · stav repozitára po commite 42182d2.

**Značky:**
- ✅ funguje priamo na stránke;
- 🔗 stránka je iba odkaz („Otvoriť …“) do inej aplikácie;
- ⚠ zle zaradené;
- ♊ duplicitné;
- ❌ chýba.

## 1. Čo má Windows 11

**11 kategórií:** Systém · Bluetooth a zariadenia · Sieť a internet · Prispôsobenie · Aplikácie · Kontá · Čas a jazyk ·
Hry · Prístupnosť · Súkromie a zabezpečenie · Windows Update.

**Systém › Pre pokročilých** (25H2, predtým „Pre vývojárov“):
- Panel úloh: Ukončiť úlohu pravým klikom.
- Prieskumník: prípony súborov, skryté a systémové súbory, celá cesta v titulku, prázdne jednotky, dlhé cesty,
  integrácia so správou verzií (Git).
- Virtuálny pracovný priestor: Vzdialená plocha, virtuálne pracovné priestory.
- Terminál: predvolený terminál, spúšťanie skriptov PowerShell, **sudo**.
- Pre vývojárov: režim vývojára (aplikácie z ľubovoľného zdroja), Device Portal, Dev Drive.

**Klasické Rozšírené nastavenia systému:** výkon (vizuálne efekty, **virtuálna pamäť**), používateľské profily,
spustenie a obnovenie, **premenné prostredia**, ochrana systému (body obnovenia), vzdialený prístup.

## 2. Nálezy v LatteOS

### 2.1 Nedokončené: 12 stránok je iba odkaz 🔗
Aplikácie, Inštalácia aplikácií, Aktualizácie, Spúšťanie a na pozadí, Súkromie a NET, Obrazovky, Zvuk, Sieť,
Bluetooth a periférie, Úložné zariadenia, Tlač a skenovanie, Napájanie.
- Na každej je iba veta a tlačidlo „Otvoriť Správcu zariadení / Aplikácie / Monitor“.
- Windows má na týchto stránkach priamo ovládanie (hlasitosť a výstup, Wi-Fi, párovanie, rozlíšenie, režim napájania…).
- **Náprava:** stránky dostanú rovnaké ovládanie ako nový Správca zariadení (zdieľané komponenty, jedna implementácia).
  Tlačidlo „Otvoriť v Správcovi zariadení“ ostane iba ako cesta k ovládačom.

### 2.2 Duplicitné ♊
| Čo | Kde všade | Windows | Návrh |
|---|---|---|---|
| Úložisko | Dáta › Úložisko **a** Hardvér › Úložné zariadenia | Systém › Úložisko (disky sú v Rozšírených nastaveniach úložiska) | jedna stránka Úložisko: obsadenie + disky a oddiely |
| App Manager | Aplikácie, Inštalácia aplikácií, Aktualizácie (3 odkazy na jednu aplikáciu) | Aplikácie › Nainštalované; Windows Update zvlášť | Aplikácie (nainštalované, inštalácia) + Aktualizácie ako samostatná oblasť |
| Mierka | Prístupnosť (veľkosť rozhrania), Písmo a mierka, Obrazovky | Obrazovka › Mierka; Prístupnosť › Veľkosť textu | mierka obrazovky iba v Obrazovke; v Prístupnosti veľkosť textu |
| Tapety | Pozadie **a** Tapety online | jedna stránka Pozadie | Tapety online ako sekcia Pozadia |
| Bezpečnosť | Softvér › Súkromie a NET, Účet › Heslo a zabezpečenie, Systém › Bezpečnosť | Súkromie a zabezpečenie (celé na jednom mieste) | jedna oblasť Súkromie a zabezpečenie |
| Prihlásenie | Účet › Prihlasovanie (greeter), Uzamknutie a nečinnosť, Heslo a zabezpečenie | Kontá › Možnosti prihlásenia | jedna stránka Prihlásenie a uzamknutie |
| Sieť | Hardvér › Sieť, Systém › Zdieľanie, karta Siete v Správcovi zariadení | Sieť a internet | jedna oblasť Sieť a internet (Wi-Fi, VPN, zdieľanie, firewall) |

### 2.3 Zle zaradené ⚠
- **Hry a herný režim** sú pod Hardvérom (Windows: samostatná kategória Hry).
- **Diagnostika a pády** sú pod Hardvérom (Windows: Systém › Riešenie problémov a Obnovenie).
- **Oznámenia** sú pod Prostredím (Windows: Systém › Oznámenia).
- **Súkromie a NET** je pod Softvérom (Windows: Súkromie a zabezpečenie › Povolenia aplikácií).
- **Cloud a synchronizácia** je pod Dátami (Windows: Kontá › Zálohovanie a e-mailové kontá).
- **Okná** (režimy okien) sú pod Prostredím (Windows: Systém › Multitasking).
- **Štart a režim** (NORMAL/SAFE, počítadlo pádov) je iba v Systéme (Windows: Obnovenie › Rozšírené spustenie).

### 2.4 Chýba oproti Windows 11 ❌
- **Systém:**
  - Schránka (história, počet slotov Kapsy, vymazať);
  - Multitasking (prichytávanie okien k okrajom a lišta rozložení zapnúť/vypnúť, Alt+Tab);
  - Nerušiť a zameranie (je iba v Oznámeniach);
  - Premietanie a vzdialená plocha;
  - Riešenie problémov (sprievodcovia: zvuk, sieť, tlačiareň);
  - Obnovenie (príde s Atomic).
- **Bluetooth a zariadenia:**
  - Kamery (výber, rozlíšenie);
  - **Automatické prehrávanie** (čo sa stane po vložení USB kľúča, SD karty, telefónu: otvoriť Súbory, importovať fotky, nič);
  - USB (upozornenia na problémy);
  - Mobilné zariadenia (KDE Connect je iba v Zdieľaní);
  - Pero a dotyk.
- **Prispôsobenie:**
  - Písma (inštalácia a prehľad písem);
  - vzhľad uzamknutej obrazovky;
  - Štart (App Manager: pripnuté, často používané, skryť odporúčané).
- **Aplikácie:**
  - voliteľné súčasti;
  - aplikácie pre webové stránky (odkazy otvára aplikácia);
  - prehrávanie videa.
- **Kontá:** e-mail a kontá (Google, Microsoft, Nextcloud pre kalendár a poštu), rodina (detský účet, čas pred obrazovkou).
- **Čas a jazyk:** Písanie (automatické opravy, návrhy, emoji), Reč (diktovanie príde s AI).
- **Hry:** Zachytávanie (priečinok snímok a nahrávok, kvalita, spätný záznam na GPU).
- **Prístupnosť:**
  - lupa;
  - farebné filtre (aj pre farboslepých);
  - kontrastné motívy;
  - čítačka (Moderátor → Orca);
  - titulky;
  - prilepené klávesy;
  - veľkosť a farba ukazovateľa a textového kurzora.
- **Súkromie a zabezpečenie:** povolenia pre kameru, mikrofón, polohu, oznámenia, súbory; diagnostika; história aktivít.
- **Aktualizácie:** história, pozastaviť, aktualizácie ovládačov a firmvéru (fwupd), plán reštartu.
- **Pre pokročilých** (Windows 25H2 plus klasické okno):
  - Ukončiť úlohu na lište;
  - Súbory: prípony, skryté súbory, celá cesta v titulku;
  - predvolený terminál;
  - sudo (či sa pýta heslo);
  - **premenné prostredia**;
  - **virtuálna pamäť** (swap a zram);
  - režim vývojára (zdroje aplikácií: Flathub, COPR, AppImage);
  - SSH server;
  - vzdialená plocha.
  - Nemá zmysel: dlhé cesty, PowerShell, Dev Drive.

### 2.5 Čo má LatteOS navyše (ostáva)
AI, NET pre aplikácie, textúry a okná v tvare L, maskot, profily ovládania, stupne výkonu, NORMAL/SAFE, živé tapety,
Kapsa, Total Commander, cloudové priečinky (rclone).

## 3. Návrh

1. ✅ **Zmazať odkazové stránky** (hotové 26. 9., commit fc6a4c6): Obrazovky, Zvuk, Sieť, Bluetooth, Napájanie, Úložné
   zariadenia a Tlač majú priamo ovládanie. Je to ten istý komponent ako Správca zariadení (`common/SpravcaZariadeni.qml`),
   takže zmena na jednom mieste platí všade. Napájanie dostalo navyše režim napájania (Úsporný · Vyvážený · Výkon)
   a herný režim ako Windows 11. Ostáva 5 odkazov na App Manager a Monitor (Aplikácie, Inštalácia, Aktualizácie,
   Súkromie a NET, Spúšťanie) — tie vyriešim pri zlučovaní duplicít (bod 2) podľa tvojej odpovede A/B.
2. **Zlúčiť duplicity** podľa tabuľky 2.2.
3. **Doplniť chýbajúce stránky** podľa dôležitosti:
   - Pre pokročilých;
   - Schránka;
   - Automatické prehrávanie;
   - Multitasking;
   - Zachytávanie;
   - Povolenia aplikácií;
   - Aktualizácie ovládačov;
   - Písma;
   - Prístupnosť (lupa, filtre, prilepené klávesy).
4. **Horná úroveň — treba tvoje rozhodnutie** (otázka nižšie):
   - **A · ostať pri 6 oblastiach LatteOS** (Softvér, Dáta, Hardvér, Účet, Prostredie, Systém; tvoj návrh
     z main_setting_v2.md) a iba presunúť zle zaradené stránky;
   - **B · prejsť na 11 kategórií ako Windows 11** (Systém, Zariadenia, Sieť a internet, Prispôsobenie, Aplikácie, Účty,
     Čas a jazyk, Hry, Prístupnosť, Súkromie a zabezpečenie, Aktualizácie) + Pre pokročilých. Bývalý používateľ
     Windows by hľadal na rovnakom mieste; vrstvené karty ostanú.

---

# Alfatest 1: LatteOS očami používateľa Windows, macOS a Linuxu

25. 9. 2026 večer · stav repozitára `gamerdistro` po commite 2bfdc98 · overené na živej VM (`hyprctl binds`, konfigurácia)
a v kóde (Súbory, Plocha, Kapsa, Noctalia).

Pokrýva, **ako človek systém naozaj ovláda**: myšou s viacerými tlačidlami a kolieskom (časť 5) a klávesnicou,
nielen zoznam skratiek.

**Ako čítať:**
- ✅ funguje rovnako alebo lepšie;
- 🟡 existuje, ale ináč (iná skratka, iné miesto);
- ❌ chýba;
- ⚠ **konflikt**: rovnaká skratka robí v LatteOS niečo iné. Toto je najhoršie, lebo zvyk používateľa spôsobí chybu.
- ❓ neoverené, treba vyskúšať rukou.

**Na konci** sú vybrané riešenia (licencie, alternatívy, rozdiely) a poradie práce. Kým ich nepotvrdíš, nič z toho
nerobím. Hotová je iba úprava okna L (bod 0).

---

## Stav po tvojich odpovediach (25. 9. 2026 v noci)

**Rozhodnutia:**
- Cieľová skupina sú bývalí používatelia Windows. Hlavné ovládanie je **myš s dvomi tlačidlami ako Windows 7–11**;
  v sporných prípadoch vyhráva Windows.
- Skratky: predvolený **profil Windows**, v Nastaveniach sa dá prepnúť na **Linux** alebo **macOS**.
- Nič dôležité nesmie byť iba na klávese Win alebo AltGr (herné klávesnice Win často nemajú): Štart ide aj cez
  **Ctrl+Esc** a všetko ide myšou z lišty.
- Režim plávajúcich okien = **Windows 11**, páska a dlaždice = Linux (páska ostáva na tvoje preskúmanie).

**Hotové** (podrobnosti v denníku):

| Oblasť | Stav |
|---|---|
| P0: Super+Shift+M, Super+Q, fokus kliknutím | ✅ |
| Profily Windows / Linux / macOS, Nastavenia › Klávesnica a skratky, Num Lock | ✅ |
| Alt+Tab, Alt+F4, Ctrl+Alt+Del, Win a Ctrl+Esc = Štart, Win+E/I/S/R/X/A/N/V/./D/M/Home/šípky/Ctrl+D/1…9/P/lupa | ✅ |
| Snímky (PrtSc, Win+Shift+S, Win+PrtSc, Shift+PrtSc), nahrávanie Win+Alt+R, multimediálne klávesy | ✅ |
| Prichytenie okien ťahaním k okraju s náhľadom, odtiahnutie vráti veľkosť | ✅ (overené cez hyprctl, myšou treba vyskúšať) |
| Pravý klik na titulok = ponuka okna, tlačidlá –□✕ iba ľavým, Alt+Medzerník | ✅ (po prihlásení) |
| Ťahanie súborov pravým/stredným tlačidlom s ponukou, pravidlo „ten istý disk = presun“, Ctrl/Shift/Alt | ✅ |
| Súbory prijímajú súbory zvonku, Plocha ťahá ikony do okien | ✅ |
| Súbory: F2, F5, Del bez otázky, Ctrl+Z, Alt+←→↑, bočné tlačidlá, Ctrl+koliesko, Shift+F10, Menu, Medzerník | ✅ |
| Bočné tlačidlá myši v Nastaveniach a App Manageri | ✅ |
| Nastavenia › Myš: tlačidlá → akcie, Piper, opakovanie klávesov | ✅ |
| Panel úloh: klik na aktívne okno minimalizuje, stredný klik nové okno, pravý klik na Štart = Win+X | ✅ (po prihlásení) |
| Barista: voľba profilu ovládania pri prvom štarte | ✅ |
| Win+P: Iba obrazovka PC / Duplikovať / Rozšíriť / Iba druhá | ✅ (s dvomi monitormi až na HW) |
| Lišta rozložení Windows 11 pri ťahaní okna k hornému okraju v strede | ✅ |

**Treba vyskúšať rukou:** samotný Win po Win+E, Alt+Tab, prichytenie okna myšou, pravé ťahanie súboru na Ploche
a v Súboroch.

**Ostáva (poradie):**
1. Súbor podržaný nad oknom v páske ho prenesie dopredu; súbor pustený na ikonu aplikácie ju otvorí;
   priečinok sa pri podržaní otvorí. (Lišta Noctalie nie je cieľom ťahania, treba vrstvu nad oválom okien.)
2. Win11: rozloženia pri podržaní myši nad □ (ďalšia záplata hyprbars s časovačom).
3. Kláves Menu, Shift+koliesko a Ctrl+koliesko vo všetkých našich zoznamoch (dnes v Súboroch).
4. Rýchlosť dvojkliku, nájsť kurzor (Ctrl).
5. macOS: Cmd+C/V cez xremap, horúce rohy.
6. Klávesnica na obrazovke (wvkbd nie je vo Fedore, treba zostaviť zo zdroja; GPL-3.0), čítačka (Orca),
   diktovanie (s AI).

---

## 0. Hotové dnes večer: App Manager s GIF / videom

- **Ostrov na lište nemá ikonu**, iba pekný rám: tenký lem vo farbe akcentu a jemný svetlý lem vnútri.
- **Pri otvorení sa rám plynulo presunie na celé okno.**
  - Pri p = 0 obrys presne kopíruje ostrov (všetky rohy zaoblené).
  - Kmeň potom vyrastie z hornej hrany ostrova a obrys sa roztiahne po celom tvare L až po panel. Rohy sa pritom plynulo
    menia z rohov ostrova na rohy okna.
  - Zatváranie beží opačne a na konci rám ostane na ostrove.
- Rovnako to funguje aj pri Zariadeniach (pravé L) a v náhľade v Nastaveniach › Lišta.
- Opravené popri tom:
  - obrys mal pri rohoch malé výbežky čiar;
  - stlmenie textúry pretŕčalo cez zaoblený roh kmeňa.
- Pri para, matrix a ďalších textúrach ostáva ikona ako doteraz.
- Overené v headless kompozitore: 6 fáz animácie, obe strany, skutočný App Manager zatvorený aj otvorený.
- Nasadené v `/usr/share/latteos/apps`. Prejaví sa po reštarte spúšťača (`latte-app spustac`) alebo po prihlásení.
- **Video** ako textúra lišty zatiaľ nejde, lišta vie iba GIF / WebP / obrázok. Video (mp4) by potrebovalo mpv vo vrstve
  a to je až na počítači s GPU (VM padá, pozri živú tapetu).

---

## 1. Ťahanie pravým tlačidlom (tvoja otázka)

| | Čo sa stane po pustení | Klávesy pri ľavom ťahaní |
|---|---|---|
| **Windows 10 aj 11** (Prieskumník, plocha) | Ponuka: **Kopírovať sem · Presunúť sem · Vytvoriť odkazy sem · Zrušiť**; programy pridávajú vlastné položky (7-Zip: „Rozbaliť sem“). Tučná je položka, ktorú by urobilo ľavé ťahanie. | Ľavé ťahanie: **na tom istom disku presunie, na iný disk skopíruje**, pri .exe vytvorí odkaz. **Ctrl** = kopírovať, **Shift** = presunúť, **Alt** alebo **Ctrl+Shift** = odkaz. Pri kurzore je popis „+ Kopírovať do Dokumenty“. Esc ťahanie zruší. |
| **macOS** (Finder) | Pravé ťahanie neexistuje. | Na tom istom disku presunie, na iný skopíruje. **Option** = kopírovať, **Cmd** = presunúť, **Cmd+Option** = alias. Keď podržíš súbor nad priečinkom, priečinok sa sám otvorí (spring-loaded). |
| **Linux · KDE Dolphin** | Ponuka **Presunúť sem · Kopírovať sem · Odkaz sem · Zrušiť** sa ukáže pri **každom** pustení (aj ľavom), ak nedržíš kláves. | Shift = presunúť, Ctrl = kopírovať, Ctrl+Shift = odkaz. |
| **Linux · Thunar (XFCE)** | Pravé alebo stredné ťahanie ukáže tú istú ponuku (od verzie 1.6.2 znova). | Ako Windows. |
| **Linux · Nautilus (GNOME), Nemo** | Ponuku ukáže **Alt + ľavé ťahanie**. Stredné ťahanie ju malo tiež, ale v GTK 3/4 je pokazené (hlásenie GTK #1512). | Ctrl = kopírovať, Shift = presunúť. |
| **LatteOS dnes** | **Nič.** Súbory aj Plocha berú iba ľavé tlačidlo. | Súbory: **vždy kopíruje** (ako Total Commander), Shift = presunúť. Ctrl, Alt ani odkaz nejdú. Plocha: ikona na priečinok = presunúť, súbor z inej aplikácie = kopírovať. |

**Čo ešte chýba pri ťahaní v LatteOS:**
- **Súbory neprijmú nič zvonku.** Súbor z Firefoxu, z Plochy ani z Kapsy sa do Súborov pretiahnuť nedá, prijímajú iba
  ťahanie medzi vlastnými panelmi.
- **Z Plochy sa nedá ťahať von.** Ikonu z plochy nepretiahneš do Súborov, do prehliadača ani do Discordu.
- Ťahanie zo Súborov do iných aplikácií funguje, ale iba ako kopírovanie.
- **Súbor sa nedá pustiť na ikonu aplikácie** (lišta, App Manager), aby sa v nej otvoril. Windows to vie cez odkazy
  a Mac cez Dock.
- **Podržanie súboru nad oknom v páske** okno neprenesie dopredu (Windows to robí nad tlačidlom na paneli úloh).
- Priečinok sa pri podržaní neotvorí sám (spring-loaded).

**Obmedzenie Waylandu:** protokol má akciu „opýtať sa“ (`dnd_action ask`), GTK 4 ju podporuje, Qt nie.
- Ponuku po pustení preto vieme ukázať vždy, keď cieľom je aplikácia LatteOS (Súbory, Plocha, Kapsa, Kôš), aj pri súbore
  z cudzej aplikácie.
- Keď cieľom je cudzia aplikácia (Firefox, Discord), o akcii rozhoduje ona, prakticky vždy „kopírovať“. Rovnako to
  funguje aj vo Windows.

---

## 2. Používateľ Windows 10 / 11

### 2.1 Čím sa líši Windows 10 a 11 (čo si používateľ prinesie)

| | Windows 10 | Windows 11 | Čo z toho LatteOS |
|---|---|---|---|
| Kontextová ponuka | plná, dlhá | skrátená, zvyšok v „Zobraziť ďalšie možnosti“ (Shift+F10) | ponuky sú plné, ale zoradené; ✅ vyhovie obom |
| Štart | vľavo, dlaždice | v strede, pripnuté + odporúčané | App Manager vľavo (bližšie Win10) |
| Win+A | Centrum akcií (oznámenia + tlačidlá) | Rýchle nastavenia | Win11 význam ✅ |
| Win+N | – | Oznámenia a kalendár | ⚠ v LatteOS minimalizuje okno |
| Rozloženia okien | Snap myšou k okrajom | + **Win+Z** a podržanie myši nad □, lišta pri ťahaní hore | Win+Z ✅, myšou ❌ |
| Karty v Prieskumníkovi | nie | áno (Ctrl+T/W) | ✅ |
| Pretiahnutie súboru na tlačidlo v paneli úloh | áno | zmizlo v 21H2, vrátené v 22H2 | ❌ |
| Trasenie oknom = minimalizovať ostatné | zapnuté | vypnuté predvolene | ❌ netreba |
| Panel úloh na boku obrazovky | áno | nie | lišta dole ✅ |
| PrtSc | kopíruje obrazovku | otvorí Výstrižky (výber oblasti) | ❌ |

### 2.2 Klávesnica: celý systém

| Akcia | Windows | LatteOS teraz | Stav |
|---|---|---|---|
| Štart (samotný kláves Win) | Win | nič | ❌ **najčastejšia akcia vôbec** |
| Prepínanie okien | **Alt+Tab** (drž Alt) | nič; Noctalia ho má na Super+Shift+Tab | ❌ |
| Zavrieť okno | **Alt+F4** | nič (iba Super+Q alebo ✕) | ❌ |
| Ponuka okna | Alt+Medzerník | nič | ❌ |
| Správca úloh | Ctrl+Shift+Esc | Monitor | ✅ |
| Bezpečnostná obrazovka | Ctrl+Alt+Del | nič | ❌ |
| Zamknúť | Win+L | zamknúť | ✅ |
| Plocha | Win+D | plocha a späť | ✅ |
| Prieskumník | Win+E | Súbory | ✅ |
| Nastavenia | Win+I | **AI rozhovor** | ⚠ |
| Hľadať | Win+S / Win+Q | **Win+Q zavrie okno!** | ⚠ **nebezpečné** |
| Spustiť | Win+R | Text Bar je na Super+Medzerník | 🟡 |
| Ponuka pre pokročilých | Win+X (alebo pravý klik na Štart) | nič | ❌ |
| Schránka s históriou | Win+V | **prepne okno na plávajúce** | ⚠ (Kapsa existuje, iba nie je na Win+V) |
| Emoji | Win+. | nič (Noctalia to má: spúšťač `/emo`) | ❌ |
| Výstrižok oblasti | **Win+Shift+S**, PrtSc | nič (Noctalia to má: `screenshot-region`) | ❌ |
| Celá obrazovka do súboru | Win+PrtSc | nič | ❌ |
| Nahrávanie obrazovky | Win+Alt+R (Game Bar), Výstrižky | nič | ❌ |
| Herný panel | Win+G | Herňa | ✅ |
| Rozloženia okna | Win+Z | panel rozložení | ✅ |
| Zobrazenie úloh | Win+Tab | prehľad pásky | ✅ |
| Maximalizovať / snap | Win+↑ / Win+←→ | **presun fokusu** | ⚠ |
| Minimalizovať | Win+↓ | presun fokusu | ⚠ |
| Minimalizovať všetko / obnoviť | Win+M / Win+Shift+M | nič / **Win+Shift+M okamžite odhlási bez otázky** | ⚠ **nebezpečné** |
| Minimalizovať ostatné | Win+Home | nič | ❌ |
| Okno na iný monitor | Win+Shift+←→ | to isté | ✅ |
| Nová / ďalšia virtuálna plocha | Win+Ctrl+D / Win+Ctrl+←→ | nič / **Win+Ctrl+←→ presúva okno** | ⚠ |
| Aplikácia č. N z panela úloh | Win+1…9 | prepne plochu N | ⚠ (pre tiling používateľov správne) |
| Oznámenia | Win+N | minimalizuje okno | ⚠ |
| Premietanie (monitory) | Win+P | nič | ❌ |
| Bezdrôtový displej | Win+K | nič | ❌ (neskôr, Miracast) |
| Diktovanie | Win+H | nič | ❌ (neskôr, s AI) |
| Lupa / klávesnica na obrazovke / Moderátor | Win+Plus / Win+Ctrl+O / Win+Ctrl+Enter | nič | ❌ |
| Rozloženie klávesnice | Alt+Shift, Win+Medzerník | Alt+Shift ✅, Win+Medzerník = Text Bar | 🟡 |
| Hlasitosť, jas | klávesy | ✅ | ✅ |
| Prehrať / ďalšia skladba | multimediálne klávesy | **nenaviazané** | ❌ |

### 2.3 Myš a okná

| Akcia | Windows | LatteOS | Stav |
|---|---|---|---|
| Kliknutím okno aktivovať | klik | **okno sa aktivuje už prejdením myšou** (`follow_mouse = 1`), písanie ide tam, kde je kurzor | ⚠ **mätúce** |
| Rolovanie v neaktívnom okne | áno | áno | ✅ |
| Dvojklik na titulok = zväčšiť | áno | áno | ✅ |
| Ťahanie za titulok | áno | áno | ✅ |
| Ťahanie k hornému okraju = maximalizovať | áno | nie | ❌ |
| Ťahanie k boku / do rohu = polovica / štvrtina | áno | nie | ❌ |
| Ťahanie maximalizovaného okna ho obnoví | áno | ❓ | ❓ |
| Myš nad □ ukáže rozloženia | Win11 | nie (Win+Z áno) | ❌ |
| Pravý klik na titulok = ponuka okna | áno | nie (hyprbars nerozlišuje tlačidlo myši) | ❌ |
| Zmena veľkosti za okraj | áno | áno | ✅ |
| Náhľad pri prejdení nad oknom v paneli | áno | áno (ovál pások) | ✅ |
| Pravý klik na okno v paneli | jump list | kontextová ponuka | ✅ |
| Klik na aktívne okno v paneli = minimalizovať | áno | ❓ | ❓ |
| Stredný klik v paneli = nové okno / zavrieť | áno | ❓ | ❓ |
| Pripnúť aplikáciu na panel | áno | nie | ❌ |
| Pravý klik na Štart = Win+X ponuka | áno | App Manager nemá pravý klik | ❌ |
| „Zobraziť plochu“ v pravom rohu | áno | pravý roh sú Zariadenia | 🟡 (Super+D) |

### 2.4 Prieskumník → Súbory (režim Forklift)

| Akcia | Windows | LatteOS Súbory | Stav |
|---|---|---|---|
| Premenovať | **F2** | **F2 obnoví zoznam**, premenovanie je Shift+F6 (TC) alebo cez ponuku | ⚠ |
| Obnoviť | F5 | **F5 = kopírovať (TC)** | ⚠ v režime Forklift |
| Nový priečinok | Ctrl+Shift+N | F7 | 🟡 |
| Späť / dopredu | Alt+← / Alt+→, bočné tlačidlá myši | iba tlačidlá v hlavičke | ❌ |
| O úroveň vyššie | Alt+↑ | Backspace | 🟡 |
| **Vrátiť akciu** | **Ctrl+Z** (presun, premenovanie, zmazanie) | nie (iba hromadné premenovanie) | ❌ |
| Hľadať | Ctrl+F / F3 | Alt+F7; F3 prepína dva panely | ⚠ |
| Do adresy | Ctrl+L / Alt+D | klikateľná adresa | 🟡 ❓ skratka |
| Vlastnosti | Alt+Enter | Alt+Enter | ✅ |
| Kôš / natrvalo | Del / Shift+Del | rovnako | ✅ |
| Kopírovať / vystrihnúť / vložiť | Ctrl+C/X/V | rovnako, spolupracuje s inými aplikáciami | ✅ |
| Kopírovať ako cestu | Ctrl+Shift+C | v ponuke Príkazy | 🟡 |
| Veľkosť ikon kolieskom | Ctrl+koliesko | ❓ | ❓ |
| Karty | Ctrl+T / Ctrl+W | rovnako | ✅ |
| Medzerník | nič zvláštne | označí (TC) | 🟡 |
| Otvoriť v… / zbaliť / vlastnosti | pravý klik | pravý klik | ✅ |
| Ťahanie | pozri časť 1 | pozri časť 1 | ❌ |

### 2.5 Plocha a Kôš

- ✅ Pravý klik (Zobraziť, Zoradiť podľa, Nový…), F2, Del, Ctrl+C/X/V, výber obdĺžnikom, ťahanie ikon.
- ✅ Kôš na ploche, Kôš s obnovením (`latte-kos obnov`).
- ❌ Ikonu z plochy nepretiahneš do okna (časť 1).
- ❌ Alt+F4 na ploche (vo Windows ponuka Vypnúť / Reštartovať).

---

## 3. Používateľ macOS

Najväčší rozdiel nie je vzhľad, ale **kláves Cmd**. Na Macu sa kopíruje Cmd+C, na PC Ctrl+C. Kto má klávesnicu
Mac alebo zvyk z Macu, stláča kláves vedľa medzerníka (na PC klávesnici je tam Alt, Cmd = Super).

| Akcia | macOS | LatteOS | Stav |
|---|---|---|---|
| Kopírovať / vložiť / späť… | **Cmd**+C/V/Z/S/W/T/F | Ctrl+… | ❌ **treba prepínač „Cmd ako Ctrl“** |
| Spotlight | Cmd+Medzerník | Super+Medzerník = Text Bar | ✅ **presne sedí** |
| Prepínanie aplikácií | Cmd+Tab | Super+Tab = prehľad pásky | 🟡 |
| Okná tej istej aplikácie | Cmd+` | nič | ❌ |
| Ukončiť aplikáciu | Cmd+Q | Super+Q zavrie okno | 🟡 (na Macu končí celá aplikácia) |
| Skryť / minimalizovať | Cmd+H / Cmd+M | nič / Super+N | ❌ / 🟡 |
| Vynútiť ukončenie | Cmd+Option+Esc | nič (Monitor cez Ctrl+Shift+Esc) | 🟡 |
| Zamknúť | Ctrl+Cmd+Q | Super+L | 🟡 |
| Snímka obrazovky | Cmd+Shift+3 / 4 / 5 | nič | ❌ |
| Mission Control | F3, Ctrl+↑, 3 prsty hore | Super+Tab, 4 prsty hore | 🟡 |
| Okná aktuálnej aplikácie | Ctrl+↓ | nič | ❌ |
| Plochy (Spaces) | Ctrl+←→, 3 prsty do strán | Super+1…9, 3 prsty do strán | 🟡 |
| Horúce rohy | áno | nie (Noctalia ich má, vypnuté) | ❌ |
| Launchpad / Dock | áno | App Manager / lišta | ✅ |
| Súbor na ikonu v Docku = otvoriť v nej | áno | nie | ❌ |
| Emoji | Ctrl+Cmd+Medzerník, Globe+E | nič | ❌ |
| Rýchly náhľad | **Medzerník** | Medzerník označí | ⚠ |
| Premenovať vo Finderi | **Enter** | Enter otvorí | ⚠ |
| Otvoriť / nadradený priečinok | Cmd+↓ / Cmd+↑ | Enter / Backspace | 🟡 |
| Do koša / vysypať | Cmd+Delete / Cmd+Shift+Delete | Del / ponuka | 🟡 |
| Vrátiť zo Koša | Vrátiť späť | `latte-kos obnov` | ✅ |
| Skryté súbory | Cmd+Shift+. | Ctrl+H | 🟡 |
| Prejsť na priečinok | Cmd+Shift+G | klikateľná adresa | 🟡 |
| Informácie | Cmd+I | Alt+Enter | 🟡 |
| Duplikovať | Cmd+D | nie | ❌ |
| Vrátiť presun / premenovanie | Cmd+Z | nie | ❌ |
| Štítky (farby) | áno | áno | ✅ |
| Ťahanie: Option = kópia, Cmd = presun | áno | iba Shift = presun | ❌ |
| Priečinok sa otvorí pri podržaní | áno | nie | ❌ |
| Prirodzené rolovanie, ťuknutie | áno | áno (touchpad) | ✅ |
| Dva prsty = pravý klik | áno | áno (ťuknutie dvoma prstami) | ✅ ❓ |
| Zelené tlačidlo / dlaždice (macOS 15) | ťahanie k okraju, Option+klik | Win+Z | 🟡 |
| AirDrop, spoločná schránka s mobilom | áno | KDE Connect (mobil) | 🟡 |
| Time Machine | áno | `latte-backup` | 🟡 ❓ |
| Globálna lišta ponúk hore | áno | nie | ❌ (neplánujem, každá aplikácia má vlastnú) |
| Skok po slovách / na začiatok riadku | Option+←→ / Cmd+←→ | Ctrl+←→ / Home, End | 🟡 (vyrieši profil Mac) |

---

## 4. Používateľ Linuxu

LatteOS stojí na Hyprlande, takže **používateľ tiling správcov (Hyprland, i3, Sway)** je doma: Super+Enter
terminál, Super+Q zavrieť, Super+1…9 plochy, Super+šípky fokus, Super+ťahanie myšou, fokus za myšou.
Používateľ **GNOME, KDE, XFCE alebo Cinnamonu** je bližšie k Windows.

| Akcia | GNOME / KDE / XFCE | LatteOS | Stav |
|---|---|---|---|
| Samotný Super = prehľad / ponuka | áno | nič | ❌ |
| Spustiť príkaz | Alt+F2 | Super+Medzerník | 🟡 |
| Terminál | Ctrl+Alt+T | Super+Enter (foot) | 🟡 |
| Odhlásenie / vypnutie | Ctrl+Alt+Del | nič | ❌ |
| Plochy | Ctrl+Alt+←→ (KDE, XFCE), Super+PgUp/PgDn (GNOME) | Super+1…9 | 🟡 |
| Presun okna myšou | Super+ťahanie (GNOME), Alt+ťahanie (KDE, XFCE) | Super+ťahanie | ✅ / 🟡 |
| Zmena veľkosti myšou | Super+pravé (KDE), Super+stredné (GNOME) | Super+pravé | ✅ |
| Stredný klik vloží označený text | áno | áno | ✅ |
| Snímka obrazovky | PrtSc (nástroj GNOME / Spectacle) | nič | ❌ |
| Ponuka po pustení súboru | Dolphin vždy, Thunar pravé/stredné, Nautilus Alt | nič | ❌ |
| F2 premenovať, Ctrl+L adresa, Ctrl+H skryté | áno | F2 obnoví, Ctrl+H ✅ | ⚠ / ✅ |
| F3 rozdeliť okno (Dolphin) | áno | F3 = dva panely | ✅ |
| Alt+←→ / Alt+↑ | áno | nie / Backspace | ❌ / 🟡 |
| Ctrl+Z v správcovi súborov | áno | nie | ❌ |
| KDE Connect | áno | áno | ✅ |
| Flatpak, obchod | áno | App Manager | ✅ |
| Horúci roh (GNOME Aktivity) | áno | nie | ❌ |

---

## 5. Myš s viacerými tlačidlami, koliesko a klávesnica ako zariadenie

Platí pre všetkých troch používateľov. Bežná myš má dnes 5 tlačidiel (ľavé, pravé, stredné / koliesko, **Späť** a
**Dopredu** na boku). Herná alebo kancelárska myš (Logitech MX, G502, Razer) má ďalšie tlačidlá, koliesko do strán
a tlačidlo DPI.

### 5.1 Tlačidlá myši

| Tlačidlo / úkon | Windows | macOS | Linux (GNOME / KDE) | LatteOS | Stav |
|---|---|---|---|---|---|
| Pravý klik = ponuka všade | áno | áno (aj Ctrl+klik) | áno | naše aplikácie, plocha, lišta ✅; **titulok okna ❌** | 🟡 |
| Stredný klik na kartu = zavrieť | áno | áno | áno | Súbory ✅ | ✅ |
| Stredný klik na odkaz = nová karta | prehliadač | prehliadač | prehliadač | prehliadač (Firefox) | ✅ |
| Stredný klik v paneli úloh | nové okno | – | KDE: nové okno / zavrieť | ❓ páska | ❓ |
| Stredný klik v texte | **automatické rolovanie** (prehliadač) | nič | **vloží označený text** | vloží označený text | ⚠ pre Windows používateľa: klik kolieskom omylom vloží text; automatické rolovanie je vo Firefoxe na Linuxe vypnuté |
| Stredný klik na titulok okna | nič | nič | KDE: okno dozadu | nič | 🟡 |
| **Bočné Späť / Dopredu** | Prieskumník, prehliadač, Nastavenia, Obchod | prehliadač, Finder (s ovládačom Logi) | prehliadač, Dolphin, Nautilus, Nastavenia KDE | prehliadač ✅; **Súbory, Nastavenia, App Manager, Monitor ❌** | ❌ |
| Ďalšie tlačidlá (G4…G11, palec, „gesto“) | G Hub / Synapse / Logi Options+ priradí akciu | Logi Options+ | **Piper** (libratbag), **Solaar**, input-remapper | nič, tlačidlá nič nerobia | ❌ |
| Tlačidlo DPI, profily, RGB | ovládač výrobcu | ovládač výrobcu | Piper, OpenRGB | nič | ❌ |
| Super + ľavé ťahanie = presun okna | – | – | GNOME áno (KDE Alt) | ✅ | ✅ (Windows používateľ o tom nevie, ukázať v Baristovi) |
| Super + pravé ťahanie = veľkosť okna | – | – | KDE áno | ✅ | ✅ |
| Ľavák (prehodené tlačidlá) | áno | áno | áno | Nastavenia › Myš ✅ | ✅ |
| Rýchlosť dvojkliku | áno | áno | áno | nie je nastavenie (Qt 400 ms) | ❌ |

### 5.2 Koliesko

| Úkon | Windows | macOS | Linux | LatteOS | Stav |
|---|---|---|---|---|---|
| Roluje okno pod kurzorom, aj neaktívne | áno (od Win10) | áno | áno | áno; ostane aj po prepnutí na „fokus kliknutím“ (`follow_mouse = 2`) | ✅ |
| Shift + koliesko = vodorovne | väčšina aplikácií | celý systém | GTK aj Qt | cudzie aplikácie ✅; naše zoznamy (Súbory v ikonách, App Manager) ❓ | ❓ |
| Koliesko do strán (naklonenie) | vodorovné rolovanie | áno | áno | cudzie ✅, naše ❓ | ❓ |
| Ctrl + koliesko = priblížiť / veľkosť ikon | prehliadač, Prieskumník, Office | Cmd + koliesko / štipnutie | áno | prehliadač ✅; **Súbory ❌**, Heidelberg ❓ | ❌ |
| Koliesko nad ikonou hlasitosti | mení hlasitosť (Win11 22H2+) | nie | KDE áno | ostrov Zariadení na lište ❓ (v paneli Zariadenia áno) | ❓ |
| Koliesko nad panelom úloh / páskou | nič | nič | KDE prepína okná | Super + koliesko = plochy; samotné ❓ | 🟡 |
| Rýchlosť rolovania | počet riadkov | áno | áno | Nastavenia › Myš (násobok) ✅ | ✅ |
| Prirodzený smer (ako mobil) | voliteľné | predvolené | voliteľné | voliteľné, touchpad predvolene zapnuté | ✅ |

### 5.3 Kurzor

| Úkon | Windows | macOS | LatteOS | Stav |
|---|---|---|---|---|
| Rýchlosť a zrýchlenie | áno | áno | Nastavenia › Myš | ✅ |
| Veľkosť kurzora | áno | áno | `XCURSOR_SIZE` z nastavení | 🟡 ❓ či je v Prístupnosti |
| Nájsť kurzor (Ctrl ukáže krúžok / zatrasenie zväčší) | Ctrl | zatrasenie | nič | ❌ |
| Bublina s popisom pri prejdení myšou | áno | áno | niekde áno, nie všade | 🟡 |

### 5.4 Klávesnica ako zariadenie (nielen skratky)

| Vec | Windows | macOS | Linux | LatteOS | Stav |
|---|---|---|---|---|---|
| **Num Lock po štarte** | stolný PC zapnutý (BIOS) | – | GNOME/KDE si pamätá | **vypnutý** (`numlock_by_default = false`); na numerickej klávesnici idú šípky namiesto čísel | ❌ |
| Upozornenie na Caps Lock | pri hesle | pri hesle | pri hesle | greeter ✅, inde nie | 🟡 |
| Slovenčina + angličtina, AltGr znaky | áno | áno | áno | sk + us, Alt+Shift, AltGr cez xkb ✅ | ✅ |
| Slovenská QWERTY (bez prehodeného Y/Z) | voliteľné | voliteľné | voliteľné | ❓ výber v Baristovi | ❓ |
| Kláves **Menu** / **Shift+F10** = kontextová ponuka | všade | – | všade | naše aplikácie ❌ | ❌ |
| Tab / Shift+Tab po prvkoch, Enter = OK, Esc = Zrušiť, Medzerník = zaškrtnúť | všade | všade (Tab voliteľne) | všade | dialógy Súborov čiastočne, Nastavenia ❓ | 🟡 ❓ |
| Alt + podčiarknuté písmeno v ponuke | áno | – | áno | nie | ❌ (neskôr) |
| Rýchlosť opakovania klávesu a oneskorenie | áno | áno | áno | predvolené Hyprlandu, bez nastavenia | ❌ |
| Prehrať / ďalšia / predošlá | áno | áno | áno | nenaviazané | ❌ |
| Stlmiť mikrofón, podsvietenie klávesnice, kalkulačka, e-mail, domov | áno | – | áno | nenaviazané (Noctalia má `mic-mute`, `keyboard-backlight-*`) | ❌ |
| Hlasitosť, jas | áno | áno | áno | ✅ | ✅ |
| Prilepené klávesy (Shift 5×) | áno | áno | áno | nie | ❌ (neskôr) |

---

## 6. Zhrnutie: čo treba riešiť (poradie podľa dopadu)

**P0: nebezpečné konflikty (opravím hneď po potvrdení, 1 hodina):**
1. **Super+Shift+M okamžite ukončí reláciu.** Vo Windows je to „obnoviť okná“. Treba ho zmeniť na obnovenie okien
   a odhlásenie presunúť za otázku (Ctrl+Alt+Del).
2. **Super+Q zavrie okno.** Vo Windows je to hľadanie. V profile Windows treba zatváranie cez Alt+F4 a Super+Q
   nechať iba profilu Linux.
3. **Fokus za myšou.** Windows aj Mac používateľ píše do okna, ktoré naposledy klikol. Treba `follow_mouse = 2`
   (klik aktivuje, koliesko ide aj do neaktívneho okna ako vo Windows).

**P1: základ, bez ktorého sa používateľ Windows / Mac cíti stratený:**
4. Alt+Tab, Alt+F4, samotný kláves Win (App Manager), Ctrl+Alt+Del.
5. Snímky obrazovky: PrtSc, Win+Shift+S, Win+PrtSc (Mac: Cmd+Shift+3/4/5).
6. Win+V (Kapsa), Win+. (emoji), Win+I (Nastavenia), multimediálne klávesy.
7. Ťahanie okna k okrajom (maximalizovať, polovica, štvrtina) a pravý klik na titulok okna.
8. **Ťahanie súborov:** ponuka pravým (aj stredným) tlačidlom, Súbory prijmú súbory zvonku, Plocha pustí ikony von,
   Windows pravidlo „ten istý disk = presun“ s popisom pri kurzore, Ctrl/Shift/Alt.
9. Súbory v režime Forklift: F2 premenovať, F5 obnoviť, Ctrl+Z späť, Alt+←→↑, Ctrl+Shift+N, Ctrl+F, Ctrl+L.
10. **Myš a klávesnica vo všetkých našich aplikáciách:**
    - bočné tlačidlá Späť / Dopredu (Súbory, Nastavenia, App Manager, Monitor);
    - Ctrl + koliesko = veľkosť, Shift + koliesko a koliesko do strán = vodorovne;
    - kláves Menu a Shift+F10 = kontextová ponuka;
    - Num Lock zapnutý na stolnom PC.

**P2: pohodlie:**
11. **Profil ovládania** v Baristovi a v Nastaveniach: Windows (predvolený) / macOS / Linux (GNOME, KDE) /
    Tiling (Hyprland). Profil nastaví skratky, správanie ťahania, fokus a horúce rohy naraz.
12. Rýchly náhľad (Medzerník v režime Forklift), priečinok sa otvorí pri podržaní, súbor na ikonu aplikácie, podržanie
    súboru nad oknom v páske.
13. Ďalšie tlačidlá myši (G-tlačidlá, palec) → akcie systému, DPI a profily myši. Nastavenia: rýchlosť dvojkliku,
    opakovanie klávesov, nájsť kurzor (Ctrl).
14. Win+X (a pravý klik na dlaždicu aplikácií), Win+P, Win+M / Win+Home, Win+Ctrl+D/←→, horúce rohy, nahrávanie
    obrazovky, lupa a klávesnica na obrazovke. Diktovanie (Win+H) príde s AI.

---

## 7. Vybrané riešenia, alternatívy a rozdiely

Pravidlo: ak existuje hotový nástroj pod voľnou licenciou, použijem ho a prispôsobím. GPL-3.0 aj AGPL sú v poriadku,
LatteOS je otvorený a zadarmo. Pri každom bode je môj výber, pod ním alternatívy, aby si mohol výber zmeniť.

### 7.1 Ťahanie súborov s ponukou (pravé / stredné tlačidlo)
**Výber: vlastná úprava Súborov, Plochy a Kapsy (QML).** Súbory sú naše, žiadna knižnica to nerieši za nás.
- **Ponuka po pustení:** Kopírovať sem · Presunúť sem · Vytvoriť odkaz sem · Zrušiť.
  - Podľa typu pribudne: *Rozbaliť sem* (archív), *Nastaviť ako tapetu* (obrázok na ploche), *Otvoriť v…*.
  - Tučná položka = to, čo by urobilo ľavé ťahanie (ako Windows).
- **Ľavé ťahanie (nastaviteľné):**
  - *Ako Windows*, predvolené: ten istý disk = presun, iný disk = kópia;
  - *Vždy kopírovať*: dnešné správanie, ako Total Commander;
  - *Vždy sa opýtať*: ako KDE.
- **Klávesy:** Ctrl = kópia, Shift = presun, Ctrl+Shift = odkaz. Esc zruší. Popis pri kurzore sa mení naživo
  („Presunúť do Dokumenty“).
- **Profil Mac:** Option (Alt) = kópia, Cmd (Super) = presun, Cmd+Option = odkaz.
- **Prijímanie zvonku:** Súbory a priečinky v nich prijmú `text/uri-list` z Firefoxu, Plochy aj Kapsy a ukážu tú istú
  ponuku. Plocha pustí ikony von (systémové ťahanie so zoznamom súborov).
- Alternatívy:
  - **Dolphin** (GPL-2.0+, KDE): ponuka pri každom pustení, veľmi vyladený; potrebuje ~150 MB knižníc KDE a nemá
    náš vzhľad ani režim TC.
  - **Thunar** (GPL-2.0+): pravé aj stredné ťahanie s ponukou, ľahký (GTK 3); vzhľad a funkcie ďaleko od Forkliftu.
  - **Nautilus** (GPL-3.0+): ponuka iba cez Alt, stredné ťahanie je roky pokazené.
  - Ktorýkoľvek z nich by sme vedeli nainštalovať ako **druhý** správca súborov pre tých, čo ho poznajú.
    Predvolené však ostávajú Súbory.

### 7.2 Snímky obrazovky (PrtSc, Win+Shift+S, Cmd+Shift+4)
**Výber: vstavané snímky Noctalie** (MIT, už nainštalované v našom forku):
- `screenshot-region` (oblasť);
- `screenshot-fullscreen` (monitor / všetky);
- `screenshot-annotate` (zmrazí obrazovku a dá sa kresliť, potom kopírovať alebo uložiť, ako Výstrižky).

Skratky:
- **Win+Shift+S** a **PrtSc** = oblasť;
- **Win+PrtSc** = celá obrazovka do `~/Obrázky/Snímky obrazovky`;
- **Shift+PrtSc** = s kreslením;
- profil Mac: Cmd+Shift+3/4/5.

Nič netreba inštalovať a vzhľad sedí so shellom. ❓ Uloženie do priečinka a oznámenie s „Upraviť“ ešte overím.
- Alternatívy:
  - **grimblast** (MIT, COPR Hyprland) + **swappy** (MIT, Fedora): overená dvojica v Hyprlande, swappy na kreslenie;
    samostatné okná bez nášho vzhľadu.
  - **satty** (MPL-2.0): krajšie kreslenie ako swappy, nie je vo Fedore (cargo alebo COPR).
  - **hyprshot** (GPL-3.0): jednoduchý skript, iba snímka.
  - **Flameshot 14** (GPL-3.0+, Fedora): najbližšie k Windows Výstrižkom, veľa nástrojov. Qt aplikácia navyše, na
    Hyprlande ide cez portál a má občas problémy s viacerými monitormi.

### 7.3 Nahrávanie obrazovky (Win+Alt+R)
**Výber: wf-recorder** (MIT, Fedora) teraz, lebo kóduje na CPU a vo VM pôjde. Ovládanie: skratka + ikona v lište
počas nahrávania.
- Na počítači s GPU pribudne **gpu-screen-recorder** (GPL-3.0, COPR Hyprland) pre Herňu: spätný záznam „posledných
  30 s“ ako Xbox Game Bar / ShadowPlay, takmer bez straty výkonu.
- Alternatívy:
  - **OBS Studio** (GPL-2.0): všetko vie, ťažké;
  - **Kooha** (GPL-3.0): pekné GTK okno, ale iba cez portál a bez spätného záznamu;
  - **wl-screenrec** (Apache-2.0): rýchly, ale potrebuje GPU.

### 7.4 Alt+Tab
**Výber: prepínač okien Noctalie** (MIT, už je v shelli):
- podporuje „drž Alt, ťukaj Tab, pusti = prepni“;
- zoradenie podľa naposledy použitých (MRU).

Stačí skratka. Super+Tab ostáva prehľad pásky (Zobrazenie úloh).
- Alternatívy:
  - **hyprswitch** (MIT, GTK 4): viac nastavení, ďalšia aplikácia s iným vzhľadom;
  - holý Hyprland `cyclenext`: bez okna, iba prepína, pre Windows používateľa nečitateľné.

### 7.5 Kláves Win sám = Štart
**Výber: skratka Hyprlandu na pustenie klávesu Super** (`SUPER_L` s voľbou release) → `latte-spustac prepni` (App
Manager s hľadaním navrchu, ako Štart).
- ❓ Treba overiť, že sa nespustí po kombinácii (Super+E…). Hyprland to rieši voľbou „iba ak nebol stlačený iný kláves“.
  Ak nie, použijem malý pomocník.
- Alternatíva: Win otvorí **Text Bar** namiesto App Managera. To je bližšie Win11 (Štart = hľadanie) a macOS
  (Spotlight). Rozhodni ty (otázka nižšie).

### 7.6 Win+V, Win+., Win+I, multimediálne klávesy, Ctrl+Alt+Del, Win+X
- **Win+V → Kapsa** (naša, cliphist GPL-3.0). Plávajúce okno sa presunie na Super+Shift+V.
- **Win+. → emoji zo spúšťača Noctalie** (`panel-open launcher /emo`, MIT).
  - ❓ Overím, či emoji vloží priamo do okna. Ak iba kopíruje, doplním vloženie cez `wtype` (MIT, už je v systéme).
  - Alternatívy:
    - **Smile** (GPL-3.0): najkrajší výber emoji, Flatpak;
    - **bemoji** (MIT): skript nad spúšťačom;
    - **GNOME Characters** (Fedora): celé znaky, nie iba emoji.
- **Win+I → Nastavenia.** AI rozhovor sa presunie na Super+Shift+I alebo Super+C (ako Copilot vo Win11).
- **Prehrať / ďalšia / predošlá → `noctalia msg media`** (MIT, už je). Alternatíva: `playerctl` (LGPL-3.0, Fedora).
- **Ctrl+Alt+Del a Win+X:** vlastná ponuka v tvare L. Obsah:
  - Zamknúť, Prepnúť používateľa, Odhlásiť, Zmeniť heslo, Monitor;
  - pri Win+X navyše Správca zariadení, Terminál, Nastavenia, Vypnúť / Reštartovať.

  Win+X sa otvorí aj **pravým klikom na dlaždicu aplikácií** (ako pravý klik na Štart).
  - Alternatíva: **wlogout** (MIT), hotová ponuka vypnutia; iný vzhľad a iba vypínanie, nie Win+X.

### 7.7 Okná myšou: prichytenie k okrajom, ponuka titulku
- **Prichytenie k okrajom:** Hyprland to sám nevie.
  - **Výber: vlastné riešenie** nad naším `snap.lua` (rozloženia už máme):
    - pri ťahaní okna sa pri okraji ukáže priehľadný náhľad cieľa (vrstva Quickshell);
    - po pustení sa použije rozloženie: hore = maximalizovať, bok = polovica, roh = štvrtina;
    - ťahanie maximalizovaného okna ho obnoví.
  - Alternatívy:
    - **labwc** (GPL-2.0, náš SAFE režim) to vie natívne. V SAFE to iba zapneme.
    - **KWin** to vie, ale znamenal by celé KDE namiesto Hyprlandu.
- **Pravý klik na titulok:** hyprbars (BSD-3) dnes na každé tlačidlo myši reaguje rovnako.
  - **Výber: malá záplata** v `resources/patches/`: pravý klik zavolá ponuku LatteOS.
  - Obsah ponuky: Obnoviť, Minimalizovať, Maximalizovať, rozloženia, Vždy navrchu, Presunúť na plochu N, NET, Zavrieť.
  - Alternatíva: Alt+Medzerník bez záplaty (iba klávesnica).
- **Myš nad □ = rozloženia (Win11):** tá istá záplata (podržanie nad tlačidlom) → panel Win+Z.

### 7.8 Profily ovládania a kláves Cmd pre Mac
**Výber: profil v Baristovi a v Nastaveniach › Hardvér › Klávesnica.** Súbor
`~/.config/latteos/profil-ovladania` prepne skratky v `hyprland.lua`, správanie ťahania v Súboroch, fokus a horúce rohy.

Pre Mac treba navyše premapovať Cmd na Ctrl (Cmd+C kopíruje), no v termináli nie.

**Výber: xremap** (MIT, jeden Rust súbor):
- vie výnimky podľa aplikácie aj v Hyprlande;
- mapu Mac napíšem podľa Toshy.

Alternatívy:
- **Toshy** (GPL-3.0): hotová najúplnejšia mapa Mac pre stovky aplikácií, podporuje Hyprland. Je to však veľký
  Python balík s vlastnou službou a tray ikonou.
- **keyd** (MIT): celosystémový, veľmi spoľahlivý, ale bez výnimiek podľa aplikácie (Ctrl+C v termináli by prestalo
  ukončovať program). Vo Fedore nie je, iba COPR.
- **Kinto** (GPL-2.0): predchodca Toshy, hlavne pre X11.

### 7.9 Horúce rohy (Mac, GNOME)
**Výber: horúce rohy Noctalie** (MIT, vstavané, dnes vypnuté). Profil Mac/GNOME ich zapne, napríklad ľavý horný =
prehľad pásky.
- Pozor: dolné rohy sú u nás dlaždice lišty (App Manager, Zariadenia), preto iba horné rohy.
- Alternatíva: **waycorner** (MIT).

### 7.10 Súbory: Ctrl+Z, rýchly náhľad, F2, priečinky pri ťahaní
- **Ctrl+Z / Ctrl+Y:** vlastný denník operácií v `latte-tc` (presun, premenovanie, Kôš, nový priečinok, kópia →
  opačná akcia).
  - Alternatíva: **KIO FileUndoManager** (LGPL, KDE). Robí presne toto, ale potrebuje knižnice KDE a náš kód v Qt C++.
- **Rýchly náhľad (Medzerník):** v režime Forklift ukáže okno s náhľadom (obrázok, text, PDF, video snímka). Použijem
  Lister, ktorý už máme. V režime TC Medzerník ďalej označuje.
  - Alternatíva: **GNOME Sushi** (GPL-2.0+), náhľad pre Nautilus cez D-Bus. Dá sa volať aj zvonku, ale ťahá GTK
    a GStreamer a nemá náš vzhľad.
- **F2 = premenovať, F5 = obnoviť v režime Forklift**; v režime TC ostáva klávesnica TC. Pribudnú Alt+←→↑, bočné
  tlačidlá myši, Ctrl+Shift+N, Ctrl+F, Ctrl+L. Profil Mac pridá Enter = premenovať a Cmd+↓/↑.
- **Priečinok sa otvorí pri podržaní** (0,8 s) a **pri podržaní nad oknom v páske** sa okno prenesie dopredu.
  Obe veci sú vlastné.

### 7.11 Ostatné (P2)
- **Win+P:** vlastný rýchly výber (Iba tento / Duplikovať / Rozšíriť / Iba druhý).
  - Profily monitorov rieši **kanshi** (MIT, Fedora).
  - Alternatívy: **nwg-displays** (MIT, grafické rozloženie monitorov pre Hyprland), **wdisplays** (GPL-3.0, Fedora).
- **Lupa (Win+Plus/Mínus):** vstavaný zoom kurzora Hyprlandu (`cursor:zoom_factor`), netreba nič inštalovať.
- **Klávesnica na obrazovke:** **wvkbd** (GPL-3.0), ľahká, pre Hyprland. Alternatíva: **squeekboard** (GPL-3.0,
  z Phosh), väčšia.
- **Moderátor (čítačka):** **Orca** (LGPL-2.1+). Quickshell zatiaľ sprístupňuje obsah obmedzene, takže naše okná
  budú čítané iba čiastočne.
- **Diktovanie (Win+H):** neskôr s AI.
  - **whisper.cpp** (MIT) vie po slovensky, na CPU je pomalšie.
  - **nerd-dictation** (GPL-3.0, Vosk) je rýchle, ale slovenský model je slabý.
- **Pripnutie aplikácií na lištu** a **súbor na ikonu aplikácie:** vlastné (lišta a App Manager).

### 7.12 Myš s viacerými tlačidlami
- **Späť / Dopredu a koliesko v našich aplikáciách: vlastné, raz pre všetky.**
  - Spoločný komponent v `apps/common/` pridá bočné tlačidlá (`Qt.BackButton` / `Qt.ForwardButton`), Ctrl + koliesko,
    Shift + koliesko a naklonenie kolieska.
  - Súbory, Nastavenia, App Manager a Monitor ho iba použijú.
  - Cudzie aplikácie (Firefox, Discord…) to už vedia samy.
- **Ďalšie tlačidlá → akcie systému:** nová stránka **Nastavenia › Hardvér › Myš › Tlačidlá**.
  - Každé ďalšie tlačidlo (mouse:277 a vyššie, palec, „gesto“) dostane akciu: Prehľad pásky, App Manager, snímka,
    Kapsa, plocha, stlmiť mikrofón, klávesová skratka… Zapíše sa do skratiek Hyprlandu.
  - Vo **Windows profile** Späť/Dopredu ostanú aplikáciám (nič sa neprebíja).
- **DPI, profily v pamäti myši, RGB: Piper + libratbag** (GPL-2.0 / MIT, Fedora):
  - grafické nastavenie myší Logitech, Razer, SteelSeries, Roccat a ďalších;
  - v App Manager › Ovládače sa ponúkne, keď Správca zariadení nájde podporovanú myš.
- Alternatívy:
  - **input-remapper** (GPL-3.0, Fedora): ľubovoľné tlačidlo na klávesy aj makrá, pre každé zariadenie zvlášť.
    Silnejšie ako skratky Hyprlandu, ale vlastná služba (root) a vlastné okno.
  - **Solaar** (GPL-2.0): iba Logitech (Unifying/Bolt), batéria a tlačidlá MX myší, veľmi dobrý pre MX Master.
  - **OpenRGB** (GPL-2.0): iba osvetlenie, zato všetkých značiek naraz.
- **Stredný klik v texte (Windows profil):** vloženie označeného textu (Hyprland `middle_click_paste`) sa dá vypnúť.
  - Návrh: vo Windows profile **vypnúť** a vo Firefoxe zapnúť automatické rolovanie ako vo Windows.
  - V Linux profile nechať zapnuté.
- **Rýchlosť dvojkliku:** jedna voľba v Nastaveniach zapíše hodnotu pre Qt (`qt6ct`, „Double click interval“), pre GTK
  (`gtk-double-click-time` v `settings.ini`) aj pre naše aplikácie.
- **Nájsť kurzor (Ctrl):** krátky krúžok okolo kurzora vo vrstve Quickshell.
  - Alternatíva: Hyprland `cursor:zoom_factor` na chvíľu (zväčší celý obraz, nie iba kurzor).

### 7.13 Klávesnica ako zariadenie
- **Num Lock:** `numlock_by_default = true` iba na stolnom PC (typ šasi z `/sys/class/dmi/id/chassis_type`). Na
  notebooku bez numerickej klávesnice by zapnutý Num Lock mohol na starších strojoch meniť písmená na čísla. Voľba
  bude aj v Nastaveniach.
- **Opakovanie klávesu:** `repeat_rate` a `repeat_delay` Hyprlandu v Nastaveniach › Klávesnica, s poľom na
  vyskúšanie.
- **Kláves Menu / Shift+F10:** spoločná obsluha v `ContextMenu.qml`. Ponuka sa otvorí pri vybranej položke, nie
  pri kurzore.
- **Multimediálne a špeciálne klávesy:** všetky XF86 klávesy naviažem na príkazy Noctalie (`media`, `mic-mute`,
  `keyboard-backlight-*`) a na naše aplikácie (kalkulačka = Text Bar v režime počítania, domov = prehliadač).
- **Prilepené klávesy:** Hyprland ich nemá.
  - Neskôr cez **keyd** (MIT) s „oneshot“ modifikátormi alebo **xremap**, podľa toho, čo vyberieme pre Mac profil.

---

## 8. Poradie práce po potvrdení

| Krok | Obsah | Čas (odhad) |
|---|---|---|
| A | P0: Super+Shift+M, Super+Q, fokus kliknutím | 1 h |
| B | Skratky Windows: Alt+Tab, Alt+F4, Win, Win+V, Win+., Win+I, snímky, médiá, Ctrl+Alt+Del / Win+X ponuka | 3–4 h |
| C | Ťahanie súborov: ponuka pravým/stredným, prijímanie zvonku, Plocha von, pravidlo disku, klávesy, popis pri kurzore | 4–6 h |
| D | Súbory Forklift: F2/F5, Ctrl+Z, história Alt+←→, bočné tlačidlá, náhľad Medzerníkom, priečinky pri podržaní | 4–5 h |
| E | Okná: prichytenie k okrajom s náhľadom, záplata hyprbars (pravý klik, rozloženia nad □) | 4–6 h |
| F | Profily ovládania (Barista + Nastavenia), xremap pre Mac, horúce rohy | 3–4 h |
| G | Myš a klávesnica vo všetkých našich aplikáciách: Späť/Dopredu, Ctrl/Shift + koliesko, kláves Menu, Num Lock, XF86 klávesy | 3–4 h |
| H | Nastavenia myši: tlačidlá → akcie, rýchlosť dvojkliku, opakovanie klávesov, nájsť kurzor, Piper v App Manageri | 3–4 h |
| I | P2: nahrávanie, Win+P, lupa, klávesnica na obrazovke, pripnutie na lištu | podľa záujmu |

Každý krok overím v headless kompozitore a zapíšem do denníka. Skratky, ktoré menia správanie živej relácie
(`hyprland.lua`), sa načítajú hneď bez reštartu.

## 9. Čaká na tvoje rozhodnutie

1. **Kláves Win sám:** otvorí **App Manager** (ako Štart vo Win10) alebo **Text Bar** (hľadanie ako Win11 / Spotlight)?
2. **Predvolené ľavé ťahanie v Súboroch:** **ako Windows** (ten istý disk = presun, môj návrh) alebo ponechať
   **vždy kopírovať** (Total Commander)?
3. **Predvolený profil ovládania:** Windows (môj návrh, väčšina používateľov) alebo výber povinne v Baristovi?
4. **Super+Q:** v profile Windows **vypnúť** (môj návrh) alebo nechať aj tam, keď si naň zvykol?
5. Súhlasíš s výberom nástrojov v časti 7 (hlavne **xremap** namiesto Toshy a **wf-recorder** pre VM)?
6. **Stredný klik v texte** vo Windows profile vypnúť (môj návrh) a vo Firefoxe zapnúť automatické rolovanie?
7. **Bočné tlačidlá myši** majú ostať iba Späť/Dopredu v aplikáciách (môj návrh), alebo ich chceš vedieť priradiť aj
   systémovým akciám?
8. Poradie A → I, alebo chceš niečo skôr?

---

**Zdroje:** správanie Windows a macOS podľa dokumentácie Microsoftu a Apple a bežnej praxe. Linux:
[KDE Discuss: predvolená akcia pri ťahaní v Dolphine](https://discuss.kde.org/t/suggestion-option-to-make-move-the-default-drag-and-drop-action-in-dolphin/42550),
[Arch fórum: Thunar a ťahanie pravým tlačidlom](https://bbs.archlinux.org/viewtopic.php?id=154464),
[GTK #1512: stredné ťahanie v Nautile / Neme](https://gitlab.gnome.org/GNOME/gtk/-/work_items/1512).
Stav LatteOS: `hyprctl binds` na živej VM, `session/hypr/hyprland.lua`, `session/apps/{subory,plocha,kapsavyrez}.qml`,
`session/apps/data/FilePane.qml`, `noctalia msg --help` (fork latte-shell, MIT).
