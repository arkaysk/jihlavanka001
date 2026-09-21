# LatteOS — plán vývoja

Od prvého kódu po prostredie, v ktorom fungujú hry, náročné aplikácie, Android a Windows programy.
Cieľ vydania: **LatteOS 1.0 „Arabica“**. Dnešný stav: **0.1 „Jihlavanka“**, prototyp.

Zásady, na ktorých plán stojí, sú v [README.md](README.md). Rozbor jadrovej vrstvy je
v [CoreAPImanifest.md](CoreAPImanifest.md) (doplnkový návrh, z ktorého plán preberá len to,
čo má overiteľný výsledok).

## Ako čítať

| Značka | Význam |
|---|---|
| ✅ | hotové |
| 🔸 | rozrobené |
| ⬜ | nezačaté |

Každá etapa má overiteľný výsledok. Kým nie je splnený, ďalej sa nejde.

Etapy s číslom (0 až 9) sú pôvodné a ich čísla sa nemenia, pretože na ne odkazuje
`data/settings/index.toml` (pole `etapa`). Nové etapy majú preto písmeno: **H** hardvér,
**J** jadro, **P** procesy a monitor. Milníky sú **M1** a **M2**.

---

## Milníky

| Milník | Podmienka | Stav |
|---|---|---|
| **0.1 Jihlavanka** | prostredie sa dá nainštalovať a odovzdať niekomu inému (etapa 9) | 🔸 |
| **M1 — overenie na strojoch** | na viacerých skutočných počítačoch fungujú hry a náročné aplikácie | ⬜ |
| **0.9 Beta** | jadro stabilné, App Manager funkčný, obnova a oprávnenia fungujú | ⬜ |
| **M2 — zmrazenie** | jadro, schéma nastavení a model aplikácií sa už nemenia | ⬜ |
| **1.0 Arabica** | LatteOS funguje ako konzistentná vrstva nad Linuxom | ⬜ |

M1 je bod, ktorý si projekt vytýčil ako kontrolu v polovici cesty: dovtedy sa vyvíja hlavne
vo virtuálnom stroji, od M1 sa každá ďalšia etapa overuje na skutočnom hardvéri.

---

## Poradie a závislosti

    Etapa 0 (Relácia) ✅
       ↓
    Etapa 1 (Súbory) ✅ ─┐
    Etapa 2 (Shell) 🔸  ─┤→ Etapa 2b (Relácia a prihlásenie) 🔸 → Etapa 3 (Vzhľad) 🔸
                          ↓
                   Etapa H (Hardvér a základ) ⬜   ← nová priorita
                          ↓
                   Etapa J (Jadro) ⬜
                          ↓
                   Etapa 4 (App Manager) ⬜
                          ↓
                   ══ M1: overenie na strojoch, hry ══
                          ↓
            ┌─────────────┼─────────────┐
            ↓             ↓             ↓
       Etapa 5       Etapa 6       Etapa 7
      (Kontajnery)   (Android)     (Windows)
            └─────────────┼─────────────┘
                          ↓
                   Etapa 8 (Nastavenia) 🔸
                          ↓
                   Etapa P (Monitor) 🔸
                          ↓
                   Etapa 9 (Vydanie) ⬜

Etapy 5, 6 a 7 sú nezávislé, dajú sa robiť v ľubovoľnom poradí. Etapa P beží priebežne,
už je rozrobená. Bod **7.4 (Proton a Steam)** sa z etapy 7 vyťahuje dopredu, do M1: Steam si
Proton nesie sám a na test hier nepotrebuje vlastnú správu prefixov z bodov 7.1 až 7.3.

---

## Etapa 0 — Spustenie systému a relácie ✅

| | Úloha | Stav |
|---|---|---|
| 0.1 | Po zapnutí počítača sa načíta Fedora a systémové služby | ✅ |
| 0.2 | Prihlasovacie menu ponúkne LatteOS ako Wayland reláciu | ✅ |
| 0.3 | Po prihlásení sa spustí labwc, environment a LatteOS desktop | ✅ |
| 0.4 | LatteOS shell sa spustí automaticky po štarte relácie | ✅ |
| 0.5 | Vývojové ukončenie relácie vráti používateľa do headless Linuxu | ✅ |

**Výsledok:** po zapnutí a prihlásení sa spustí LatteOS bez ručného zadávania príkazov.
Ručný autostart: `latteos-session`.

---

## Etapa 1 — Súbory ✅

