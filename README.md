# LatteOS 0.1 — Jihlavanka

Používateľské prostredie nad bežným Linuxom.
Skrýva vnútro Linuxu, zjednocuje aplikácie do jedného modelu
a nepredstiera ochranu, ktorú nemá.

## Stav
Prototyp. Prvý komponent: latte-files.

## Spustenie
    python3 src/latte_files/app.py

Celá relácia (labwc, lišta pod systemd):
    tools/install-session.sh     # jednorazovo: jednotky a príkazy do ~/.config a ~/.local
    latteos-session              # z konzoly
    systemctl --user restart latte-shell   # reštart lišty pri vývoji

Prihlasovacia obrazovka (greetd + gtkgreet), ako root:
    dnf install greetd gtkgreet greetd-selinux
    sh tools/install-greeter.sh
    systemctl set-default graphical.target && systemctl enable greetd

Vývoj: Ctrl+Alt+Backspace ukončí labwc a vráti prihlasovaciu obrazovku, v nej voľba
latteos-console otvorí textovú konzolu (po exit sa vráti prihlásenie).

## Komponenty
- latte-files      správca súborov so zväzkami
- latte-resources  mapa zdrojov (plánované)
- latte-apps       App Manager (plánované)
- latte-shell      lišta a plocha

## LatteOS 0.1 Jihlavanka — mapa vývoja
Od prvého kódu po hotové prostredie s Android a Windows aplikáciami Základ: Fedora Server + labwc + Python/GTK4 Stav dokumentu: pracovný plán, aktualizuje sa podľa postupu

Ako čítať mapu
Značka	Význam
✅	hotové
🔸	rozrobené
⬜	nezačaté
Každá etapa má overiteľný výsledok. Kým nie je splnený, ďalej sa nejde.

Etapa 0 — Základ ✅
Úloha	Stav
0.1	Fedora Server vo VirtualBoxe, snímky	✅
0.2	Git, GitHub, VS Code cez SSH	✅
0.3	labwc ako relácia, autoštart, environment v repozitári	✅
0.4	run-shell.sh s LD_PRELOAD pre layer-shell	✅
Výsledok: po prihlásení sa spustí prostredie bez ručného zadávania príkazov.

Etapa 1 — Súbory ✅ / 🔸
Úloha	Stav
1.1	Zväzky z lsblk, mapovanie na Device1…N, volumes.toml	✅
1.2	Koreň „Tento počítač", hranice zväzkov, žiadny Linux	✅
1.3	Breadcrumb, história, šípky, domček	✅
1.4	Tri režimy zobrazenia, aktívny panel, Tab	✅
1.5	Otvorenie súboru, nový priečinok, premenovanie, kopírovanie, presun, Kôš	✅
1.6	Premenovanie zväzku pravým klikom	✅
1.7	Kontextové menu pravým klikom nad položkou	✅
1.8	Viacnásobný výber (Ctrl, Shift) a operácie nad ním	⬜
1.9	Priebeh operácie (kopírovanie veľkých súborov, zrušenie)	⬜
1.10	Vykonať ako správca cez polkit pri „prístup odmietnutý"	⬜
1.11	Automatické obnovenie pri pripojení USB (udisks2 signály) — latte-storaged	⬜
1.12	Obľúbené položky v bočnom paneli	⬜
Výsledok: správca súborov použiteľný na bežnú prácu bez terminálu.

Etapa 2 — Shell ✅ / 🔸
Úloha	Stav
2.1	Lišta ako layer-shell panel s rezervovaným miestom	✅
2.2	Rohové dlaždice, hodiny, tlačidlá	✅
2.3	Popupy v tvare L, zatvorenie klikom mimo, pripnutie do okna	✅
2.4	Zoznam otvorených okien v strede lišty (protokol wlr-foreign-toplevel)	✅
2.5	Systémový manažér: vypnúť, reštart, odhlásiť, nastavenia	⬜
2.6	Manažér času: hodiny → pásma, zvonček → oznámenia, dátum → kalendár	⬜
2.7	Oznámenia (démon org.freedesktop.Notifications) — latte-shell	⬜
2.8	Prompt/search segment s prepínačom: hľadať / terminál / AI	⬜
2.9	Schránka s ôsmimi slotmi — latte-clipd	⬜
2.10	Plocha: tapeta, ikony, Kôš	⬜
2.11	Animované rohové dlaždice viazané na stav	⬜
Výsledok: prostredie, v ktorom sa dá pracovať celý deň bez cudzieho desktopu.

