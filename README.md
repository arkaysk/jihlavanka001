LatteOS Gamer Distro — Manifest
22. 9. 2026 · @Arkay
Premisa a cieľ
Projekt sa preto zužuje na konkrétny, zvládnuteľný cieľ: vlastná herná Linux distribúcia (v duchu Bazzite/SteamOS), kde je odlišnosť postavená na kombinácii známych súčiastok poskladaných po vlastnom, nie na jednej revolučnej myšlienke.
Škrtnuté zo zamerania:
• serveroví power-useri s nutnými špecifickými nástrojmi
• najslabšie firemné pracovné stanice (Excel, databázy)
Ponechané v zameraní:
• gaming, vrátane esportu a plnej podpory anti-cheatu
• moderný, vizuálne fluidný desktop
• hračovy/mainstreem uživatelovy windowsu ostane pohodlie a funkčnost, pribudne cool dizajn, nove schopnosti, lepši bezpečnost a ak nema vyvojarsku verziu, nulové sledovanie.
Základ systému
• Jadro: Linux
• Vzor: SteamOS 3 (Arch-based) a Bazzite (Fedora Atomic/Universal Blue) ako referenčné body — LatteOS gamerdistro ide podobnou cestou, nie kopírovaním.
Compositor a UI vrstva
• Fork Hyprlandu ako základ pre plynulý, animovaný desktop (inšpirácia: fluidnosť vo videách r/unixporn — bezier animácie, GPU-akcelerované efekty, priama kontrola nad kompozíciou cez Wayland).
• Zvažovaný stack: Slint + Rust + Smithay + Vulkan
    ◦ Smithay je Rust knižnica pre Wayland compository — čistá Rust cesta by znamenala písať compositor nad ňou od základu (roky práce); fork Hyprlandu (C++) je rýchlejšia cesta k požadovanej fluidnosti.
    ◦ Rust sa reálne oplatí nasadiť najprv na nadstavbové vrstvy: Setup Plan sprievodca, správa profilov, prekladačová logika — nie nutne v jadre compositora.
• Dôležité: fluidný desktop je vizitka (moderný, lákavý vzhľad), nie hlavný odlišovací prvok — ten je v bezpečnostnom/aplikačnom modeli (ďalšia sekcia).
Bezpečnostný a aplikačný model/Unikátne LatteOS veci
• Prekladač na aplikáciu ("weapon" = emulátor/runtime ako Wine/Proton/Android/FEX/QEMU, "radio" = kanál ku kernelu) — LatteOS píše manifest za aplikáciu, aplikácie si profil nežiadajú samé.
• Trusted / untrusted profily aplikácií:
    ◦ Steam v celku je predinštalovany a autmaticky ako trusted profil. bezpečnost jeho hier prichadza od neho.
    ◦ Hry s aktívnym anti-cheatom (BattlEye, EAC) potrebujú menej izolovaný, "trusted" beh — anti-cheat potrebuje viditeľnosť na vlastný proces a systém, čo bežný Flatpak sandbox (bubblewrap/namespaces) blokuje.
    ◦ Dôležité rozlíšenie: anti-cheat zamyká len svoj vlastný proces, nie celý systém — iné aplikácie (napr. Discord, prehliadač) môžu bežať vo Flatpaku súbežne bez problémov.
    ◦ EAC/BattlEye majú aj "Linux-native" režim (cez Proton, bez kernel-level ovládača z Windowsu) — beží ako bežný proces s právami používateľa; závisí od rozhodnutia vývojára hry, či ho zapne (zoznam: areweanticheatyet.com).
