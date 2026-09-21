# LatteOS 0.1 — Jihlavanka

Používateľské prostredie nad bežným Linuxom.
Skrýva vnútro Linuxu, zjednocuje aplikácie do jedného modelu
a nepredstiera ochranu ani podporu, ktorú nemá.

Základ: Fedora (vyvíja sa na Fedore 44) + labwc + Python/GTK4.
Plán vývoja je v samostatnom súbore: **[ROADMAP.md](ROADMAP.md)**.

---

## Zásady

Osem pravidiel, ktoré platia pre každé rozhodnutie v kóde. Podrobný rozbor a návrh jadrovej vrstvy
je v [CoreAPImanifest.md](CoreAPImanifest.md) (doplnkový návrh, nie záväzná špecifikácia).

**1. Linux first, Latte second.**
Ak existuje štandard Linuxu alebo freedesktopu, použije sa. Ak toolkit ponúka štandardné API, použije sa.
Ak existuje portál, použije sa. Vlastný mechanizmus je posledná možnosť. LatteOS pridáva UX a koordináciu,
nie druhý paralelný svet.

**2. Kompatibilita cez systémové názvoslovie.**
Interne sa používajú názvy a rozhrania, ktorými hovorí ostatný Linux (XDG, D-Bus, portály, GSettings,
KDE farebné schémy, Wayland protokoly). Nadviazať na existujúce a spracovať to lepšie, nie vytvoriť
vlastné pomenovanie toho istého.

**3. Aplikácia nemá potrebovať verziu pre LatteOS.**
Ak program funguje na štandardnom Linuxe a používa štandardné rozhrania, LatteOS ho má zaradiť
do prostredia bez toho, aby jeho autor čokoľvek menil.

**4. Jeden zdroj pravdy.**
Každá systémová vlastnosť má jedno miesto, kde sa nastavuje. Vzhľad drží `appearance.toml` + motív,
odtiaľ ho služba `latte-appearance` rozposiela do portálu, GTK, Qt a kompozitora. Adaptér nikdy nie je
samostatným zdrojom nastavenia.

**5. Cudzie konfigurácie sú cudzie.**
Nie každý súbor je majetkom LatteOS. Zapisuje sa len spravovaný blok alebo vlastné kľúče
(`merge_block`, `merge_ini` v [appearance.py](src/latte_common/appearance.py)), nikdy celý cudzí súbor.

**6. Poctivý stav namiesto predstierania.**
Čo sa nepodarilo zistiť alebo použiť, sa povie: `problems` v správcovi zariadení, `problem`
v scénach, `latte-appearance status` pri adaptéroch. Tichá degradácia je zakázaná.

**7. Chýbajúca bežná funkcia sa konzultuje.**
Ak je niečo v iných systémoch samozrejmé (kontextové menu pravým tlačidlom, ovládanie okna z lišty
úloh, vystrihnúť a prilepiť na ploche) a v LatteOS to chýba, neznamená to, že je to nepotrebné.
Znamená to, že sa o tom nerozhodlo, a treba to prebrať. Kopírovať Windows všade však cieľ nie je:
nastavenie obrazovky ani tapety do kontextového menu plochy nepatrí, pretože má svoje miesto
v Nastaveniach.

**8. Hardvér je pripravený dopredu.**
Ovládače sa neriešia až vtedy, keď používateľ zistí, že mu niečo nefunguje. Inštalácia LatteOS má
priniesť aktuálne stabilné ovládače a firmvér pre hardvér daného počítača: 3D grafika (Radeon aj
GeForce), zvuk, vstupné zariadenia, sieť a tlač majú fungovať po prvom prihlásení.
Stav: **rozrobené, etapa H v roadmape.** Zoznam balíkov a stav ovládačov už existujú
(`latte-devices base`, `latte-devices status`), samotné dopĺňanie je zatiaľ ručné.

---

## Stav

Prototyp. Hotové: relácia a prihlásenie, správca súborov, lišta s popupmi a oznámeniami, plocha
s tapetou a ikonami, správca zariadení, správca procesov, schéma Nastavení a jednotný vzhľad
naprieč vlastnými komponentmi, GTK4/libadwaita aj rámami okien od kompozitora.

Rozrobené: aplikácia Nastavenia, dekoratívne rohové dlaždice, prístupnosť, profily aplikácií,
hardvérová základňa (etapa H: zoznam `latteos-base` a stav ovládačov).
Nezačaté: App Manager, jadro (etapa J), kontajnery, Android, Windows a hry.

