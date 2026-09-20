# LatteOS Core API Manifest

**Projekt:** LatteOS  
**Repository:** arkaysk/jihlavanka001  
**Manifest:** LatteOSCoreAPImanifest.md  
**Cieľová verzia:** LatteOS 1.0 "Arabica"  
**Stav:** návrh Core API v0.1  
**Dátum:** september 2026

---

## 0. Účel

LatteOS je používateľská a systémová vrstva nad Linuxom, nie náhrada Linuxu. Preto musí vedieť integrovať aj štandardné Linuxové aplikácie, ktoré neboli vytvorené pre LatteOS.

Zásadné pravidlo:

> Ak aplikácia používa štandardné Linuxové rozhrania, LatteOS ju má podľa možností integrovať bez špeciálnej LatteOS verzie.

LatteOS preto nesmie vytvoriť druhý paralelný svet, v ktorom vlastné aplikácie používajú LatteOS API a ostatné aplikácie sú občania druhej kategórie.

---

# 1. Architektúra

Základný model:

    LatteOS UI
        ↓
    LatteOS Core API
        ↓
    ┌─────────────────────────────────────┐
    │ Linux / freedesktop / toolkit APIs │
    └─────────────────────────────────────┘
        ↓
    Linux

Core API je normalizačná vrstva. Nie je náhradou GTK, Qt, Waylandu, D-Bus, portals, XDG ani Linuxových oprávnení.

LatteOS má poskytovať UX a koordináciu, Linux má poskytovať štandardné backendy.

---

# 2. Princíp "Linux first, Latte second"

Pri návrhu každej funkcie sa použije toto poradie:

1. Ak existuje štandard Linux/freedesktop, použiť ho.
2. Ak toolkit poskytuje štandardné API, použiť ho.
3. Ak existuje vhodný desktop portal, použiť portal.
4. Ak Linux poskytuje backend, ale nie vhodné UX, LatteOS vytvorí UX nad ním.
5. Ak potrebná abstrakcia neexistuje, vytvorí sa LatteOS Core API.
6. Vlastný mechanizmus sa vytvára až ako posledná možnosť.

Toto pravidlo je záväzné pre Core API.

---

# 3. Zdroje pravdy

Každá systémová vlastnosť musí mať jeden zdroj pravdy.

Príklad vzhľadu:

    LatteOS Settings
          ↓
    appearance state
          ↓
    LatteOS Appearance Core
          ├── desktop portal
          ├── GTK adapter
          ├── Qt/KDE adapter
          ├── compositor adapter
          ├── icon/cursor adapter
          ├── Electron/Chromium adapter
          └── Firefox adapter

Adaptéry nesmú byť samostatnými zdrojmi nastavení.

---

# 4. Povinné integračné štandardy

| Oblasť | Preferovaný mechanizmus |
|---|---|
| Aplikácie | XDG Desktop Entry |
| MIME | XDG MIME associations |
| Predvolené aplikácie | XDG default applications |
| Spúšťanie | desktop entry / D-Bus activation / runtime launcher |
| Vzhľad | XDG Desktop Portal + toolkit-native nastavenia |
| GTK | GTK/GSettings/XDG |
| Qt | Qt/KDE štandardy |
| Ikony | freedesktop icon theme |
| Kurzory | Xcursor / toolkit integration |
| Fonty | Fontconfig + desktop/toolkit nastavenia |
| Notifikácie | D-Bus desktop notifications |
| Súbory | XDG user directories + MIME |
| Dokumenty | portals podľa sandboxu |
| Oprávnenia | portals / polkit / Linux permissions |
| Session | systemd/logind/greetd |
| Okna | Wayland + compositor protocols |
| Screenshot | Screenshot portal |
| Screencast | ScreenCast portal |
| File chooser | FileChooser portal |
| Sandbox | Flatpak/portal alebo Latte runtime |
| Hardware | Linux sysfs/udev/PCI a existujúce backendy |

LatteOS môže tieto mechanizmy skryť za jednotné používateľské rozhranie, ale nemá ich zbytočne nahrádzať.

---

# 5. Core API moduly

Prvá verzia má definovať minimálne tieto rozhrania:

- latte.app
- latte.appearance
- latte.settings
- latte.windows
- latte.storage
- latte.files
- latte.notifications
- latte.permissions
- latte.portals
- latte.runtime

Core API nemusí byť v 0.1 verejným API pre externých vývojárov. Je to stabilný interný kontrakt, ktorý zabráni vzniku prepojeného monolitu.

---

# 6. Application API

LatteOS musí rozlišovať aplikáciu od procesu.

Podporované typy:

- native Linux
- distribučný balík
- Flatpak
- AppImage
- LatteOS application
- Wine/Proton application
- Android application
- VM application

Aplikácia je objekt s minimálnymi vlastnosťami:

    AppID
    Name
    DesktopEntry
    Source
    Runtime
    Sandbox
    Windows
    State
    Capabilities

Shell nesmie byť dlhodobo správcom všetkých aplikácií cez priame subprocess volania.

Cieľová architektúra:

    latte-shell
        ↓
    latte-appd
        ↓
    native / Flatpak / Wine / Android / VM

Tým sa aplikácia stane objektom LatteOS, nie iba procesom, ktorý Shell náhodne spustil.

---

# 7. Appearance API

Toto je jedna z najdôležitejších častí Core API.

Zdrojom pravdy je používateľský stav LatteOS, napríklad:

    ~/.config/latteos/appearance.toml

Aktuálny Jihlavanka už obsahuje latte_common.appearance a službu latte-appearance. Tento základ sa má zachovať, ale rozšíriť z vzhľadu vlastných komponentov na orchestráciu vzhľadu celého desktopu.

Core model musí pracovať s významovými tokenmi, nie s jednotlivými hard-coded farbami.