| | Úloha | Stav |
|---|---|---|
| 1.1 | Zväzky z lsblk, mapovanie na Device1…N, volumes.toml | ✅ |
| 1.2 | Koreň „Tento počítač“, hranice zväzkov, žiadny Linux | ✅ |
| 1.3 | Breadcrumb, história, šípky, domček | ✅ |
| 1.4 | Tri režimy zobrazenia, aktívny panel, Tab | ✅ |
| 1.5 | Otvorenie súboru, nový priečinok, premenovanie, kopírovanie, presun, Kôš | ✅ |
| 1.6 | Premenovanie zväzku pravým klikom | ✅ |
| 1.7 | Kontextové menu pravým klikom nad položkou | ✅ |
| 1.8 | Viacnásobný výber (Ctrl, Shift) a operácie nad ním | ✅ |
| 1.9 | Priebeh operácie (kopírovanie veľkých súborov, zrušenie) | ✅ |
| 1.10 | Vykonať ako správca cez polkit pri „prístup odmietnutý“ | ✅ |
| 1.11 | Automatické obnovenie pri pripojení USB (signály udisks2) | ✅ |
| 1.12 | Obľúbené položky v bočnom paneli | ✅ |
| 1.13 | Štýly zobrazenia: Zoznam, Stredné ikony, Podrobnosti, Miniatúry | ✅ |
| 1.14 | Detekcia zdrojov dát: disky, USB, optika, disketa, zdieľané priečinky | ✅ |
| 1.15 | Bočný panel: farba popisu priečinka, skutočné premenovanie nesystémových priečinkov, zväzky len alias ([docs/lista-a-rohy.md](docs/lista-a-rohy.md), časť 6) | ⬜ |

**Výsledok:** správca súborov použiteľný na bežnú prácu bez terminálu.

---

## Etapa 2 — Shell 🔸

| | Úloha | Stav |
|---|---|---|
| 2.1 | Lišta ako layer-shell panel s rezervovaným miestom | ✅ |
| 2.2 | Rohové dlaždice, hodiny, tlačidlá | ✅ |
| 2.3 | Popupy v tvare L, zatvorenie klikom mimo, pripnutie do okna | ✅ |
| 2.4 | Zoznam otvorených okien v strede lišty (wlr-foreign-toplevel) | ✅ |
| 2.5 | Systémový manažér: vypnúť, reštartovať, odhlásiť. Zostáva prepojenie na Nastavenia | 🔸 |
| 2.6 | Manažér času: pásma, oznámenia, kalendár | ✅ |
| 2.7 | Oznámenia (`org.freedesktop.Notifications`): bubliny, zoznam, akcie, Nerušiť | ✅ overiť na živej zbernici |
| 2.8 | Prompt s prepínaním režimov: hľadanie, príkazy Linuxu, AI | ✅ |
| 2.9 | Schránka s ôsmimi slotmi — `latte-clipd` (chce vlastného klienta wlr-data-control) | ⬜ |
| 2.10 | Plocha: tapeta ✅, ikony z ~/Desktop ✅, Kôš ✅. Zostáva kontextové menu, presúvanie ikon, obnovenie z Koša | 🔸 |
| 2.11 | Dekoratívne rohové dlaždice: kroky R1 až R5 hotové (rozmery, kmeň L, scény, prevody a svetlo, vlastný GIF/WebP). Zostáva strihač videa | 🔸 |
| 2.12 | **Kontextové menu pravým tlačidlom ako systémové pravidlo:** každý objekt, nad ktorým sa dá niečo urobiť, má menu. V iných systémoch je to samozrejmosť, v LatteOS je zatiaľ takmer nevyužité (dnes len v správcovi súborov a v mapách). Jedno spoločné menu, jeden vzhľad, jedno miesto v kóde | ⬜ |
| 2.13 | **Plocha, pravé tlačidlo na prázdne miesto:** Nový priečinok, Nový súbor (podľa typu, aj zoznam), Prilepiť, Zoradiť, Obnoviť, Vlastnosti. Nastavenie obrazovky a tapety tu **nie je** — patrí do Nastavení, kde je dobre dostupné | ⬜ |
| 2.14 | **Plocha, pravé tlačidlo na ikonu:** Otvoriť, Otvoriť v aplikácii, Vystrihnúť, Kopírovať, Premenovať, Zmazať (do Koša), Detaily. Operácie už existujú v `fileops.py`, chýba ich vyvolanie | ⬜ |
| 2.15 | **Lišta úloh, zobrazenie položiek:** ikona a popis verzus len ikona, správanie pri takmer prázdnej lište (nerozťahovať položky na celú šírku) a pri preplnenej (zhromaždiť okná jednej aplikácie pod jednu položku, potom skracovať popis, až nakoniec len ikony) | ⬜ |
| 2.16 | **Lišta úloh, ovládanie okna pravým tlačidlom:** Zavrieť, Minimalizovať, Obnoviť, Maximalizovať, Vždy navrchu, Presunúť na plochu alebo monitor. Zavrieť, minimalizovať a maximalizovať vie protokol wlr-foreign-toplevel, ktorý už používame; ostatné treba overiť | ⬜ |
| 2.17 | **Náhľad okna pri prejdení kurzorom** nad položkou v lište, vrátane minimalizovaného okna. **Najprv overiť, či to ide:** minimalizované okno sa nekreslí a `wlr-screencopy` snímkuje výstup, nie okno; snímka jedného okna potrebuje `ext-image-copy-capture-v1` a podporu v labwc. Ak to nejde, náhľad bude ikona, názov a poctivá informácia, nie falošný obrázok | ⬜ |