Etapa 2b — Relácia a prihlásenie 🔸
Základ: tenká vrstva nad systemd user službami. Reštarty, závislosti a poradie rieši systemd, latte-sessiond drží stav relácie a hovorí s prihlásením.

Úloha	Komponent	Stav
2b.1	Skript relácie s premennými (XDG_CURRENT_DESKTOP, LD_PRELOAD, GSK_RENDERER)	latteos-session	✅
2b.2	latteos.desktop v /usr/share/wayland-sessions/	—	✅
2b.3	Prihlasovacia obrazovka (greetd + gtkgreet, neskôr vlastná)	latte-greeter	✅
2b.4	systemd user jednotky pre každý komponent, latte-session.target	—	✅
2b.5	Stav relácie, odhlásenie, vypnutie, reštart (logind)	latte-sessiond	⬜
2b.6	Zamykanie obrazovky	latte-sessiond	⬜
2b.7	Uvítanie pri prvom prihlásení: čo sa spúšťa, čo beží na pozadí	latte-greeter	⬜
2b.8	Obnova otvorených okien po prihlásení (deklaratívne, nie snímka pamäte)	latte-sessiond	⬜
Výsledok: prostredie sa spúšťa prihlásením, pád jedného komponentu nezhodí reláciu.

Etapa 3 — Vzhľad 🔸
Úloha	Stav
3.1	data/styles/latte.css — jedna téma pre všetky komponenty	✅
3.2	Paleta a typografia podľa prototypu (teplá káva, krémová, karamel)	⬜
3.3	Vlastná sada ikon (~30 kusov)	⬜
3.4	Tapeta a prihlasovacia obrazovka (greetd + gtkgreet v téme)	⬜
3.5	Polopriehľadné panely so šumom (náhrada za sklo, kým nie je vlastný kompozitor)	⬜
3.6	Kontrola prístupnosti: kontrast, veľkosť cieľov, viditeľnosť fokusu	⬜
Výsledok: prostredie vyzerá ako jeden produkt, nie ako sada nástrojov.

Etapa 4 — App Manager, natívne aplikácie ⬜
Úloha
4.1	Zoznam nainštalovaných (.desktop + Flatpak), spúšťanie, štítky pôvodu
4.2	Inštalácia a odstránenie Flatpaku (flatpak cez D-Bus alebo príkaz)
4.3	Aktualizácie: systém (PackageKit) aj Flatpak na jednom mieste
4.4	Repozitáre: Flathub a vlastné, zapnutie a vypnutie
4.5	Mapa oprávnení nad flatpak permissions — zobraziť a odobrať
4.6	Prepínač siete pre kontajnerovú aplikáciu — latte-netd
4.7	Štítok SYSTÉM pri aplikáciách bez izolácie + ponuka kontajnerovej verzie
4.8	xdg-desktop-portal nainštalovaný a nastavený (systémové dialógy súborov)
Výsledok: používateľ nainštaluje, spustí a obmedzí aplikáciu bez terminálu. Míľnik: prvý bod manifestu, ktorý je skutočnou pridanou hodnotou v bezpečnosti.

Etapa 5 — Kontajnery a recepty ⬜
Úloha
5.1	Podman ako základ (bez roota, systemd integrácia)
5.2	Formát receptu: čo sa pýta, predvolené hodnoty, potrebné práva
5.3	Čítanie metadát obrazu (ExposedPorts, VOLUME)
5.4	Automatické pridelenie portov, konflikty rieši systém
5.5	Overenie po štarte: čo v kontajneri naozaj počúva
5.6	Čítanie známych chýb (EULA, chýbajúce práva) a ponuka riešenia
5.7	Import docker-compose.yml so štítkom „neoverený recept"
5.8	10 receptov na začiatok (Tailscale, torrent, Minecraft, Home Assistant…)
Výsledok: kontajnerová aplikácia beží po jednom kliknutí, bez experimentovania.

