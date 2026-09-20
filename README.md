# LatteOS 0.1 — Jihlavanka

Používateľské prostredie nad bežným Linuxom.
Skrýva vnútro Linuxu, zjednocuje aplikácie do jedného modelu
a nepredstiera ochranu, ktorú nemá.

## Stav
Prototyp. Prvý komponent: latte-files; lišta má prompt (hľadať, terminál, AI), oznámenia, manažér času a ikony na ploche.

## Spustenie
    python3 src/latte_files/app.py

Celá relácia (labwc, lišta pod systemd):
    tools/install-session.sh     # jednorazovo: jednotky a príkazy do ~/.config a ~/.local
    latteos-session              # z konzoly
    systemctl --user restart latte-shell   # reštart lišty pri vývoji

Práca ako správca v správcovi súborov (polkit), ako root:
    sh tools/install-admin.sh    # pomocník do /usr/libexec/latteos/ a polkit politika;
                                 # spustiť znova po zmene src/latte_files/latte-files-admin alebo fileops.py
Dialóg pre heslo zobrazuje latte-polkit, ktorý spúšťa session/labwc/autostart (nie systemd: polkit chce agenta v scope relácie).

Testy:
    python3 -m unittest discover -s tests

Vzhľad (Prispôsobenie): jedno miesto pre celé prostredie, pozri docs/nastavenia.md.
    latte-appearance set color.scheme light        # tmavý/svetlý režim, platí hneď (aj v bežiacich aplikáciách GTK4)
    latte-appearance set color.accent '#3A9BD9'    # vlastný akcent; reset ho vráti
    latte-appearance status | show | themes | profiles | apply | release
Služba latte-appearance (portál pre režim, akcent a písmo; gtk.css; rámy okien v labwc) sa spúšťa s reláciou.
Po `tools/install-session.sh` sa treba znovu prihlásiť alebo urobiť `systemctl --user restart xdg-desktop-portal`.
Vývoj bez inštalácie: tools/run-appearance.sh. Motívy: data/themes/<id>/theme.toml (vlastné v ~/.local/share/latteos/themes/).

Závislosti (Fedora), okrem GTK4, gtk4-layer-shell, labwc:
    udisks2 polkit                  pripájanie diskov a práca ako správca
    ffmpegthumbnailer               náhľady videí v zobrazení Miniatúry (fotky idú bez neho)
    kernel-modules-extra            ovládač disketovej mechaniky (modul floppy); bez disketovej
                                    mechaniky vo VM nie je potrebný

Prihlasovacia obrazovka (greetd + latte-greeter, gtkgreet ako záloha), ako root:
    dnf install greetd gtkgreet greetd-selinux
    sh tools/install-greeter.sh  # kód a dáta greetera sa KOPÍRUJÚ do /usr/local; spustiť znova po zmene
    systemctl set-default graphical.target && systemctl enable greetd
Vývoj greetera bez inštalácie a reštartu (v okne, proti simulovanému greetd; účty test/kava a guest):
    tools/run-greeter.sh

Vývoj: Ctrl+Alt+Backspace ukončí labwc a vráti prihlasovaciu obrazovku (pri riadnom ukončení
nezobrazí nič). V prihlasovaní je vľavo menu: vypnúť/reštartovať počítač a dve voľby dev buildu,
"Reštartovať LatteOS" (znovu načíta greetd) a "Ukončiť do konzoly" (multi-user.target, textový
režim). Z konzoly späť: latteos-start. Voľba relácie "Konzola (headless)" otvorí shell a po exit
sa vráti prihlásenie.

Ak relácia spadne, prihlasovanie vpravo ukáže kartu s dôvodom, v journale je zápis
(journalctl LATTEOS_KIND=crash) a podrobnosti dá príkaz:
    latteos-diag