**Výsledok:** prostredie, v ktorom sa dá pracovať celý deň bez cudzieho desktopu.

**Pravidlo k bodom 2.12 až 2.17:** ak je nejaká funkcia v iných systémoch bežná a tu chýba, neznamená to,
že je nepotrebná. Znamená to, že sa o nej nerozhodlo, a treba ju prebrať s vlastníkom projektu.

---

## Etapa 2b — Relácia a prihlásenie 🔸

Tenká vrstva nad systemd user službami. Reštarty a poradie rieši systemd, `latte-sessiond` drží
stav relácie a hovorí s prihlásením.

| | Úloha | Komponent | Stav |
|---|---|---|---|
| 2b.1 | Skript relácie s premennými (XDG_CURRENT_DESKTOP, GSK_RENDERER) | latteos-session | ✅ |
| 2b.2 | `latteos.desktop` v `/usr/share/wayland-sessions/` | — | ✅ |
| 2b.3 | Prihlasovacia obrazovka: `latte-greeter` nad greetd, gtkgreet ako záloha | latte-greeter | ✅ |
| 2b.4 | systemd user jednotky pre komponenty, `latte-session.target` | — | ✅ |
| 2b.5 | Stav relácie, odhlásenie, vypnutie, reštart (logind) | latte-sessiond | ⬜ |
| 2b.6 | Zamykanie obrazovky | latte-sessiond | ⬜ |
| 2b.7 | Uvítanie pri prvom prihlásení: čo sa spúšťa, čo beží na pozadí | latte-greeter | ⬜ |
| 2b.8 | Obnova otvorených okien po prihlásení (deklaratívne, nie snímka pamäte) | latte-sessiond | ⬜ |
| 2b.9 | Dôvod pádu relácie: journald, karta v prihlasovaní, `latteos-diag` | latteos-session | ✅ |
| 2b.10 | Prihlasovanie: nedávni používatelia, účet bez hesla, napájacie menu, dev voľby | latte-greeter | ✅ overiť vo VM: SELinux, polkit |
| 2b.11 | Panel oznamov v prihlasovaní: počasie, RSS (cache plní služba, greeter nesťahuje) | latte-greeter | ⬜ |
| 2b.12 | `latteos-start`: z konzoly späť do grafiky | latteos-start | ✅ |

**Výsledok:** prostredie sa spúšťa prihlásením, pád jedného komponentu nezhodí reláciu.

---

## Etapa 3 — Vzhľad 🔸

| | Úloha | Stav |
|---|---|---|
| 3.1 | `data/styles/latte.css`: jedna téma pre všetky komponenty | ✅ |
| 3.2 | Paleta a typografia podľa prototypu (teplá káva, krémová, karamel) | 🔸 farby a polomery sú v motíve, typografia zostáva |
| 3.3 | Vlastná sada ikon (~30 kusov) | ⬜ |
| 3.4 | Tapeta a prihlasovacia obrazovka v jednej téme | ✅ |
| 3.5 | Polopriehľadné panely so šumom (náhrada za sklo) | ⬜ |
| 3.6 | Prístupnosť: kontrast, veľkosť cieľov, viditeľnosť fokusu | 🔸 kontrast AA a Vysoký kontrast hotové |
| 3.7 | Jeden zdroj pravdy: `appearance.toml` + motív, služba, portál, gtk.css, rámy labwc | ✅ overené na GTK4/libadwaita |
| 3.8 | Adaptéry pre GTK 3, Qt, Firefox, Chromium a Electron, Wine | ⬜ |
| 3.9 | Profily aplikácií: úroveň vynucovania a značka „vlastný vzhľad“ v prepínači okien | 🔸 dáta hotové, zobrazenie zostáva |
| 3.10 | Jedna výška záhlavia a jednotné tlačidlá okien vo vlastných komponentoch, libadwaite aj v rámoch labwc | ✅ |
| 3.11 | Živá tapeta: kódovaná scéna alebo GIF, rovnaký stroj scén ako lišty | ⬜ |
| 3.12 | **Bočná lišta od vrchu až dole.** Priehľadná bočná lišta ide cez celú výšku okna vrátane pásu hlavičky, nezačína pod ňou. Šípky späť a vpred, názov, hľadanie a tlačidlá okna začínajú až vpravo od nej. Dnes to tak nie je: všetky tri okná používajú `Gtk.HeaderBar` + `set_titlebar()`, takže hlavička ide cez celú šírku | ⬜ |
| 3.13 | **Bočná lišta ako všeobecný vzor pre všetky okná LatteOS:** raz rozkladacie menu (Nastavenia), raz zoznam diskov a obľúbených priečinkov (Súbory), raz rýchly prístup k funkciám (editor textu alebo obrázkov). Jeden komponent, nie tri kópie | ⬜ |
| 3.14 | **Miesto pre prepínač NET v hlavičke** vedľa hľadania, vľavo od tlačidiel min/max/zavrieť. Najprv len placeholder; funkciu dodá bod 8.1 | ⬜ |