Etapa 6 — Android ⬜
Úloha
6.1	Waydroid: inštalácia, binder v jadre, overenie na skutočnom stroji
6.2	Inicializácia obrazu Androidu zo sprievodcu, nie z terminálu
6.3	Android aplikácia ako okno na ploche (Waydroid v režime jednotlivých aplikácií)
6.4	Zoznam Android aplikácií v App Manageri so štítkom ANDROID
6.5	Inštalácia .apk z App Managera
6.6	Navigačné tlačidlá (späť, domov, prehľad) a klávesové skratky
6.7	Prístup k súborom: zdieľaný priečinok medzi LatteOS a Androidom
6.8	Schránka naprieč systémami (LatteOS ↔ Android)
6.9	Sieť a jej vypnutie pre Android prostredie
Výsledok: Android aplikácia sa spúšťa a používa ako každá iná. Pozor: vo VirtualBoxe nepobeží dobre, testuje sa na skutočnom stroji.

Etapa 7 — Windows a hry ⬜
Úloha
7.1	Bottles alebo vlastná správa prefixov, jeden prefix na aplikáciu
7.2	Inštalácia .exe z App Managera, štítok WIN32
7.3	Odstránenie disku Z: z prefixu (aplikácia nevidí koreň)
7.4	Proton a Steam pre hry
7.5	Schránka naprieč systémami (LatteOS ↔ Wine)
7.6	Kompatibilitná databáza: čo funguje, čo nie, s čím sa netrápiť
7.7	Poctivé označenie neriešiteľných prípadov (cloudové licencie, anti-cheat)
Výsledok: Windows aplikácie a hry bežia tam, kde to je možné, a kde nie, systém to povie vopred.

Etapa 8 — Systémové nastavenia bez terminálu ⬜
Úloha
8.1	Wi-Fi, VPN, Bluetooth (NetworkManager, BlueZ)
8.2	Zvuk a hlasitosť v mape zdrojov (PipeWire) — latte-audiod
8.3	Tlačiarne (CUPS) — latte-deviced
8.4	Disky: pripojenie, odpojenie, formátovanie výmenných médií (udisks2)
8.5	Používatelia, heslá, jazyk, klávesnica, čas
8.6	Aktualizácie systému — latte-updated
8.7	Zálohovanie a obnova používateľských dát — latte-snapshotd (bez snapshotov, iba kópia)
8.8	Diagnostika: zobraziť chybu, ručne odoslať — latte-diagd
Výsledok: splnené kritérium „bežný používateľ nepotrebuje terminál ani raz".

Etapa 9 — Sprievodca a vydanie ⬜
Úloha
9.1	Zistenie schopností (Flatpak, Waydroid, KVM, Landlock) a ich zobrazenie — latte-probe
9.2	Otázky, tabuľky profilov, Setup Plan, schválenie — latte-wizard
9.3	Balíček (RPM) so všetkými komponentmi a reláciou
9.4	ISO obraz cez Fedora kickstart
9.5	Test na čistom stroji podľa 10 kritérií z manifestu
9.6	Dokumentácia pre používateľa a stránka projektu
Výsledok: LatteOS 0.1 Jihlavanka sa dá nainštalovať a odovzdať niekomu inému.