Príklady:

    appearance.theme
    appearance.color.scheme
    appearance.color.accent
    appearance.color.transparency
    appearance.contrast
    appearance.font.family
    appearance.font.scale
    appearance.font.monospace
    appearance.icon.theme
    appearance.cursor.theme
    appearance.cursor.size
    appearance.shape.corners
    appearance.window.titlebar
    appearance.window.button-layout
    appearance.animation

Aplikácia má dostať význam "accent", nie priamo konkrétnu farbu.

---

# 8. Appearance adapters

## 8.1 Latte adapter

Pokrýva:

- Latte shell
- vlastné okná
- Settings
- File Manager
- Process Manager
- Devices
- greeter
- vlastné dialógy

Stav: enforced.

## 8.2 Compositor adapter

Aktuálne labwc:

- rámy okien
- titlebar
- window buttons
- menu
- OSD
- window switcher

Stav: enforced.

Core API však nesmie používať názvy typu labwc_theme_color. labwc je iba adapter.

## 8.3 GTK adapter

Musí podporovať:

- GTK 4
- libadwaita
- GTK 3
- GTK settings
- GSettings
- desktop portal

Cudzia GTK aplikácia nesmie vyžadovať úpravu zdrojového kódu.

## 8.4 Qt/KDE adapter

Musí riešiť:

- color scheme
- palette
- font
- icon theme
- cursor
- window behavior
- KDE color scheme
- Qt platform integration

LatteOS nemá vytvárať vlastný Qt fork.

## 8.5 Portal adapter

Je kritický pre aplikácie mimo LatteOS a najmä sandboxované aplikácie.

Má koordinovať podľa dostupnosti:

- Settings
- FileChooser
- OpenURI
- Screenshot
- ScreenCast
- ďalšie štandardné portal rozhrania

Sandboxovaná aplikácia nesmie dostať širší prístup iba preto, že ju chce LatteOS integrovať.

## 8.6 Electron/Chromium adapter

Electron aplikácie nie sú automaticky totožné s GTK aplikáciami. Adapter preto rieši systémový color scheme, podporované Electron/Chromium mechanizmy, ikony, fonty a ďalšiu dostupnú systémovú integráciu.

LatteOS nesmie agresívne patchovať používateľské konfigurácie aplikácie.

## 8.7 Firefox adapter

Firefox musí mať samostatný adapter. LatteOS nemá predpokladať, že všetko vyrieši GTK.

Používajú sa iba podporované systémové alebo aplikačné integračné mechanizmy.

---

# 9. Appearance ownership

Najdôležitejšie pravidlo pre synchronizáciu vzhľadu:

Nie každý konfiguračný súbor je majetkom LatteOS.

Každý adapter musí deklarovať spôsob vlastníctva:

- enforced
- managed
- aligned
- advisory
- unsupported

### Enforced

LatteOS vlastní výsledok.

Príklad: vlastné LatteOS CSS.

### Managed

LatteOS spravuje iba konkrétny blok alebo kľúče. Zvyšok súboru musí zostať nedotknutý.

### Aligned

LatteOS nastaví systémovú preferenciu, ale aplikácia ju môže modifikovať.

### Advisory

LatteOS iba poskytne preferenciu.

### Unsupported

LatteOS integráciu negarantuje.

Toto pravidlo je dôležitejšie než samotný theme engine, pretože zabraňuje poškodeniu cudzích Linuxových aplikácií.

---

# 10. GTK a Qt nie sú LatteOS aplikácie

LatteOS musí prijať fakt, že používateľ môže používať:

- LatteOS aplikáciu
- GNOME aplikáciu
- KDE aplikáciu
- Qt aplikáciu
- GTK aplikáciu
- Electron aplikáciu
- inú Linuxovú aplikáciu

Cieľom nie je prinútiť všetky aplikácie vyzerať pixelovo identicky.

Cieľom je zabezpečiť konzistentné systémové vlastnosti:

- dark/light
- accent
- font
- font scale
- icon theme
- cursor
- základné window behavior
- accessibility settings

Aplikácia môže mať vlastný layout, widgety, branding alebo aplikačné CSS.

Výsledkom má byť:

> jednotné desktopové prostredie bez uniformity všetkých aplikácií.

---

# 11. Icon Theme API

Core:

    appearance.icon.theme

Musí sa premietnuť cez štandardný Linuxový icon theme mechanizmus do:

- GTK
- Qt
- shellu
- File Managera
- desktopu
- ďalších aplikácií, ktoré štandard rešpektujú

LatteOS ikony musia mať štandardné názvy a fallback.

---

# 12. Cursor API

Core:

    appearance.cursor.theme
    appearance.cursor.size

Adaptery:

- Xcursor
- Wayland/toolkit integration
- GTK
- Qt

---

# 13. Font API

Core:

    appearance.font.family
    appearance.font.scale
    appearance.font.monospace

Musí sa podľa možností prejaviť v:

- GTK
- Qt
- libadwaita
- shell
- terminal
- LatteOS aplikáciách

LatteOS nemusí distribuovať vlastný font. Core určuje preferenciu.

---

# 14. Default Application API

LatteOS nesmie vytvoriť vlastnú databázu typu "PDF → latte-pdf".

Používa štandardný MIME/desktop-entry model.

Príklad:

    application/pdf
        ↓
    default desktop entry
        ↓
    selected application

Rovnako:

- text/plain
- image/png
- inode/directory
- http/https
- audio
- video
- archívy

Settings môže poskytnúť pohodlné GUI, ale výsledok musí zostať štandardnou Linuxovou konfiguráciou.

---

# 15. Window API

Core API musí abstrahovať konkrétny compositor.

Aktuálny prototyp používa Wayland a zwlr_foreign_toplevel_manager_v1. To je vhodné pre súčasný stav, ale Core API nesmie byť pomenované podľa tohto konkrétneho protokolu.