Systémový manažér (tlačidlo napájania v lište) spúšťa session/latteos-logout ako samostatnú user službu:
labwc skončí čisto (labwc --exit, potrebuje LABWC_PID z labwc/autostart), latteos-session upratá a potom
"Odhlásiť" ukončí prihlásenie, ktoré vlastní greetd (aj konzolu, z ktorej si LatteOS spustil ručne), takže
sa ukáže prihlasovacia obrazovka. "Vypnúť" v dev builde prepne do textovej konzoly (multi-user.target);
bez hesla to ide len s pravidlom data/polkit/51-latteos-dev.rules (dáva ho install-greeter.sh, len dev),
inak sa po odhlásení ukáže prihlasovanie. Bez greetd je oboje len odhlásenie.

Tapeta: systémová je v data/wallpapers/ (používa ju prihlasovanie a plocha bez vlastnej tapety),
používateľská je súbor v priestore používateľa a jej cestu drží ~/.config/latteos/appearance.toml.
Tapetu nastavíš v Nastaveniach (Prostredie › Pozadie); z terminálu:
    latte-wallpaper set ~/Obrázky/moja.jpg [cover|contain|fill]    # zmena platí hneď
    latte-wallpaper reset                                           # späť na systémovú

Prompt v lište: malá ikona vľavo prepína režim (klik, koliesko myši alebo Ctrl+1/2/3): lupa hľadá súbory
a priečinky (domov a pripojené zväzky, bez diakritiky, Enter otvorí), znak konzoly spúšťa príkazy Linuxu
(výstup v popupe nad lištou, `cd` platí ďalej, Ctrl+C zastaví, vim/top/ssh/sudo sa otvoria v okne foot),
iskry sú AI. AI beží lokálne v LM Studiu (predvolene http://192.168.56.1:1234, použije sa načítaný model).
Nastavenie, ak je iné, v ~/.config/latteos/prompt.toml:
    ai_url = "http://192.168.56.1:1234"
    ai_model = "qwen/qwen3-4b-thinking-2507"     # nepovinné; bez neho model, čo je v LM Studiu načítaný
Časové pásma v manažéri času: ~/.config/latteos/clock.toml (zones = "Europe/London,Asia/Tokyo"), dajú sa
pridať aj v popupe. Oznámenia prijíma latte-shell na org.freedesktop.Notifications; skúška: notify-send "Ahoj" "text".
Ikony plochy sa berú z priečinka Plocha (~/Desktop, ak existuje).

Ďalší používatelia (arkay, kenshi): `su -c 'sh tools/create-users.sh'` (bežné účty, súkromný domov, vlastný Kôš; pozri docs/nastavenia.md).

## Komponenty
- latte-files      správca súborov so zväzkami
- latte-settings   Nastavenia systému (tlačidlo Nastavenia v menu napájania v lište; pozri docs/nastavenia.md)
- latte-devices    Správca zariadení: všetok hardvér po skupinách a monitory (latte_common/hardware.py, outputs.py, displays.py);
                   `latte-devices list`, `latte-devices display list|set|apply`
- latte-resources  Správca zdrojov (popup ZDROJE v lište): zariadenia a siete ako dlaždice po skupinách, tlačidlo Nastavenia v ramene L
- latte-apps       App Manager (plánované)
- latte-shell      lišta a plocha
- latte-polkit     dialóg na zadanie hesla správcu (polkit agent relácie)

## LatteOS 0.1 Jihlavanka — mapa vývoja
Od prvého kódu po hotové prostredie s Android a Windows aplikáciami Základ: Fedora Server + labwc + Python/GTK4 Stav dokumentu: pracovný plán, aktualizuje sa podľa postupu

Ako čítať mapu
Značka	Význam
✅	hotové
🔸	rozrobené
⬜	nezačaté
Každá etapa má overiteľný výsledok. Kým nie je splnený, ďalej sa nejde.

Etapa 0 — Spustenie systému a relácie ✅
Úloha	Stav
0.1	Po zapnutí počítača sa načíta Fedora a systémové služby	✅
0.2	Prihlasovacie menu ponúkne LatteOS ako Wayland reláciu	✅
0.3	Po prihlásení sa spustí labwc, environment a LatteOS desktop	✅
0.4	LatteOS shell sa spustí automaticky po štarte relácie	✅
0.5	Vývojové ukončenie relácie vráti používateľa do headless Linuxu	✅
Výsledok: po zapnutí a prihlásení sa spustí LatteOS bez ručného zadávania príkazov.
Vývojový výsledok: Ctrl+Alt+Backspace ukončí labwc a vráti systém do prihlasovacieho alebo textového režimu, aby spustené aplikácie nezavadzali pri úprave kódu.
ručny autostart je latteos-session alebo
/home/user/dev/jihlavanka001/session/latteos-session

Etapa 1 — Súbory ✅
Úloha	Stav
1.1	Zväzky z lsblk, mapovanie na Device1…N, volumes.toml	✅
1.2	Koreň „Tento počítač", hranice zväzkov, žiadny Linux	✅
1.3	Breadcrumb, história, šípky, domček	✅
1.4	Tri režimy zobrazenia, aktívny panel, Tab	✅
1.5	Otvorenie súboru, nový priečinok, premenovanie, kopírovanie, presun, Kôš	✅
1.6	Premenovanie zväzku pravým klikom	✅
1.7	Kontextové menu pravým klikom nad položkou	✅
1.8	Viacnásobný výber (Ctrl, Shift) a operácie nad ním	✅
1.9	Priebeh operácie (kopírovanie veľkých súborov, zrušenie)	✅
1.10	Vykonať ako správca cez polkit pri „prístup odmietnutý"	✅
1.11	Automatické obnovenie pri pripojení USB (udisks2 signály) — latte-storaged	✅
1.12	Obľúbené položky v bočnom paneli	✅
1.13	Štýly zobrazenia: Zoznam, Stredné ikony, Podrobnosti, Miniatúry (náhľady fotiek a videí, inak veľké ikony)	✅
1.14	Detekcia zdrojov dát: disky, USB, optická mechanika, disketa, zdieľané priečinky (latte_common/devices.py, prvá časť manažéra zariadení)	✅
Výsledok: správca súborov použiteľný na bežnú prácu bez terminálu.

Etapa 2 — Shell ✅ / 🔸
Úloha	Stav
2.1	Lišta ako layer-shell panel s rezervovaným miestom	✅
2.2	Rohové dlaždice, hodiny, tlačidlá	✅
2.3	Popupy v tvare L, zatvorenie klikom mimo, pripnutie do okna	✅
2.4	Zoznam otvorených okien v strede lišty (protokol wlr-foreign-toplevel)	✅
2.5	Systémový manažér: popup nad tlačidlom napájania (skryje sa, keď z neho odídeš kurzorom). Hotové: Vypnúť (relácia → konzola), Reštartovať (s potvrdením) a Odhlásiť (→ prihlásenie). Zostáva: nastavenia (čakajú na etapu 8)	🔸
2.6	Manažér času: hodiny → pásma, zvonček → oznámenia (Nerušiť), dátum → kalendár	✅
2.7	Oznámenia (démon org.freedesktop.Notifications) — latte-shell: bubliny vpravo hore, zoznam pod zvončekom, akcie, Nerušiť	✅ (overiť na živej zbernici: notify-send)
2.8	Prompt segment s prepínacou ikonou: hľadať v priečinkoch / príkazy Linuxu / AI (LM Studio)	✅
2.9	Schránka s ôsmimi slotmi — latte-clipd (preskočené: chce vlastného klienta wlr-data-control)	⬜
2.10	Plocha: tapeta ✅ (systémová + používateľská, mení sa za behu), ikony z ~/Desktop ✅, Kôš ✅ (otvorí jeho priečinok). Zostáva: kontextové menu, presúvanie ikon, obnovenie z Koša	🔸
2.11	Animované rohové dlaždice viazané na stav	⬜
Výsledok: prostredie, v ktorom sa dá pracovať celý deň bez cudzieho desktopu.

Etapa 2b — Relácia a prihlásenie 🔸
Základ: tenká vrstva nad systemd user službami. Reštarty, závislosti a poradie rieši systemd, latte-sessiond drží stav relácie a hovorí s prihlásením.

Úloha	Komponent	Stav
2b.1	Skript relácie s premennými (XDG_CURRENT_DESKTOP, LD_PRELOAD, GSK_RENDERER)	latteos-session	✅
2b.2	latteos.desktop v /usr/share/wayland-sessions/	—	✅
2b.3	Prihlasovacia obrazovka: vlastný latte-greeter (greetd), gtkgreet ako záloha	latte-greeter	✅
2b.4	systemd user jednotky pre každý komponent, latte-session.target	—	✅
2b.5	Stav relácie, odhlásenie, vypnutie, reštart (logind)	latte-sessiond	⬜
2b.6	Zamykanie obrazovky	latte-sessiond	⬜
2b.7	Uvítanie pri prvom prihlásení: čo sa spúšťa, čo beží na pozadí	latte-greeter	⬜
2b.8	Obnova otvorených okien po prihlásení (deklaratívne, nie snímka pamäte)	latte-sessiond	⬜
2b.9	Dôvod pádu relácie: journald, záznam, karta v prihlasovaní, latteos-diag, oznam v konzole (riadne ukončenie nič nezobrazí)	latteos-session	✅
2b.10	Prihlasovanie: nedávni používatelia, účet bez hesla sa prihlási hneď, napájacie menu, dev voľby	latte-greeter	✅ (overiť vo VM: SELinux, polkit)
2b.11	Panel oznamov v prihlasovaní: počasie, RSS, čo si používateľ povolí (cache plní samostatná služba, greeter sám nesťahuje)	latte-greeter	⬜
2b.12	latteos-start: z konzoly späť do grafiky	latteos-start	✅
Výsledok: prostredie sa spúšťa prihlásením, pád jedného komponentu nezhodí reláciu.

Etapa 3 — Vzhľad 🔸
Úloha	Stav
3.1	data/styles/latte.css — jedna téma pre všetky komponenty	✅
3.2	Paleta a typografia podľa prototypu (teplá káva, krémová, karamel)	🔸 (farby a polomery sú v motíve data/themes/latte/theme.toml, tmavý aj svetlý variant; typografia zostáva)
3.3	Vlastná sada ikon (~30 kusov)	⬜
3.4	Tapeta a prihlasovacia obrazovka v jednej téme (spoločné latte.css, widgety, tapeta)	✅
3.5	Polopriehľadné panely so šumom (náhrada za sklo, kým nie je vlastný kompozitor)	⬜
3.6	Kontrola prístupnosti: kontrast, veľkosť cieľov, viditeľnosť fokusu	🔸 (kontrast AA dodaných motívov a režim Vysoký kontrast; ciele a fokus zostávajú)
3.7	Prispôsobenie: jeden zdroj pravdy (appearance.toml + motív), služba latte-appearance, portál, gtk.css, rámy okien v labwc; docs/nastavenia.md	✅ (overené na GTK4/libadwaita)
3.10	Jedna výška záhlavia všetkých okien (window.titlebar) a jednotné tlačidlá minimalizovať/maximalizovať/zavrieť v komponentoch, libadwaita aplikáciách aj v rámoch od labwc	✅
3.8	Adaptéry pre GTK 3, Qt, Firefox, Chromium a Electron, Wine (stav: latte-appearance status)	⬜
3.9	Profily aplikácií: úroveň vynucovania a značka „vlastný vzhľad“ v prepínači okien (data/appearance-profiles/, dáta a načítanie hotové, zobrazenie v lište zostáva)	🔸
Výsledok: prostredie vyzerá ako jeden produkt, nie ako sada nástrojov. Vzhľad sa mení z jedného miesta a platí pre všetky okná, kde je to technicky možné; pre ostatné platí náhradné riešenie (rám od kompozitora, poctivá značka), nikdy filter, ktorý by zničil obsah.

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
8.9	Schéma systémových nastavení: jeden súbor na doménu, schémy a strom stránok v data/settings/ (latte_common/settings.py, docs/nastavenia.md)	✅
8.10	Aplikácia Nastavenia: okno skladané zo schém (Registry), stránka Prispôsobenie ako prvá	🔸
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
latte-deviced	zariadenia: kamera, tlačiareň, Bluetooth (detekcia diskov a zdieľaných priečinkov už je: latte_common/devices.py)	8
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