Komponenty zo špecifikácie 1.1 a ich miesto v Jihlavanke
Komponent	V Jihlavanke	Etapa
latte-files (nad rámec špecifikácie, vlastný pre 0.1)	správca súborov	1
latte-shell	lišta, popupy, oznámenia, plocha	2
latte-sessiond	relácia nad systemd user službami	2b
latte-greeter	prihlásenie a uvítanie	2b
latte-clipd	schránka	2 (9)
latte-appd → latte-apps	App Manager (Flatpak, PackageKit, Waydroid, Bottles)	4
latte-capd → latte-perms	mapa oprávnení nad Flatpakom; nie vlastný capability engine	4
latte-netd → latte-net	prepínač siete pre aplikáciu	4
latte-storaged → latte-resources	zväzky, pripojenie, USB, udisks2	1, 8
latte-deviced	zariadenia: kamera, tlačiareň, Bluetooth	8
latte-audiod	zvuk nad PipeWire	8
latte-translatord	výber prostredia: Flatpak / Waydroid / Bottles	4–7
latte-probe	zistenie schopností hostiteľa	9
latte-wizard	sprievodca a Setup Plan	9
latte-updated	aktualizácie	8
latte-diagd	diagnostika, čierna skrinka	8
latte-decoderd	náhľady súborov v sandboxe	odložené
latte-console	Service Console	nie v 0.1 (patrí k Release režimu)
latte-a11yd	prístupnosť, sémantický strom	nie v 0.1 (rieši GTK a AT-SPI)
latte-compositor	vlastný kompozitor	nie v 0.1 (labwc)
latte-execd, latte-radio@, latte-objectd	vysielačka, svety aplikácií, objekty	nie v 0.1 (Arabica)
latte-vmd	Level 3, VM	nie v 0.1 (Arabica)
latte-snapshotd	snapshoty a Kôš	Kôš v etape 1, snapshoty až s btrfs
latte-licensed	licencia	nie v 0.1 (Jihlavanka je zdarma)
latte-resourced	limity CPU a RAM pre aplikácie	odložené (cgroup cez systemd)
Pomenovanie: v Jihlavanke komponenty nenesú koncovku d, lebo to nie sú démony, ale bežné programy. Pri prechode na Arabicu sa meno vráti k tvaru zo špecifikácie.

Poradie a závislosti
Etapa 0 ✅
   ↓
Etapa 1 (Súbory)  ─┐
Etapa 2 (Shell)   ─┤→ Etapa 2b (Relácia) → Etapa 3 (Vzhľad)
                    ↓
              Etapa 4 (App Manager)
                    ↓
        ┌───────────┼───────────┐
        ↓           ↓           ↓
   Etapa 5      Etapa 6     Etapa 7
  (Kontajnery)  (Android)   (Windows)
        └───────────┼───────────┘
                    ↓
              Etapa 8 (Nastavenia)
                    ↓
              Etapa 9 (Vydanie)
Etapy 5, 6 a 7 sú nezávislé. Dajú sa robiť v ľubovoľnom poradí alebo striedavo, podľa chuti.

Čo sa dá odložiť bez straty
animácie a sklo (čakajú na vlastný kompozitor),
AI v prompte (bod 2.8 môže mať zatiaľ iba hľadanie a terminál),
schránka s ôsmimi slotmi (stačí systémová),
obľúbené položky, náhľady súborov, vyhľadávanie v súboroch.
Čo sa odložiť nedá
štítky pôvodu a ochrany pri každej aplikácii (bez nich sa porušuje pravidlo poctivosti),
odoberanie oprávnení, ktoré naozaj platí (bod 4.5),
overenie po štarte kontajnera (bod 5.5) — bez neho zostane experimentovanie s nastaveniami, teda presne to, čo Jihlavanka má odstrániť,
zobrazenie chýbajúcich schopností (bod 9.1) — tichá degradácia je zakázaná.
Prvé tri kroky od dneška
1.7 Kontextové menu — operácie už existujú, chýba len ich vyvolanie pravým klikom.
3.1 a 3.2 Téma — vytiahnuť CSS do data/styles/latte.css, kým sú komponenty dva.
2.4 Zoznam okien v lište — až potom je lišta naozaj lištou.
Hneď po nich 2b.1 až 2b.4, teda relácia a systemd jednotky. Čím skôr komponenty spúšťa systemd, tým menej sa budeš trápiť s ich reštartovaním pri vývoji.

Potom Etapa 4, ktorá je najväčším skokom v hodnote celého projektu.