**Výsledok:** prostredie vyzerá ako jeden produkt. Vzhľad sa mení z jedného miesta a platí pre všetky
okná, kde je to technicky možné; inde platí náhradné riešenie (rám od kompozitora, poctivá značka),
nikdy filter, ktorý by zničil obsah.

**Poznámka k bodu 3.12.** Vedú k nemu dve cesty a treba sa rozhodnúť:
*(a) vzhľadová* — hlavička zostane v `set_titlebar()`, ale jej ľavý úsek v šírke bočnej lišty bude
priehľadný a s rovnakým podkladom, takže panel vyzerá ako jeden celok od vrchu až dole; ťahanie okna,
zmena veľkosti a tlačidlá okna fungujú ako dnes.
*(b) štruktúrová* — okno bez hlavičky, vnútri vpravo `Gtk.WindowHandle` s `Gtk.WindowControls`;
bočná lišta je skutočne celovýšková a presne podľa obrázka, ale treba overiť ťahanie a najmä zmenu
veľkosti okna bez dekorácií.
Odporúčam začať cestou (a) a ak zostane viditeľný spoj, prejsť na (b). Platí to len pre vlastné okná
LatteOS; rámy, ktoré kreslí labwc cudzím aplikáciám, takto zmeniť nemožno.

---

## Etapa H — Hardvér a základný systém ⬜

Nová etapa. Vychádza zo zásady 7: ovládače majú byť pripravené dopredu, nie ako reakcia na to,
že používateľovi niečo nefunguje. „Najnovšie“ znamená **najnovšie stabilné**, nie testovacie.
Nič sa neinštaluje potajomky a vždy sa dá vrátiť (Fedora drží viac kernelov).

| | Úloha | Stav |
|---|---|---|
| H.1 | Metabalík `latteos-base`: firmvér, grafika, zvuk, vstup, sieť, Bluetooth, tlač, portály, Flatpak, fwupd. Jeden zoznam pre všetky stroje | ⬜ |
| H.2 | Stav hardvéru podľa zariadenia v Správcovi zariadení: funguje / chýba firmvér / chýba balík / treba cudzí repozitár / nepodporované. Samostatný modul, aby detekcia zostala len na čítanie | ⬜ |
| H.3 | Grafika a 3D: Mesa pre Radeon a Intel, proprietárny ovládač pre GeForce (stabilná vetva z RPM Fusion nonfree, akmod), Vulkan, 32-bitové ovládače pre Steam, Secure Boot a podpis modulu (MOK) | ⬜ |
| H.4 | Zvuk: PipeWire, WirePlumber, `alsa-ucm`, `alsa-sof-firmware`; overiť výstup, vstup a HDMI | ⬜ |
| H.5 | Vstupné zariadenia cez libinput: klávesnice, touchpady, gamepady, tablety (`libwacom`), mapovanie tabletu na obrazovku | ⬜ |
| H.6 | Firmvér zariadení cez `fwupd`, vrátane zobrazenia v Nastaveniach (Softvér › Aktualizácie) | ⬜ |
| H.7 | Doplnenie chýbajúceho z rozhrania: PackageKit alebo dnf s potvrdením cez polkit, aj pri hot-plug udalosti z udev. Cudzí repozitár len s výslovným súhlasom | ⬜ |
| H.8 | Hardvérový report v `latteos-diag`: porovnateľný výstup zo skúšobných strojov (PCI, USB, zvuk, vstup, GPU, ovládače, firmvér) | ⬜ |
| H.9 | Prenosné verzus strojové nastavenia: motív a písmo idú s používateľom, rozloženie obrazoviek podľa EDID, zvukové zariadenie a mapovanie tabletu zostávajú stroju | ⬜ |

**Výsledok:** po inštalácii LatteOS na nový počítač fungujú 3D grafika, zvuk, sieť, vstupné zariadenia
a tlač bez toho, aby používateľ čokoľvek dopĺňal. Čo fungovať nemôže, systém vopred pomenuje.

**Poznámka k vývojovému stroju:** vo virtuálnom stroji sa toto overiť nedá (virtio hardvér).
H.1 až H.9 sa uzatvárajú až na skutočných počítačoch v M1.

---

## Etapa J — Jadro ⬜