Presné stavy po bodoch: [ROADMAP.md](ROADMAP.md).

---

## Závislosti

Okrem GTK4, `gtk4-layer-shell` a `labwc`:

    udisks2 polkit                  pripájanie diskov a práca ako správca
    ffmpegthumbnailer               náhľady videí v zobrazení Miniatúry (fotky idú bez neho)
    kernel-modules-extra            ovládač disketovej mechaniky (modul floppy); bez disketovej
                                    mechaniky vo VM nie je potrebný
    greetd gtkgreet greetd-selinux   prihlasovacia obrazovka

Hardvérová základňa (etapa H) z toho urobí jeden metabalík `latteos-base`. Jeho zoznam už existuje
a je strojovo čitateľný: **[data/hardware/base.toml](data/hardware/base.toml)** — dvanásť skupín
(firmvér, grafika, zvuk, vstup, sieť, Bluetooth, tlač, disky, napájanie, portály, fwupd, prostredie).
Čo na tomto stroji chýba, povie:

    latte-devices base          # zoznam verzus skutočný stav, aj príkaz, ktorý to doplní
    latte-devices base --all    # aj balíky, ktoré už sú

Zoznam je rovnaký pre každý počítač (zásada 8): firmvér pre Radeon aj GeForce, pre Wi-Fi Intel aj
Realtek sa inštaluje všade, lebo stojí pár megabajtov a ušetrí „nefunguje mi sieť“.

**Celý povinný zoznam (63 balíkov) je z Fedory.** Cudzí repozitár nie je podmienkou behu LatteOS
a nezapína sa pri inštalácii. RPM Fusion rieši dva úzke prípady hardvéru — proprietárny ovládač
GeForce a Wi-Fi Broadcom — a k tomu kodeky. Steam medzi ne nepatrí: ide cez **Flatpak z Flathubu**.
Preto sú balíky z cudzích repozitárov v zozname vždy voliteľné a ponúknu sa až vtedy, keď
`latte-devices status` nájde zariadenie, ktoré bez nich nefunguje. Na stroji s Radeonom alebo Intelom
sa nezapne nikdy.

**Podporované však zostávajú aj tam, kde sa nepoužijú.** `base.toml` drží ku každému repozitáru jeho
balík `release`, adresu a riziká, takže cesta k zapnutiu je pripravená a `latte-devices base` ju
vypíše. Vypnutý repozitár sa nehlási ako problém — je to fakt, nie porucha.

Ku každému cudziemu repozitáru je v [base.toml](data/hardware/base.toml) napísané, čo to stojí:
`akmod-nvidia` sa prekladá znova pri každej aktualizácii jadra a po zlyhaní nabehne systém bez
ovládača, pri Secure Boote treba podpísať modul (MOK), balíky `*-freeworld` nahrádzajú fedorovské
a Fedora tento repozitár nepodporuje. Nič z toho sa nemá dozvedieť až po reštarte.

Pre hry treba navyše 32-bitové ovládače (`mesa-vulkan-drivers.i686`), tie sú vo Fedore.

### Čo funguje a čo nie

    latte-devices status        # zariadenia, ktoré si žiadajú pozornosť
    latte-devices status --all  # aj tie, ktoré fungujú

Každé zariadenie dostane jeden z piatich stavov: *funguje*, *chýba firmvér*, *chýba balík*,
*treba cudzí repozitár*, *nepodporované* (a *nezistené*, keď sa napríklad nedá čítať záznam jadra).
Zdroje sú lokálne: väzba ovládača v sysfs, hlásenia jadra o firmvéri a `rpm`. Nič sa neinštaluje —
to príde s bodom H.7.

**Zo zoznamu zariadení nesmie nič vypadnúť.** Väčšina skupín sa číta z rozhrania, ktoré zariadenie
vytvorí, až keď má ovládač: sieťová karta má rozhranie v `/sys/class/net`, zvuková kartu
v `/proc/asound`. Bez ovládača nevytvoria nič a zo zoznamu by zmizli, hoci na zbernici sú. Preto je
skupina **Ostatné zariadenia**: PCI zariadenie, ktoré sa neprihlásilo nikde, a USB zariadenie, ktoré
nepovedalo, čo je, sú v nej aj s dôvodom. Nezaradené zariadenie nikdy nedostane stav *funguje*.