Minimálne operácie:

- enumerate windows
- identify application
- activate
- minimize
- restore
- maximize
- close request
- monitor/output association
- workspace association
- state changes

Model:

    Latte Window API
        ↓
    Wayland adapter
        ↓
    compositor

---

### Window placement, restoration and rules

LatteOS má podporovať dve odlišné vrstvy správania:

1. **Automatic restoration**
   - aplikácia si alebo compositor podľa možností pamätá posledný monitor/output, workspace a stav okna
   - pri opätovnom spustení sa aplikácia môže objaviť tam, kde bola naposledy používaná

2. **Explicit Window Rules**
   - používateľ môže definovať pravidlo pre konkrétnu aplikáciu alebo typ okna
   - napríklad monitor, workspace, veľkosť, maximalizáciu, fullscreen alebo always-on-top
   - pravidlo má vyššiu prioritu než automatická obnova, ak používateľ výslovne určil iné správanie

Window Rules teda nemajú duplikovať bežnú obnovu poslednej pozície. Sú to používateľom definované výnimky a preferencie.

### Window tiling

LatteOS má poskytovať integrované tiling rozhranie pre klasické aj produktívne viacokenné pracovné plochy.

Minimálne:
- vizuálne snap zóny
- rozdelenie obrazovky na viac oblastí
- automatické prispôsobenie okien zóne
- keyboard shortcuts
- multi-monitor
- workspace integration
- možnosť uložiť layout
- možnosť kombinovať tiling s klasickým voľným umiestnením okien

Tiling je súčasť Window API a shell UX, nie samostatný compositor fork.

### Always on top

Always-on-top má byť systémová window action dostupná z jednotného LatteOS window menu a podľa možností aj cez Window API.

---

# 16. Process API

Process Manager má zobrazovať reálne Linuxové procesy.

Core poskytuje:

- PID
- PPID
- UID
- user
- executable
- command
- CPU
- memory
- state
- start time
- application association

Proces a aplikácia nie sú to isté.

Jedna aplikácia môže mať viac procesov.

Preto Process Manager nesmie byť App Manager.

Privilegované operácie musia ísť cez broker/polkit a nie priamo z GUI.

---

# 17. Storage API

Core model:

    Volume
      stable ID
      display name
      filesystem
      mount state
      capacity
      free space
      permissions

Používateľské názvy ako Práca, Médiá a Archív sú prezentačná vrstva.

Stable ID musí zostať stabilné aj po premenovaní volume.

---

# 18. File API

Spoločné Core operácie:

- copy
- move
- rename
- delete
- trash
- restore
- conflict resolution
- progress
- cancel
- snapshots, ak sú podporované

File Manager nemá vlastniť vlastnú implementáciu týchto operácií. Rovnaké API musia používať aj budúce aplikácie a capability broker.

---

# 19. Notification API

Minimálny model:

    Notification
      app_id
      title
      body
      icon
      actions
      urgency
      timeout

Native aplikácie používajú štandardný Linuxový notification mechanismus. LatteOS určuje prezentáciu.

---

# 20. Settings API

Každá doména má:

    schema
    values
    defaults
    validation
    persistence
    change notification
    adapter synchronization

Príklady domén:

- appearance
- display
- sound
- network
- power
- input
- accessibility
- privacy
- applications
- storage

GUI nemá obsahovať business logiku jednotlivých subsystémov.

---

# 20A. Universal Search / Prompt Bar

LatteOS má mať jedno centrálne vstupné pole, ktoré nie je iba vyhľadávačom súborov.

Používateľ môže do rovnakého baru zadať napríklad:

    wifi

a dostať relevantné výsledky z viacerých zdrojov:
- aplikácie
- súbory
- Settings a konkrétne nastavenia
- systémové funkcie
- zariadenia
- posledné položky
- dostupné akcie

Search má používať jednotný index/registry model a nemá byť obmedzený na filesystem.

### Režimy vstupu

Ten istý UI prvok sa môže prepnúť medzi:

1. **Search mode**
   - aplikácie
   - súbory
   - nastavenia
   - systémové objekty
   - akcie

2. **AI Prompt mode**
   - zadanie príkazu lokálnej AI
   - AI pracuje nad povolenými LatteOS objektmi a capability modelom
   - AI nemá automaticky získavať nové oprávnenia

3. **Command mode**
   - priame zadávanie Linuxových príkazov
   - výsledok sa má zobrazovať ako terminálový výstup alebo bezpečne vykonaná systémová akcia podľa príslušných oprávnení

Tieto režimy používajú rovnaké vstupné miesto, ale majú odlišný execution model.

Search nesmie implicitne vykonávať deštruktívne akcie iba preto, že používateľ napísal text. Výsledok môže byť objekt, návrh akcie alebo explicitná požiadavka na vykonanie.

---

# 21. Configuration hierarchy

Poradie:

    System defaults
        ↓
    Distribution defaults
        ↓
    LatteOS defaults
        ↓
    User settings
        ↓
    Application-specific preferences

LatteOS nesmie bezdôvodne prepisovať aplikačné nastavenia.

Ak ide o štandardnú systémovú vlastnosť, LatteOS ju môže synchronizovať cez príslušný adapter.

---

# 22. Appearance drift

Aktuálna služba latte-appearance sleduje spravované súbory a obnovuje ich podľa nastavení.

Tento mechanizmus sa zachová, ale iba v rámci ownership pravidiel.

Napríklad GTK settings.ini môže obsahovať používateľské alebo aplikačné nastavenia, ktoré LatteOS nevlastní.

Preto sa má meniť iba spravovaný blok alebo konkrétne kľúče.

Nikdy nie celý cudzí konfiguračný súbor bez potreby.