Jadrová podpovrchová vrstva. Nevytvára sa od nuly: dnešný `src/latte_common/` už túto úlohu plní
(nastavenia, vzhľad, hardvér, procesy, súborové operácie, zväzky). Etapa J z neho urobí stabilný
kontrakt a doplní, čo chýba. Premenovanie na `latte_core` sa odkladá až za M2, aby sa funkčný kód
neprepisoval pre estetiku architektúry.

| | Úloha | Stav |
|---|---|---|
| J.1 | **App Registry:** aplikácia ako objekt (AppID = desktop-id, názov, ikona, runtime, pôvod, stav) nad `Gio.DesktopAppInfo` | ⬜ |
| J.2 | Shell prestane spúšťať aplikácie cez `subprocess.Popen([sys.executable, cesta])` (dnes 4 miesta v `latte_shell/app.py`); pribudne test, ktorý zlyhá pri novej priamej závislosti shell → aplikácia | ⬜ |
| J.3 | Vlastníctvo cudzích konfigurácií ako samostatná os (enforced, managed, aligned, advisory, unsupported) oddelene od zrelosti adaptéra; zosúladiť s `ADAPTERS` v `appearance.py` | ⬜ |
| J.4 | Väzba proces → aplikácia v `processes.py` (cgroup alebo desktop entry); Správca procesov zostáva správcom procesov, nie aplikácií | ⬜ |
| J.5 | Okná ako adaptér: dnešný `foreign_toplevel.py` schovať za rozhranie, ktoré nenesie názov protokolu; tiling a pravidlá okien sú generovaná konfigurácia kompozitora, nie operácie shellu | ⬜ |
| J.6 | Prenos a verzovanie: rozhodnúť knižnica verzus D-Bus služba, zaviesť verziu rozhrania a chybové stavy (funguje, náhradné riešenie, nepodporované, chyba) | ⬜ |
| J.7 | Privilegované operácie výhradne cez broker a polkit, nikdy priamo z rozhrania (vzor: `latte-files-admin`) | 🔸 platí pre súbory, inde zostáva |
| J.8 | Každý modul jadra má testy | 🔸 36 testovacích súborov, pokrytie nových modulov zostáva |

**Výsledok:** jadro má stabilné rozhranie a jeden zdroj pravdy pre každú vlastnosť. Rozhranie sa
dá vymeniť bez prepísania celého prostredia.

---

## Etapa 4 — App Manager a natívne aplikácie ⬜

| | Úloha | Stav |
|---|---|---|
| 4.1 | Zoznam nainštalovaných (.desktop + Flatpak), spúšťanie, štítky pôvodu | ⬜ |
| 4.2 | Inštalácia a odstránenie Flatpaku | ⬜ |
| 4.3 | Aktualizácie: systém (PackageKit) aj Flatpak na jednom mieste | ⬜ |
| 4.4 | Repozitáre: Flathub a vlastné, zapnutie a vypnutie | ⬜ |
| 4.5 | Mapa oprávnení nad `flatpak permissions`: zobraziť a odobrať | ⬜ |
| 4.6 | Prepínač siete pre kontajnerovú aplikáciu | ⬜ |
| 4.7 | Štítok SYSTÉM pri aplikáciách bez izolácie a ponuka kontajnerovej verzie | ⬜ |
| 4.8 | `xdg-desktop-portal` nainštalovaný a nastavený (systémové dialógy súborov) | 🔸 portál vzhľadu beží, FileChooser zostáva |
| 4.9 | Pôvod aplikácie zrozumiteľne: odkiaľ je, aký runtime, či je podpísaná, aká izolácia, aké oprávnenia, aktualizačný zdroj | ⬜ |

**Výsledok:** používateľ nainštaluje, spustí a obmedzí aplikáciu bez terminálu.

---

## M1 — Overenie na viacerých strojoch ⬜

Kontrola v polovici cesty medzi 0.1 a 1.0. Dovtedy stačil virtuálny stroj, tu sa prostredie prvýkrát
poriadne skúša na skutočnom hardvéri. Predpoklad: hotová etapa H, etapa 4 a bod 7.4 (Steam a Proton).

| | Úloha | Stav |
|---|---|---|
| M1.1 | Aspoň tri odlišné stroje: AMD Radeon, NVIDIA GeForce (rad 50xx), notebook s integrovanou grafikou | ⬜ |
| M1.2 | Steam sa nainštaluje z rozhrania, spustí a prihlási; Proton je dostupný | ⬜ |
| M1.3 | Hry: natívna, Proton DirectX 11 a Proton DirectX 12 alebo Vulkan; overiť obraz, zvuk, gamepad, plynulosť | ⬜ |
| M1.4 | Celá obrazovka: lišta ani oznámenia nekradnú fokus, nerezervujú miesto a neprekrývajú hru; obnovovacia frekvencia a rozlíšenie sa nestratia | ⬜ |
| M1.5 | Náročné aplikácie: 3D (Blender), grafika (Krita alebo GIMP), video (Kdenlive), prehliadač s WebGL | ⬜ |
| M1.6 | Viac monitorov a rôzne mierky: rozloženie sa zapamätá podľa stroja (EDID), po odpojení sa vráti | ⬜ |
| M1.7 | Rovnaký používateľ na dvoch strojoch: vzhľad, písmo a obľúbené idú s ním, hardvérové nastavenia zostávajú stroju | ⬜ |
| M1.8 | Ovládače: `latteos-diag` report z každého stroja, žiadne chýbajúce ovládače ani firmvér po čistej inštalácii | ⬜ |
| M1.9 | Čo nefunguje, je zapísané: kompatibilitná tabuľka stroj × ovládač × aplikácia, vrátane príčiny | ⬜ |