---

## Spustenie

Jednotlivá aplikácia:

    python3 src/latte_files/app.py

Celá relácia (labwc, lišta pod systemd):

    tools/install-session.sh     # jednorazovo: jednotky a príkazy do ~/.config a ~/.local
    latteos-session              # z konzoly
    systemctl --user restart latte-shell   # reštart lišty pri vývoji

Práca ako správca v správcovi súborov (polkit), ako root:

    sh tools/install-admin.sh    # pomocník do /usr/libexec/latteos/ a polkit politika;
                                 # spustiť znova po zmene src/latte_files/latte-files-admin
                                 # alebo fileops.py

Dialóg pre heslo zobrazuje `latte-polkit`, ktorý spúšťa `session/labwc/autostart` (nie systemd: polkit
chce agenta v scope relácie).

Prihlasovacia obrazovka (greetd + latte-greeter, gtkgreet ako záloha), ako root:

    dnf install greetd gtkgreet greetd-selinux
    sh tools/install-greeter.sh  # kód a dáta greetera sa KOPÍRUJÚ do /usr/local;
                                 # spustiť znova po každej zmene
    systemctl set-default graphical.target && systemctl enable greetd

Ďalší používatelia (arkay, kenshi): `su -c 'sh tools/create-users.sh'` — bežné účty, súkromný domov,
vlastný Kôš; pozri [docs/nastavenia.md](docs/nastavenia.md).

---

## Komponenty

| Komponent | Úloha |
|---|---|
| `latte-shell` | lišta, popupy, oznámenia, plocha |
| `latte-files` | správca súborov so zväzkami |
| `latte-settings` | Nastavenia systému (tlačidlo v menu napájania; [docs/nastavenia.md](docs/nastavenia.md)) |
| `latte-appearance` | služba vzhľadu: portál, gtk.css, Qt schéma, téma labwc |
| `latte-devices` | Správca zariadení: hardvér po skupinách, stav ovládačov a monitory (`list`, `status`, `base`, `display list\|set\|apply\|safe`) |
| `latte-resources` | Správca zdrojov (popup ZDROJE): zariadenia a siete ako dlaždice |
| `latte-process` | Správca procesov a systémový monitor: živý stav, procesy, autorun |
| `latte-greeter` | prihlasovacia obrazovka nad greetd |
| `latte-polkit` | dialóg na zadanie hesla správcu (polkit agent relácie) |
| `latte-apps` | App Manager (plánované) |
| `latte-heidelberg` | editor dokumentov, začíname md, txt a html (plánované; [docs/lista-a-rohy.md](docs/lista-a-rohy.md), časť 7) |

Spoločný kód je v `src/latte_common/` (nastavenia, vzhľad, hardvér a jeho stav, procesy, súborové
operácie, scény, zväzky, hľadanie). Je to dnešné jadro; etapa J z neho urobí stabilný kontrakt.

---

## Vzhľad

Jedno miesto pre celé prostredie, podrobne v [docs/nastavenia.md](docs/nastavenia.md).

    latte-appearance set color.scheme light        # tmavý/svetlý režim, platí hneď
    latte-appearance set color.accent '#3A9BD9'    # vlastný akcent; reset ho vráti
    latte-appearance status | show | themes | profiles | apply | release

Služba `latte-appearance` sa spúšťa s reláciou (portál pre režim, akcent a písmo; gtk.css; rámy okien
v labwc). Po `tools/install-session.sh` sa treba znovu prihlásiť alebo urobiť
`systemctl --user restart xdg-desktop-portal`. Vývoj bez inštalácie: `tools/run-appearance.sh`.
Motívy: `data/themes/<id>/theme.toml`, vlastné v `~/.local/share/latteos/themes/`.

Tapeta: systémová je v `data/wallpapers/` (používa ju prihlasovanie a plocha bez vlastnej tapety),
používateľská je súbor v priestore používateľa a jej cestu drží `~/.config/latteos/appearance.toml`.
Nastaví sa v Nastaveniach (Prostredie › Pozadie) alebo z terminálu:

    latte-wallpaper set ~/Obrázky/moja.jpg [cover|contain|fill]    # zmena platí hneď
    latte-wallpaper reset                                          # späť na systémovú

---

## Lišta