---

# 23. Adapter manifest

Každý adapter má deklarovať približne:

    id
    name
    level
    supported API version
    supported appearance properties
    ownership mode
    runtime requirements
    diagnostic state

Príklad:

    GTK4
      color scheme = supported
      accent = supported
      font = supported
      font scale = supported
      icon theme = supported
      cursor = supported
      transparency = limited

Tým sa zabráni predstieraniu podpory.

---

# 24. Stav integrácie

Každá funkcia má mať stav:

- native
- adapter
- fallback
- unsupported
- error

Príklad:

    GTK4
      color scheme = native
      accent = native
      font = native
      transparency = fallback

Ak aplikácia vlastnosť nepodporuje, LatteOS ju nemá označiť ako úspešne aplikovanú.

---

# 25. Capability model

Pôvodný LatteOS koncept "access is object" zostáva.

LatteOS capability vrstva však nemá zbytočne nahrádzať existujúcu Linux security architektúru.

Hierarchia:

    LatteOS capability policy
        ↓
    Linux permissions
    polkit
    portals
    Flatpak sandbox
    Wine container
    Android container
    microVM

LatteOS poskytuje jednotný používateľský model, zatiaľ čo backend využíva najvhodnejší existujúci mechanizmus.

Príklad capability:

    source
    target
    rights
    validity
    origin

Používateľ môže povoliť aplikácii konkrétny dokument alebo priečinok bez toho, aby UI tvrdilo, že aplikácia získala celý disk.

---

# 26. Privileged operations

GUI nesmie priamo vykonávať privilegované operácie.

Napríklad:

    latte-process
        ↓
    Latte privileged service
        ↓
    polkit
        ↓
    system operation

Platí pre:

- cudzie procesy
- služby
- mount/unmount
- systémové nastavenia
- sieť
- zariadenia
- power management
- používateľské účty

---

# 27. Application Manager

App Manager nie je iba obchod s LatteOS aplikáciami.

Musí pracovať s:

- native packages
- Flatpak
- AppImage
- LatteOS applications
- Wine/Proton
- Android
- VM runtimes

Aplikácia musí mať:

- identitu
- zdroj
- verziu
- desktop entry
- ikonu
- runtime
- sandbox/isolation level
- capabilities
- update channel
- uninstall mechanism

Prvé backendy:

1. Fedora/native packages
2. Flatpak
3. AppImage

Neskôr:

4. Wine/Proton
5. Android
6. microVM

---

# 28. Application launch

Shell nesmie používať interné cesty typu "spusť konkrétny Python súbor".

Namiesto toho:

    user action
        ↓
    App Registry
        ↓
    AppID
        ↓
    runtime launcher
        ↓
    application

Vývojová fáza môže používať subprocess ako dočasný mechanizmus. Core API však musí odstrániť túto závislosť pred 1.0.

---

# 29. Repository architecture

Navrhovaná cieľová hranica:

    src/
      latte_core/
        app.py
        appearance.py
        settings.py
        windows.py
        storage.py
        files.py
        notifications.py
        permissions.py
        portals.py
        runtime.py

      latte_adapters/
        gtk.py
        qt.py
        portal.py
        compositor.py
        xdg.py
        electron.py
        firefox.py
        wine.py

      latte_services/
        appd/
        appearance/
        settings/
        permissions/

      latte_shell/
      latte_files/
      latte_settings/
      latte_devices/
      latte_process/

Toto je cieľová architektúra, nie požiadavka na okamžitý veľký refactor.

---

# 30. Migračné pravidlo

Funkčný kód sa nemá prepisovať iba kvôli estetike architektúry.

Postup:

    existujúca implementácia
        ↓
    identifikovať stabilné rozhranie
        ↓
    zabaliť Core API
        ↓
    presunúť volajúcich na API
        ↓
    odstrániť priamu závislosť

---

# 31. Roadmap k LatteOS 1.0 "Arabica"

## Fáza 0: Jihlavanka prototype

Cieľ:

- reálny Wayland session
- greetd
- session lifecycle
- labwc
- latte-shell
- desktop
- taskbar
- notifications
- File Manager
- Settings
- Device Manager
- Process Manager
- System Information
- základný Appearance service

Výstup:

> funkčný LatteOS desktop na reálnom Linuxe.

---

## Fáza 1: Core API 0.1

Prioritný ďalší krok.

Definovať:

- Application API
- Appearance API
- Settings API
- Window API
- Storage API
- File API
- Notification API
- Permission API
- Portal API
- Runtime API

Súčasne:

- ownership model
- adapter model
- API versioning
- error states
- application identity
- oddelenie shellu od launchovania aplikácií

Výstup:

> LatteOS Core API 0.1.

---

## Fáza 2: systémová integrácia

Cieľ:

> Nastavenie LatteOS ovplyvňuje celý desktop, nielen vlastné aplikácie.

Dokončiť:

- GTK 4
- libadwaita
- GTK 3
- Qt
- KDE
- XDG MIME
- default applications
- desktop entries
- icon themes
- cursor
- font integration
- portals
- compositor adapter

Výstup:

> Bežná Linuxová aplikácia sa po inštalácii správa ako prirodzená súčasť LatteOS bez LatteOS-specific úprav.

---

## Fáza 3: App Manager

Musí vedieť:

- vyhľadávanie
- inštaláciu
- odinštalovanie
- aktualizáciu
- spustenie
- zdroj
- runtime
- sandbox
- oprávnenia

Prvé backendy:

1. native packages
2. Flatpak
3. AppImage

---

## Fáza 4: Capability layer

Prvé capability:

- file read
- file write
- directory access
- removable device
- clipboard
- screen capture
- camera
- microphone
- network
- process control
- device access

Prvá implementácia má využívať existujúce Linuxové mechanizmy.