• NET tlačidlo na aplikáciu (vrátane Windows aplikácií cez Proton) ostáva súčasťou modelu.
• App Manager spravuje všetky aplikacie, updaty 
• ProcessManager (Monitor) spravuje aktivne ulohy, kopia windoes ctrl alt del menu s pridanou hodnotou : autoruns , hwinfo, cpuZ. 
• Device Manager spravuje hardware
• Session Manager bude cez mobilnu appku prenašač účtov. Bezpečne prihlasovanie sa s overenim a zaroven načitanie uloženeho profilu z internetoveho uložiska/usb sticku. zaroven bude spravovat uživatelov na instalovanom pc.
• Data Manager je suborovy manager vychadzajuci z Forklift pre Mac, rozširujuci funkčnost až na Total Commander. zaroven je to projekcia datovej štruktury, neprepisuje linux ani neskriva linux datovu štrukturu (var/ usr/ bin/ mnt/) ale dava jej windowslike podobu
• Wizzard je program ktory služi ostatnym procesom ako možnost, ponuka inštalacie. V zaklade pomocou offline tabulky ponuka zavislosti, čo instalovat s čím, ale ma aj offline aj online AI-da sa mu povedat co človek potrebuje za funkciu a on navrhne aplikaciu vratane celeho balika čo je nutne pre chod na linuxe. 
• Text Bar je lišta kde sa da rovnako ako  v win11 rychlo spustit app pisanim nazvu, okamžite ponuka a zaklade textu aplikacie, funkcie sytemu a vyhladavnanie medzi suborama či medzi help systemu, prepnut sa da na Ai prompter pre lokalnu instruct ai, kde sa da nastavit/vybrat model podla vlastnych preferencii, vratane stiahnuteho offline, až po api/chat modul pre online AI, pripadne vlatnu lokalnu vzdialenu(domaci server ), spravovat tokeny, spotrebu a iné.
• Clipboard manager Android to ma, ale zistil som že aj windows to ma, len to je skryte. tady to bude priamo sučastou dolnej lišty. 
  
Súborový systém a zobrazenie
• Reálna Linux adresárová štruktúra ostáva nezmenená pod kapotou — LatteOS pridáva len zobrazovaciu vrstvu nad ňou (analogicky ako Nautilus/Dolphin dnes stavajú na GVfs/udisks2).
• Cieľový vzhľad: štýl Windows "Tento počítač" — oddelené položky Systém, Disk1 Volume1/2, Disk2, CD-ROM, USB, zdieľané zložky, priamo z výstupu udisks2, nie nový súborový systém.
• Inštalácie aplikácií ostávajú po starom (rozhodnuté, neprepisovať):
    ◦ klasické balíky (RPM/DEB/pacman) sa neinštalujú do vlastnej zložky — rozhadzujú súbory podľa FHS,
    ◦ Flatpak už dnes má každú appku vo vlastnom priestore (/var/lib/flatpak/app/<app>/ alebo ~/.local/share/flatpak/app/...) — LatteOS to len zobrazí používateľovi ako samostatné položky/zložky v "Tento počítač" pohľade, fyzicky sa nič nemení,
    ◦ AppImage zostáva ako doplnkový formát (appka = súbor, spustiteľný odkiaľkoľvek).
Technologický stack (zhrnutie)
Vrstva
Voľba
Základ / distribúcia
Linux, štýl Bazzite (Fedora Atomic) alebo Arch (štýl SteamOS)
Compositor
Fork Hyprlandu (Wayland, wlroots)
UI / nadstavbové nástroje
Slint + Rust
Wayland vrstva (dlhodobo)
Smithay (Rust) — zvažované, nie nutné pre v0
Grafika
Vulkan
Hry
Steam natívne + Proton (trusted profil)
Android
Lepton (Waydroid-based)
Ostatné aplikácie
Flatpak (nezmenené, len inak zobrazené) + AppImage
Súborový manažér
Vlastná "This PC" zobrazovacia vrstva nad udisks2
Vývojové prostredie (aktuálne)
Fedora Server VM (Oracle VirtualBox, Windows host) — repo: github.com/arkaysk/jihlavanka001
Čo zostáva otvorené / ďalšie kroky
• Presná voľba distribučnej základne pre gamerdistro smer: Fedora Atomic (Bazzite štýl) vs. Arch (SteamOS štýl).
• Rozsah forku Hyprlandu — koľko meniť hneď, koľko nechať ako je.
• Definícia presných pravidiel trusted/untrusted (čo okrem Steamu/anti-cheat hier ešte spadá do trusted).
• Plán najbližšieho kroku: čistý git a nový VM image s Linuxom.
• 