**Výsledok:** LatteOS je overené prostredie na skutočných počítačoch, nie prototyp vo virtuálnom stroji.
Vieme, na čom hry a náročné aplikácie bežia, na čom nie a prečo.

---

## Etapa 5 — Kontajnery a recepty ⬜

| | Úloha |
|---|---|
| 5.1 | Podman ako základ (bez roota, integrácia so systemd) |
| 5.2 | Formát receptu: čo sa pýta, predvolené hodnoty, potrebné práva |
| 5.3 | Čítanie metadát obrazu (ExposedPorts, VOLUME) |
| 5.4 | Automatické pridelenie portov, konflikty rieši systém |
| 5.5 | Overenie po štarte: čo v kontajneri naozaj počúva |
| 5.6 | Čítanie známych chýb (EULA, chýbajúce práva) a ponuka riešenia |
| 5.7 | Import `docker-compose.yml` so štítkom „neoverený recept“ |
| 5.8 | Desať receptov na začiatok (Tailscale, torrent, Minecraft, Home Assistant…) |

**Výsledok:** kontajnerová aplikácia beží po jednom kliknutí, bez experimentovania.

---

## Etapa 6 — Android ⬜

| | Úloha |
|---|---|
| 6.1 | Waydroid: inštalácia, binder v jadre, overenie na skutočnom stroji |
| 6.2 | Inicializácia obrazu Androidu zo sprievodcu, nie z terminálu |
| 6.3 | Android aplikácia ako okno na ploche (režim jednotlivých aplikácií) |
| 6.4 | Zoznam Android aplikácií v App Manageri so štítkom ANDROID |
| 6.5 | Inštalácia `.apk` z App Managera |
| 6.6 | Navigačné tlačidlá (späť, domov, prehľad) a klávesové skratky |
| 6.7 | Prístup k súborom: zdieľaný priečinok medzi LatteOS a Androidom |
| 6.8 | Schránka naprieč systémami (LatteOS ↔ Android) |
| 6.9 | Sieť a jej vypnutie pre Android prostredie |

**Výsledok:** Android aplikácia sa spúšťa a používa ako každá iná. Vo virtuálnom stroji nepobeží
dobre, testuje sa na skutočnom stroji.

---

## Etapa 7 — Windows a hry ⬜

| | Úloha | Stav |
|---|---|---|
| 7.4 | **Proton a Steam pre hry** (vytiahnuté dopredu, do M1) | ⬜ |
| 7.1 | Bottles alebo vlastná správa prefixov, jeden prefix na aplikáciu | ⬜ |
| 7.2 | Inštalácia `.exe` z App Managera, štítok WIN32 | ⬜ |
| 7.3 | Odstránenie disku Z: z prefixu (aplikácia nevidí koreň) | ⬜ |
| 7.5 | Schránka naprieč systémami (LatteOS ↔ Wine) | ⬜ |
| 7.6 | Kompatibilitná databáza: čo funguje, čo nie, s čím sa netrápiť | ⬜ |
| 7.7 | Poctivé označenie neriešiteľných prípadov (cloudové licencie, anti-cheat) | ⬜ |

**Výsledok:** Windows aplikácie a hry bežia tam, kde to je možné, a kde nie, systém to povie vopred.

---

## Etapa 8 — Systémové nastavenia bez terminálu 🔸

| | Úloha | Stav |
|---|---|---|
| 8.1 | Wi-Fi, VPN, Bluetooth (NetworkManager, BlueZ) | ⬜ |
| 8.2 | Zvuk a hlasitosť v mape zdrojov (PipeWire) | ⬜ |
| 8.3 | Tlačiarne (CUPS) | ⬜ |
| 8.4 | Disky: pripojenie, odpojenie, formátovanie výmenných médií (udisks2) | 🔸 pripájanie a zväzky hotové |
| 8.5 | Používatelia, heslá, jazyk, klávesnica, čas | ⬜ |
| 8.6 | Aktualizácie systému | ⬜ |
| 8.7 | Zálohovanie a obnova používateľských dát (bez snapshotov, iba kópia) | ⬜ |
| 8.8 | Diagnostika: zobraziť chybu, ručne odoslať | 🔸 `latteos-diag` pre pád relácie hotové |
| 8.9 | Schéma systémových nastavení: jeden súbor na doménu, schémy a strom stránok v `data/settings/` | ✅ |
| 8.10 | Aplikácia Nastavenia: okno skladané zo schém, Prispôsobenie ako prvé | 🔸 šesť stránok `ready`, ostatné `partial` alebo `planned` |
| 8.11 | Obrazovky: rozlíšenie, mierka, otočenie, rozloženie, bezpečné vrátenie | 🔸 `latte-devices display` hotové, stránka Obrazovky `partial` |
| 8.12 | Napájanie: profily (výkon, vyvážený, tichý, šetrenie batérie) nad existujúcimi backendmi | ⬜ |