---

## Fáza 5: Runtime layer

### Native

Priama Linuxová aplikácia.

### Flatpak

Portal-based integrácia.

### Wine/Proton

Translation container so samostatnou hranicou.

### Android

Waydroid alebo neskorší podporovaný runtime.

### MicroVM

Pre aplikácie vyžadujúce vlastný kernel alebo vyššiu izoláciu.

---

## Fáza 6: Desktop completion

Pred 1.0 musí byť hotové:

- taskbar
- application launcher
- App Manager
- File Manager
- Settings
- notifications
- display management
- sound
- network
- power
- accessibility
- Process Manager
- Device Manager
- default applications
- startup applications
- session lifecycle
- multi-monitor
- workspaces
- keyboard shortcuts
- clipboard
- screenshot
- screen recording
- search

---

## Fáza 7: Stability

Pred beta:

- crash recovery
- structured logs
- diagnostics
- settings rollback
- atomic configuration writes
- safe display rollback
- compositor restart recovery
- shell restart recovery
- app launch failure handling
- corrupt configuration recovery

Každý Core modul musí mať testy.

---

## Fáza 8: Compatibility matrix

Testovať reprezentatívne kategórie:

### GTK
- GTK 3
- GTK 4
- libadwaita

### Qt
- Qt 5
- Qt 6
- KDE applications

### Packaging
- native package
- Flatpak
- AppImage

### Runtimes
- native
- sandboxed

### Application categories
- file manager
- text editor
- office suite
- image editor
- media player
- browser
- terminal
- archive manager
- PDF viewer
- system utility

Testovacím cieľom je toolkit a integračný mechanizmus, nie certifikácia konkrétnej značky.

---

## Fáza 9: Beta

Označenie:

    LatteOS 0.9 Beta

Podmienky:

- Core API stabilné
- Appearance adapters stabilné
- App Manager funkčný
- native Linux aplikácie fungujú
- Flatpak funguje
- základný AppImage funguje
- session recovery funguje
- permissions fungujú
- multi-monitor funguje
- upgrade mechanizmus otestovaný
- kritické zmeny majú rollback

---

## Fáza 10: Release Candidate

Označenie:

    LatteOS 1.0-rc1

Freeze:

- Core API
- settings schema
- application model
- capability model
- appearance token model
- storage model

Od tejto fázy sa nemenia základné architektonické princípy. Opravujú sa chyby a regresie.

---

# 32. LatteOS 1.0 "Arabica"

Arabica nemá znamenať "všetko je vlastné".

Má znamenať:

> LatteOS funguje ako konzistentná vrstva nad Linuxom.

## Session

- login
- logout
- restart
- shutdown
- crash recovery

## Shell

- desktop
- taskbar
- launcher
- notifications
- window list
- system area

## Applications

- native Linux
- Flatpak
- základný AppImage

## Appearance

- LatteOS
- GTK
- libadwaita
- GTK3
- Qt/KDE
- compositor
- icon theme
- cursor
- fonts
- dark/light
- accent
- accessibility contrast

## Files

- volumes
- copy/move
- trash
- MIME
- default application
- permissions

## System

- devices
- processes
- resources
- displays
- power
- network
- sound

## Security

- portals
- polkit
- sandbox awareness
- capability abstraction
- žiadne priame privilegované GUI operácie

---

# 33. Čo nemusí LatteOS 1.0 implementovať vlastnými silami

Nie je potrebné vytvárať:

- vlastný kernel
- vlastný compositor
- vlastný filesystem
- vlastný Wayland server
- vlastný toolkit
- vlastný browser
- vlastný office suite
- vlastný package manager
- vlastný init system

LatteOS má Linux spojiť do používateľsky konzistentného prostredia.

---

# 34. Čo je naopak jadrom LatteOS

LatteOS-specific majú zostať:

- shell
- desktop UX
- unified Settings
- App Manager
- application model
- capability UX
- permission UX
- file integration
- appearance orchestration
- cross-toolkit consistency
- runtime abstraction
- diagnostics
- recovery

---

# 35. Praktický scenár: zmena vzhľadu

Používateľ zvolí:

    Nastavenia → Vzhľad → Tmavý

Core zmení:

    appearance.color.scheme = dark

Appearance Core potom synchronizuje:

    Latte CSS
    portal
    GTK
    Qt
    compositor
    Electron/Chromium adapter
    Firefox adapter

Nie je cieľom prepísať desiatky náhodných konfiguračných súborov.

Ak určitá aplikácia vlastnosť nepodporuje:

    supported
    unsupported
    fallback
    error

LatteOS musí vedieť rozlíšiť tieto stavy.

---

# 36. Praktický scenár: inštalácia aplikácie

Používateľ nainštaluje aplikáciu.

    App Manager
        ↓
    package / Flatpak / AppImage
        ↓
    desktop entry
        ↓
    App Registry
        ↓
    Shell

Shell nepotrebuje vedieť, kde je binárka ani ako bola nainštalovaná.

Pozná:

    AppID
    Name
    Icon
    DesktopEntry
    Runtime
    State

---

# 37. Praktický scenár: otvorenie dokumentu

    File Manager
        ↓
    MIME type
        ↓
    Default Application API
        ↓
    App Registry
        ↓
    Runtime
        ↓
    Application

Ak je aplikácia native, Flatpak, Wine, Android alebo VM, používateľ nemusí poznať rozdiel.

---

# 38. Definition of Done: Core API 0.1