**Prompt.** Malá ikona vľavo prepína režim (klik, koliesko myši alebo Ctrl+1/2/3): lupa hľadá súbory
a priečinky (domov a pripojené zväzky, bez diakritiky, Enter otvorí), znak konzoly spúšťa príkazy
Linuxu (výstup v popupe nad lištou, `cd` platí ďalej, Ctrl+C zastaví, vim/top/ssh/sudo sa otvoria
v okne foot), iskry sú AI. AI beží lokálne v LM Studiu (predvolene `http://192.168.56.1:1234`,
použije sa načítaný model). Nastavenie v `~/.config/latteos/prompt.toml`:

    ai_url = "http://192.168.56.1:1234"
    ai_model = "qwen/qwen3-4b-thinking-2507"     # nepovinné

**Čas a oznámenia.** Hodiny → pásma, zvonček → oznámenia (Nerušiť), dátum → kalendár. Časové pásma:
`~/.config/latteos/clock.toml` (`zones = "Europe/London,Asia/Tokyo"`), pridať sa dajú aj v popupe.
Oznámenia prijíma `latte-shell` na `org.freedesktop.Notifications`; skúška: `notify-send "Ahoj" "text"`.

**Plocha.** Ikony sa berú z priečinka Plocha (`~/Desktop`, ak existuje).

---

## Relácia a jej ukončenie

Systémový manažér (tlačidlo napájania v lište) spúšťa `session/latteos-logout` ako samostatnú user
službu: labwc skončí čisto (`labwc --exit`, potrebuje `LABWC_PID` z `labwc/autostart`),
`latteos-session` upratá a potom „Odhlásiť“ ukončí prihlásenie, ktoré vlastní greetd (aj konzolu,
z ktorej si LatteOS spustil ručne), takže sa ukáže prihlasovacia obrazovka. „Vypnúť“ v dev builde
prepne do textovej konzoly (`multi-user.target`); bez hesla to ide len s pravidlom
`data/polkit/51-latteos-dev.rules` (dáva ho `install-greeter.sh`, len dev), inak sa po odhlásení ukáže
prihlasovanie. Bez greetd je oboje len odhlásenie.

Ak relácia spadne, prihlasovanie vpravo ukáže kartu s dôvodom, v journale je zápis
(`journalctl LATTEOS_KIND=crash`) a podrobnosti dá `latteos-diag`. **Riadne ukončenie nezobrazí nič.**

---

## Vývoj

    python3 -m unittest discover -s tests

Testy nesmú zasiahnuť živú reláciu: žiadny autostart, žiadny zápis do user managera ani na živú
zbernicu, žiadne `pkill -f` cez cudzie procesy.

Vývojové spúšťače bez inštalácie: `tools/run-shell.sh`, `run-settings.sh`, `run-devices.sh`,
`run-process-manager.sh`, `run-greeter.sh` (proti simulovanému greetd, účty test/kava a guest),
`run-appearance.sh`, `run-polkit.sh`.

Ctrl+Alt+Backspace ukončí labwc a vráti prihlasovaciu obrazovku. V prihlasovaní je vľavo menu:
vypnúť/reštartovať počítač a dve voľby dev buildu, „Reštartovať LatteOS“ (znovu načíta greetd)
a „Ukončiť do konzoly“ (`multi-user.target`). Z konzoly späť: `latteos-start`. Voľba relácie
„Konzola (headless)“ otvorí shell a po `exit` sa vráti prihlásenie.

`LD_PRELOAD` pre layer-shell je zámerne len pri lište, nie v premenných relácie, aby neovplyvňoval
ostatné aplikácie.

---

## Dokumenty

| Súbor | Čo obsahuje |
|---|---|
| [ROADMAP.md](ROADMAP.md) | plán vývoja po etapách, stav každého bodu, milníky |
| [CoreAPImanifest.md](CoreAPImanifest.md) | návrh jadrovej vrstvy a adaptérov (doplnkový brainstorming) |
| [main_setting_v2.md](main_setting_v2.md) | návrh aplikácie Nastavenia, platná verzia |
| [main_settings.md](main_settings.md) | predchádzajúca verzia návrhu Nastavení |
| [docs/nastavenia.md](docs/nastavenia.md) | schéma nastavení, Prispôsobenie, správca zariadení, používatelia |
| [docs/lista-a-rohy.md](docs/lista-a-rohy.md) | lišta, rohové dlaždice, scény, farba priečinka, Heidelberg |
| [IDEAS.md](IDEAS.md) | zbierka nápadov, ktoré ešte nie sú rozhodnuté |