**Výsledok:** splnené kritérium „bežný používateľ nepotrebuje terminál ani raz“.

---

## Etapa P — Správca procesov a systémový monitor 🔸

Nie je to ďalšia úroveň nastavení ani správca hardvéru. Je to nástroj na sledovanie skutočného
aktuálneho stavu. Hranice: App Manager konfiguruje aplikácie, Správca zariadení hardvér,
Monitor iba číta stav, identifikuje jeho zdroje a umožní bezpečný zásah.

| | Úloha | Stav |
|---|---|---|
| P.1 | Živý stav: CPU, RAM, disky, sieť, GPU, teploty, spotreba | 🔸 |
| P.2 | Procesy: strom, vlastník, cesta, príkaz, systémový verzus používateľský, ukončenie | 🔸 |
| P.3 | Offline identifikácia hardvéru z `pci.ids` bez siete | ✅ |
| P.4 | Autorun na jednom mieste: XDG autostart, systemd služby a časovače, cron; pôvod, vlastník, príkaz, zapnutie a vypnutie | 🔸 desktop a systemd hotové |
| P.5 | Krátka história záťaže, nie len okamžitá hodnota | ⬜ |
| P.6 | Proces → aplikácia (závisí od J.4) | ⬜ |
| P.7 | Prepojenie na hardvér: aplikácia → proces → zariadenie → teplota a spotreba | ⬜ |
| P.8 | Telemetria pre externé zobrazovače (OLED displeje chladenia, Stream Deck) cez lokálne rozhranie, bez preberania ich konfigurácie | ⬜ |
| P.9 | „Čo to používa?“: pri zlyhaní operácie povedať, ktorý proces objekt drží, namiesto Skúsiť znova / Zrušiť | ⬜ |
| P.10 | Zdravie hardvéru oddelene od Správcu zariadení: SMART, opotrebovanie, throttling, batéria | ⬜ |

**Výsledok:** používateľ vidí, čo sa v počítači práve deje, odkiaľ to pochádza a čo s tým môže urobiť.

---

## Etapa 9 — Sprievodca a vydanie ⬜

| | Úloha |
|---|---|
| 9.1 | Zistenie schopností (Flatpak, Waydroid, KVM, Landlock) a ich zobrazenie |
| 9.2 | Otázky, tabuľky profilov, plán nastavenia, schválenie |
| 9.3 | Balíček (RPM) so všetkými komponentmi a reláciou |
| 9.4 | ISO obraz cez Fedora kickstart, vrátane `latteos-base` z etapy H |
| 9.5 | Test na čistom stroji podľa kritérií z manifestu |
| 9.6 | Dokumentácia pre používateľa a stránka projektu |

**Výsledok:** LatteOS 0.1 Jihlavanka sa dá nainštalovať a odovzdať niekomu inému.

---

## Cesta k 1.0 Arabica

Po M1 a etapách 5 až 9 zostáva do vydania:

| Oblasť | Čo musí platiť |
|---|---|
| Stabilita | obnova po páde, štruktúrované záznamy, vrátenie nastavení, atomický zápis konfigurácie, bezpečné vrátenie obrazovky, prežitie reštartu kompozitora a shellu |
| Kompatibilita | otestované GTK 3 a 4, libadwaita, Qt 5 a 6, KDE aplikácie, natívny balík, Flatpak, AppImage; kategórie aplikácií, nie konkrétne značky |
| Vzhľad | adaptéry z bodu 3.8 hotové, každý so deklarovaným vlastníctvom a poctivým stavom |
| Aplikácie | inštalácia, odstránenie, aktualizácia a oprávnenia z jedného miesta |
| Bezpečnosť | portály, polkit, vedomie o sandboxe, žiadne privilegované operácie priamo z rozhrania |
| M2 zmrazenie | jadro, schéma nastavení, model aplikácií, model oprávnení a model úložiska sa už nemenia |

Arabica neznamená „všetko je vlastné“. Znamená, že LatteOS funguje ako konzistentná vrstva nad Linuxom.
LatteOS nestavia vlastný kernel, kompozitor, súborový systém, toolkit, prehliadač, kancelársky balík,
správcu balíkov ani init.