- [ ] Shell nemá závislosť na interných cestách konkrétnych aplikácií.
- [ ] Existuje App Registry.
- [ ] Settings používa stabilné domény.
- [ ] Appearance má jeden zdroj pravdy.
- [ ] GTK adapter je oddelený od Latte CSS.
- [ ] Qt adapter je oddelený od GTK.
- [ ] compositor je adapter.
- [ ] portal je samostatná vrstva.
- [ ] default applications používajú XDG.
- [ ] privileged operations idú cez broker/polkit.
- [ ] Process Manager rozlišuje proces a aplikáciu.
- [ ] File operations sú spoločné Core operácie.
- [ ] každý adapter deklaruje podporu.
- [ ] každý Core modul má testy.
- [ ] nevznikajú nové priame závislosti typu shell → konkrétna aplikácia.

---

### Definition of Done: extended system integration

- [ ] Universal Search vyhľadáva aplikácie, súbory, nastavenia a systémové objekty.
- [ ] Search bar má oddelený Search, AI Prompt a Command mode.
- [ ] AI nemôže rozširovať svoje capability iba spracovaním používateľského promptu.
- [ ] Command mode zachováva štandardné Linuxové oprávnenia a bezpečnostné hranice.
- [ ] Window Tiling funguje na jednom aj viacerých monitoroch.
- [ ] Explicit Window Rules sú oddelené od automatickej obnovy poslednej pozície.
- [ ] System Monitor má System Timeline.
- [ ] Security Center má Security Timeline.
- [ ] File Locksmith vie identifikovať používajúci proces podľa dostupnosti.
- [ ] Hardware Health je oddelený od Device Managera.
- [ ] diagnostika vie vysvetliť pozorované systémové problémy bez predstierania kauzality.

# 39. Definition of Done: Arabica 1.0

- [ ] systém sa dá nainštalovať
- [ ] používateľ sa prihlási
- [ ] shell sa spustí
- [ ] shell sa dá bezpečne reštartovať
- [ ] aplikácie sa dajú inštalovať
- [ ] aplikácie sa dajú odstrániť
- [ ] native Linux aplikácie fungujú
- [ ] Flatpak aplikácie fungujú
- [ ] základné AppImage aplikácie fungujú
- [ ] GTK aplikácie rešpektujú systémový vzhľad
- [ ] Qt aplikácie rešpektujú systémový vzhľad
- [ ] dark/light je konzistentný
- [ ] font scale je konzistentný
- [ ] icon/cursor theme je konzistentný
- [ ] window management je konzistentný
- [ ] MIME associations fungujú
- [ ] File Manager používa štandardné associations
- [ ] notifikácie fungujú
- [ ] multi-monitor funguje
- [ ] základné permissions fungujú
- [ ] privileged actions sú chránené
- [ ] konfigurácia sa dá obnoviť
- [ ] kritické zmeny majú rollback
- [ ] diagnostika vie identifikovať problém
- [ ] Core API je verzované
- [ ] kompatibilita je testovaná

---

# 40. Záverečný princíp

LatteOS má byť:

    Linux
      +
    freedesktop standards
      +
    GTK / Qt / ďalšie toolkit integrácie
      +
    Wayland
      +
    sandbox / portals
      +
    LatteOS Core API
      +
    LatteOS UX
      =
    LatteOS

A pri vydaní Arabica má platiť:

> Ak aplikácia funguje na štandardnom Linuxe a používa štandardné Linuxové rozhrania, LatteOS ju má vedieť zaradiť do svojho prostredia bez toho, aby jej vývojár musel písať špeciálnu verziu pre LatteOS.

Toto je hranica medzi témou nad Linuxom a skutočným desktopovým operačným prostredím.


---

# 41. Rozšírenie platformy podľa IDEAS.md

## 41.1 Live Wallpaper API

LatteOS má natívne podporovať živé pozadie ako prvotriedny desktopový objekt, nie ako hack spúšťajúci okno pod ostatnými oknami.

Podporované režimy:
- statické pozadie
- animované pozadie
- video
- interaktívne pozadie
- viacmonitorové pozadie
- workspace-specific pozadie

Core má riešiť FPS limit, spotrebu GPU/CPU, pozastavenie pri fullscreen aplikácii a úsporný režim.

Model:
    Wallpaper Provider → Latte Wallpaper API → Desktop / Output

Externý provider môže byť samostatná aplikácia.

## 41.2 Latte System Defender

LatteOS má obsahovať vlastnú doplnkovú bezpečnostnú vrstvu založenú predovšetkým na behaviorálnej analýze.

Má sledovať podľa dostupných oprávnení napríklad:
- neobvyklý rast počtu procesov
- náhle masové čítanie alebo prepisovanie súborov
- podozrivé šifrovanie dokumentov
- neobvyklú CPU/GPU záťaž
- správanie typické pre mining
- nové alebo meniace sa autorun položky
- neobvyklé sieťové spojenia
- manipuláciu s inými procesmi
- spúšťanie binárnych súborov z neobvyklých umiestnení
- zmeny kritických systémových súborov
- náhle zmeny oprávnení

Stavy:
    known / trusted / unknown / suspicious / blocked / confirmed malicious

Neznámy proces nesmie byť automaticky označený za malware. Defender má poskytovať rizikové signály, dôkazy a vysvetlenie.

Model:
    Process / File / Network telemetry
        ↓
    Latte Defender
        ↓
    Risk assessment
        ↓
    User notification
        ↓
    optional containment

Má využívať existujúce Linuxové mechanizmy tam, kde sú vhodné, napríklad systemd, audit, fanotify/inotify, podpisy balíkov, Flatpak sandbox a portals. Automatické blokovanie musí byť konzervatívne, auditovateľné a vratné.

## 41.3 Latte Security Center

Defender má mať používateľské centrum zobrazujúce:
- stav ochrany
- posledné udalosti
- podozrivé procesy a súbory
- autorun zmeny
- sieťové anomálie
- sandbox/capability udalosti
- vykonané zásahy
- dôvod zásahu
- možnosť obnovy

Každá udalosť má obsahovať: what, why, source, evidence, risk, action, recovery.

## 41.4 Heidelberg

Heidelberg je natívny LatteOS dokumentový viewer/editor.

Natívne editovanie:
- TXT, MD, JSON, XML, HTML, CSS, CSV, TOML, YAML

Štruktúrované dokumenty:
- RTF, ODT, DOC/DOCX podľa parsera

Čítanie/import:
- EPUB, MOBI, PDF

Obmedzená externá podpora:
- Apple Pages

Ak LatteOS nevie formát kvalitne editovať, má radšej ponúknuť import/export alebo externú aplikáciu než predstierať plnú kompatibilitu.

## 41.5 Latte Basic Apps

### Core
- text/document viewer
- text editor
- calculator
- image viewer
- screenshot
- archive manager
- terminal
- system information
- system monitor
- settings

### Essential/Optional
- calendar
- tasks
- notes
- media player
- PDF reader
- ebook reader

Nemusia byť všetky súčasťou minimálneho base image. App Manager môže poskytovať oficiálny LatteOS Essential Apps balík.

## 41.6 Games

LatteOS môže mať oficiálny voliteľný balík open-source alebo inak legálne redistribuovateľných hier.

Quake II je kandidát iba podľa konkrétnej licencie a redistribuovateľnosti dát. Ak je redistribuovateľný engine, ale nie herné dáta, App Manager môže ponúknuť engine a vyžiadať si vlastné dáta používateľa.

## 41.7 Media integration

LatteOS nemusí vytvárať vlastný prehrávač len kvôli značke. Má však poskytovať jednotnú systémovú integráciu pre:
- media keys
- MPRIS
- notifikácie
- artwork
- panel/media controls
- fullscreen state
- power behavior

VLC a ďalšie kompatibilné prehrávače sa tým môžu správať ako prirodzená súčasť desktopu bez LatteOS-specific verzie.

## 41.8 Calendar, Tasks a Wellbeing

LatteOS môže poskytovať API služby pre:
- Calendar: udalosti, pripomienky, časové pásma, notifikácie
- Tasks: úlohy, termíny, priority, pripomienky
- Wellbeing: čas aktívneho používania, čas v aplikáciách, fullscreen/session čas, pracovné bloky, prestávky, voliteľné limity

Tieto služby majú byť API-first.

---

# 42. Latte System Monitor 2.0

Existujúci Process Manager nemá byť kópiou Windows Task Managera. Má kombinovať:
- Task Manager
- Autoruns
- CPU-Z
- HWiNFO
- základný system monitoring
- diagnostiku

Device Manager zostáva samostatný.

### Processes
- strom procesov
- proces → aplikácia
- CPU, RAM, GPU, VRAM podľa dostupnosti
- disk I/O, network I/O
- command line, executable path
- package/source
- runtime
- sandbox
- parent/children
- user/system/helper classification

### Autorun
Zjednotiť:
- XDG autostart
- systemd user/system services
- systemd timers
- cron podľa dostupnosti
- session hooks
- Flatpak autostart

Pri každej položke zobrazovať pôvod, vlastníka, definíciu, príkaz, typ a bezpečnosť zásahu.

### Resources
- krátka história
- CPU load
- disk throughput a IOPS podľa dostupnosti
- network throughput
- GPU load a memory
- teploty
- ventilátory
- spotreba
- swap
- batéria

### Hardware correlation
    Application → Process → GPU/device → thermal/power effect

System Monitor a Device Manager sa tým prepoja dátami, ale zostanú samostatnými nástrojmi.

### Diagnostics
Detail procesu môže podľa dostupnosti zobrazovať executable, package, signature/source, runtime, sandbox, parent/children, startup origin, network/file/hardware activity a security events.

---

# 42A. System Monitor 2.0: timelines, consumers and diagnostics

### System Timeline

System Monitor má poskytovať časovú os systémových udalostí a zmien zdrojov.

Má prepájať podľa dostupnosti:
- spustenie a ukončenie procesu
- zmenu CPU/RAM/GPU záťaže
- diskové a sieťové špičky
- zmeny teploty a spotreby
- autorun zmeny
- bezpečnostné udalosti
- zmeny zariadení
- kritické systémové udalosti

Cieľom nie je vytvoriť iba log viewer. Timeline má umožniť spätne pochopiť súvislosti, napríklad:

    spustená aplikácia
        ↓
    zvýšenie GPU load
        ↓
    zvýšenie teploty
        ↓
    zvýšenie otáčok ventilátora

Udalosti musia mať zdroj a čas. Ak je kauzalita iba odhadovaná, UI ju nesmie prezentovať ako dokázaný fakt.

### Security Timeline

Security Center má nad udalosťami Defendera poskytovať samostatnú časovú os bezpečnostných udalostí.

Príklad reťazca:

    stiahnutý súbor
        ↓
    spustenie
        ↓
    vytvorenie autorun položky
        ↓
    masové zmeny súborov
        ↓
    neobvyklá CPU záťaž
        ↓
    Defender alert

Timeline má zobrazovať jednotlivé pozorované udalosti, ich zdroj, dôkazy a vykonané opatrenie. Nemá spätne vytvárať falošnú istotu o príčine iba na základe časovej blízkosti.

### File Locksmith / What is using this?

Pri operácii, ktorá zlyhá preto, že objekt používa iný proces, má LatteOS ponúknuť informačný dialóg namiesto všeobecného:

    Retry / Cancel

Dialog má podľa dostupnosti uviesť:
- ktorý proces objekt používa
- PID
- aplikáciu
- používateľa
- otvorený súbor alebo resource
- ako dlho je resource používaný

Ponúknuté akcie môžu byť:
- retry
- cancel
- focus/activate application
- zobraziť proces v System Monitor
- bezpečne ukončiť proces, ak to oprávnenia dovoľujú