---

## Nápady mimo plánu

Nezáväzný zásobník. Sem patrí, čo ešte nemá overiteľný výsledok ani miesto v etape:
Latte System Defender a Security Center (behaviorálna analýza), časové osi systémových
a bezpečnostných udalostí, Heidelberg a základný balík aplikácií, živá tapeta ako plnohodnotný objekt,
univerzálne vyhľadávanie s režimami hľadanie/AI/príkaz, tiling a pravidlá okien, snímka pracovnej
relácie, „Prečo je počítač pomalý?“, wellbeing a správa času, hry v oficiálnom balíku, história schránky,
štítky a farby priečinkov, hľadanie duplikátov, analyzátor úložiska.

Zdroje: [IDEAS.md](IDEAS.md) a kapitoly 41 až 44 v [CoreAPImanifest.md](CoreAPImanifest.md).
Nápad sa do plánu dostane až vtedy, keď sa dá napísať jeho overiteľný výsledok.

---

## Komponenty zo špecifikácie 1.1 a ich miesto v Jihlavanke

| Komponent | V Jihlavanke | Etapa |
|---|---|---|
| latte-files | správca súborov (nad rámec špecifikácie, vlastný pre 0.1) | 1 |
| latte-shell | lišta, popupy, oznámenia, plocha | 2 |
| latte-sessiond | relácia nad systemd user službami | 2b |
| latte-greeter | prihlásenie a uvítanie | 2b |
| latte-clipd | schránka | 2 |
| latte-appd → latte-apps | App Manager (Flatpak, PackageKit, Waydroid, Bottles) | 4 |
| latte-capd → latte-perms | mapa oprávnení nad Flatpakom, nie vlastný capability engine | 4 |
| latte-netd → latte-net | prepínač siete pre aplikáciu | 4 |
| latte-storaged → latte-resources | zväzky, pripojenie, USB, udisks2 | 1, 8 |
| latte-deviced | zariadenia: kamera, tlačiareň, Bluetooth | 8, H |
| latte-audiod | zvuk nad PipeWire | 8, H |
| latte-translatord | výber prostredia: Flatpak, Waydroid, Bottles | 4–7 |
| latte-probe | zistenie schopností hostiteľa | 9 |
| latte-wizard | sprievodca a plán nastavenia | 9 |
| latte-updated | aktualizácie | 8 |
| latte-diagd | diagnostika, čierna skrinka | 8, H |
| latte-decoderd | náhľady súborov v sandboxe | odložené |
| latte-console | Service Console | nie v 0.1 |
| latte-a11yd | prístupnosť, sémantický strom | nie v 0.1 (rieši GTK a AT-SPI) |
| latte-compositor | vlastný kompozitor | nie v 0.1 (labwc) |
| latte-execd, latte-radio@, latte-objectd | vysielačka, svety aplikácií, objekty | Arabica |
| latte-vmd | Level 3, virtuálne stroje | Arabica |
| latte-snapshotd | snapshoty a Kôš | Kôš v etape 1, snapshoty až s btrfs |
| latte-licensed | licencia | nie v 0.1 (Jihlavanka je zdarma) |
| latte-resourced | limity CPU a RAM pre aplikácie | odložené (cgroup cez systemd) |

V Jihlavanke komponenty nenesú koncovku `d`, lebo to nie sú démony, ale bežné programy.
Pri prechode na Arabicu sa meno vráti k tvaru zo špecifikácie.

---

## Čo sa dá odložiť a čo nie

**Odložiť sa dá bez straty:** animácie a sklo (čakajú na vlastný kompozitor), schránka s ôsmimi
slotmi (stačí systémová), náhľady v sandboxe, vlastná sada ikon.

**Odložiť sa nedá:**
- štítky pôvodu a ochrany pri každej aplikácii (bez nich padá pravidlo poctivosti),
- odoberanie oprávnení, ktoré naozaj platí (4.5),
- overenie po štarte kontajnera (5.5), inak zostane presne to experimentovanie, ktoré má Jihlavanka odstrániť,
- zobrazenie chýbajúcich schopností a ovládačov (9.1, H.2), pretože tichá degradácia je zakázaná,
- vrátenie nastavení obrazovky a kritických zmien.

---

## Ďalšie tri kroky

1. **H.1 a H.2** — zoznam balíkov pre `latteos-base` overený proti `dnf` a stav ovládačov
   v Správcovi zariadení. Je to bezpečné (len čítanie) a hneď ukáže medzery na skutočných strojoch.
2. **J.1 a J.2** — App Registry a odstránenie štyroch `Popen` volaní zo shellu. Bez toho sa App Manager
   postaví na priamych cestách k súborom.
3. **Etapa 4** — App Manager. Najväčší skok v hodnote projektu a vstupenka do M1, pretože bez neho
   sa Steam a hry inštalujú z terminálu.