Rovnaký mechanizmus sa má použiť aj pre všeobecnú funkciu **What is using this?** pre súbory, zariadenia a ďalšie systémové objekty.

### Application Repair

App Manager/System Monitor môže ponúknuť diagnostickú opravu aplikácie:
- overenie inštalácie
- kontrola dostupnosti runtime
- kontrola základných oprávnení
- reset LatteOS-managed konfigurácie
- diagnostický report

User data nesmie byť odstránené implicitne.

### Installation Source Transparency

Pri každej aplikácii má byť zrozumiteľne viditeľné:
- odkiaľ pochádza
- aký package/runtime používa
- či je podpísaná alebo overiteľná
- úroveň izolácie
- požadované capability
- autorun/persistence
- aktualizačný zdroj

Používateľ nemá byť nútený rozumieť rozdielu medzi native package, Flatpak, AppImage alebo Wine kontajnerom, ale LatteOS mu nesmie tieto rozdiely zatajiť.

### Dependency Inspector

Pre aplikácie má byť možné zobraziť podľa dostupnosti:
- runtime
- shared libraries
- grafické backendy
- fonty
- portály
- závislosti balíka
- reverse dependencies

Cieľom je vysvetliť, prečo aplikácia funguje alebo zlyháva, nie vytvoriť druhý package manager.

### Advanced Power Profiles

LatteOS má poskytovať systémové power profiles nad existujúcimi Linux backendmi:
- Performance
- Balanced
- Quiet
- Battery Saver
- Custom

Pravidlá môžu reagovať napríklad na:
- napájanie zo siete/batérie
- fullscreen aplikáciu
- konkrétnu aplikáciu
- nečinnosť

LatteOS nemá obchádzať kernel/driver power management vlastnými nebezpečnými mechanizmami.

### Hardware Health Center

Device Manager odpovedá na otázku **čo je v počítači**.

Hardware Health odpovedá na otázku **v akom stave to je**.

Podľa dostupnosti:
- SSD/HDD SMART
- teplota a health
- opotrebovanie/TBW
- chybové počítadlá
- GPU teplota/hotspot
- VRAM
- GPU fan/power/clocks
- CPU frekvencia/teplota/package power
- thermal throttling
- RAM a ďalšie relevantné health údaje

Táto vrstva sa má opierať o existujúce Linuxové backendy a nemá duplikovať Device Manager.

### Why is my PC slow?

System Monitor môže ponúknuť diagnostický workflow, ktorý koreluje:
- CPU
- RAM
- swap
- disk
- GPU
- teploty/throttling
- background processes
- startup
- storage health

Výstup má byť vysvetlenie pozorovaných príznakov a relevantných dôkazov, nie nepriehľadné jednočíselné skóre.

### Session Snapshot / Work Session

LatteOS môže ukladať pracovný kontext:
- otvorené aplikácie
- okná
- workspace
- monitor
- window layout
- podporované taby/dokumenty
- wallpaper/session state

Obnova závisí od toho, čo aplikácia a desktopový štandard podporujú. LatteOS nemá predstierať, že vie obnoviť stav, ktorý aplikácia neposkytuje.

---

# 43. Ďalšie kandidáty pre LatteOS

### Desktop
- clipboard history
- universal search / prompt bar
- recent files
- global shortcut manager
- workspace manager
- window tiling
- explicit window rules
- always-on-top
- per-monitor/per-application scaling
- night light/color temperature
- screen profiles
- session restore
- session snapshot / work session
- system timeline
- universal search
- recent files
- global shortcut manager
- workspace manager
- window tiling
- window rules
- per-monitor/per-application scaling
- night light/color temperature
- screen profiles
- session restore

### Files
- batch rename
- File Locksmith / What is using this?
- application repair integration
- dependency/source inspection
- file tags
- colored folder labels
- saved searches
- duplicate finder
- storage analyzer
- checksum/hash
- snapshots
- previous versions
- undo history

### System
- graphical service manager
- graphical firewall frontend
- backup center
- update center
- driver/device information
- advanced power profiles
- Hardware Health Center
- battery health
- disk health/S.M.A.R.T.
- boot diagnostics
- recovery environment
- "Why is my PC slow?" diagnostics
- graphical firewall frontend
- backup center
- update center
- driver/device information
- power profiles
- battery health
- disk health/S.M.A.R.T.
- boot diagnostics
- recovery environment

### Security
- application permissions center
- Security Timeline
- sandbox viewer
- executable trust information
- package signature information
- firewall integration
- security event history
- removable-media policy
- USB device trust
- suspicious autorun detection
- ransomware behavior detection

### Productivity
- notes
- tasks
- calendar
- focus mode
- wellbeing
- clipboard
- quick capture
- document preview
- universal recent-items system

### Hardware / enthusiast
- CPU topology
- NUMA information where applicable
- RAM details
- PCI topology
- USB topology
- storage health
- SMART
- GPU details
- sensors
- supported fan control
- power consumption
- display EDID/details
- audio devices
- network adapter details

---

# 44. Prioritization toward Arabica

### Arabica Core
Funkcie potrebné na kompletné desktopové prostredie.

### Arabica Essential Apps
Malé systémové aplikácie, ktoré používateľ očakáva okamžite.

### Arabica Plus
Výrazné LatteOS-specific funkcie:
- System Defender
- rozšírený System Monitor
- Live Wallpaper
- Universal Search / Prompt Bar
- Window Tiling
- Window Rules
- System Timeline
- Security Timeline
- File Locksmith / What is using this?
- Hardware Health Center
- wellbeing
- pokročilé file tools
- diagnostika
- Installation Source Transparency

### Future
- Android
- Wine/Proton
- microVM
- pokročilý capability broker
- hardware-specific integrations
- pokročilá AI integrácia
