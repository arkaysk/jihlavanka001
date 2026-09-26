Pri prezeraní repozitára arkaysk/jihlavanka001 vo vetve gamerdistro som sa zameral na kód v crates/ (Rust) a setup/ (shell). Nižšie sú konkrétne chyby, riziká a návrhy na vylepšenie.
🔍 Hlavné oblasti a zistené chyby
1. latte-hw/src/lib.rs – detekcia grafiky

Problém s čakaním na DRM
V cmd_select sa volá wait_for_drm, ale jeho výsledok sa ignoruje (iba sa vypíše chyba). Následne Probe::run znova kontroluje has_drm cez Path::new("/dev/dri/card*").exists(). Ak sa DRM objaví až počas čakania, has_drm môže byť false, čo povedie k zbytočnému SAFE režimu.

Krehké parsovanie eglinfo
parse_eglinfo predpokladá presné reťazce "OpenGL ES profile renderer:" a "OpenGL ES profile version:". Zmena formátu (napr. iná verzia Mesa) spôsobí tiché zlyhanie – renderer zostane prázdny a ok = false.

Závislosť na DMI
virtualization() číta /sys/class/dmi/id/sys_vendor a product_name. V kontajneroch alebo niektorých VM tieto súbory nemusia existovať, čo vedie k None a strate kontextu o virtualizácii.
2. latte-boot/src/main.rs – rozhodovacia logika

Zložitá a neprehľadná funkcia decide
Funkcia obsahuje viacero vnorených podmienok a vracia Decision s reťazcami. Napríklad vetva pre vm-3d sa spustí len ak cfg.allow_vm3d je true, inak sa použije sw-gl. To je v poriadku, ale kód je ťažko testovateľný a rozširovateľný.

Nekonzistentný zápis mode.toml
cmd_select zapisuje mode.toml, session.env a hyprland.conf cez write_atomic. Ak zápis mode.toml zlyhá, session.env a hyprland.conf sa už nezapíšu, ale mode.toml môže zostať v nekonzistentnom stave.

force_safe a počítadlo pádov
Po úspešnom zápise sa force_safe odstráni, ale crash_count sa neaktualizuje. Ak relácia spadne hneď po štarte, počítadlo sa nezvýši a SAFE režim sa nemusí spustiť.

Zlyhanie zápisu počítadla
V cmd_session_start sa pri zlyhaní zápisu crash_count iba vypíše chyba a pokračuje sa. To môže viesť k tomu, že počítadlo sa nikdy neaktualizuje a SAFE režim sa nespustí.

Kontrola ppid()
cmd_ok používa ppid() na overenie, či kompozitor stále beží. Ak sa rodičovský proces zmení z iného dôvodu (napr. re-exec), môže to viesť k falošne pozitívnemu výsledku.
3. install-session.sh – inštalačný skript

Prísne set -euo pipefail
Skript používa set -euo pipefail. Ak niektorá z binárok v slučke for f in ... neexistuje, sudo install zlyhá a skript sa ukončí. To je problematické, ak sa očakáva, že niektoré binárky ešte neboli zostavené.

Chýbajúca kontrola existencie
V slučke for f in latte-session latte-safe ... sa inštalujú desiatky binárok. Ak niektorá chýba, skript spadne. Odporúčam pridať kontrolu [ -f "$S/bin/$f" ] alebo preskočiť chýbajúce súbory.

Predpoklad rpm
Skript používa rpm -q hyprland-devel na kontrolu balíčka. Na systémoch bez rpm (napr. Debian) to zlyhá. Vzhľadom na cieľový systém (Fedora) je to prijateľné, ale pre prenositeľnosť by bolo lepšie použiť command -v rpm.

Atomická výmena súborov
Funkcia put() používa mv -f. Ak mv zlyhá, môže zostať .latte-new súbor. Odporúčam pridať trap na upratanie dočasných súborov.
4. Všeobecné problémy

Manuálne parsovanie TOML
Config::load parsuje boot.toml ručne (splitovanie riadkov, hľadanie =). To je náchylné na chyby pri zložitejších hodnotách (napr. reťazce s =). Odporúčam použiť knižnicu toml so serde.

Chýbajúca validácia vstupov
V Cmdline::parse sa hodnoty latte.mode a latte.renderer ukladajú bez validácie. Ak používateľ zadá neplatnú hodnotu, decide ju ignoruje a použije predvolené správanie. Lepšie by bolo explicitne ošetriť neznáme hodnoty.
💡 Návrhy na vylepšenie

    Zjednodušiť decide a presunúť logiku do samostatných funkcií
    Rozdeliť rozhodovanie na menšie celky: select_renderer(), check_crashes(), check_virt(). To uľahčí testovanie a čítanie.

    Použiť knižnicu toml na parsovanie a serializáciu
    Nahradiť manuálne parsovanie boot.toml a generovanie mode.toml knižnicou toml + serde. Zníži sa riziko chýb a kód bude prehľadnejší.

    Zaviesť atomický zápis viacerých súborov
    V cmd_select najprv zapísať všetky súbory do dočasných súborov a potom ich presunúť na cieľové miesta. Ak niektorý krok zlyhá, vykonať rollback.

    Pridať kontrolu existencie binárok v install-session.sh
    Pred inštaláciou overiť, či súbor existuje:
    bash

    for f in latte-session latte-safe ...; do
        if [ -f "$S/bin/$f" ]; then
            sudo install -Dm755 "$S/bin/$f" "/usr/bin/$f"
        else
            echo "Chýba: $f" >&2
        fi
    done

    Zlepšiť čakanie na DRM
    V cmd_select počkať na DRM a až potom spustiť Probe::run. Alebo v Probe::run použiť wait_for_drm namiesto jednorazovej kontroly has_drm.

    Ošetriť chyby pri zápise počítadla pádov
    V cmd_session_start pri zlyhaní zápisu crash_count vrátiť ExitCode::FAILURE namiesto tichého pokračovania. To zabezpečí, že sa SAFE režim spustí včas.

    Použiť systemd Automatic Boot Assessment
    Zvážiť namiesto vlastného počítadla pádov použitie systemd-bless-boot a boot counting, ktoré je štandardným mechanizmom v systemd. To by zjednodušilo kód a zvýšilo spoľahlivosť.

    Pridať testy pre okrajové prípady
    V Rust kóde rozšíriť testy o:

        Neplatné hodnoty v cmdline (napr. latte.mode=neplatny).

        Prázdny alebo poškodený boot.toml.

        Súbeh viacerých zápisov do mode.toml.

    Zvážiť použitie start-hyprland
    Hyprland 0.53+ ponúka start-hyprland s vstavanou podporou crash recovery a safe mode. Namiesto vlastného riešenia by sa dalo integrovať s týmto wrapperom.

    Dokumentovať formát boot.toml
    Pridať do ROADMAP.md alebo README.md presný formát boot.toml vrátane povolených hodnôt a ich významu.

📋 Zhrnutie

Projekt má solídny základ – oddelenie HW detekcie, boot logiky a inštalačných skriptov. Najväčšie riziká sú v krehkom parsovaní (eglinfo, TOML), nekonzistentnom zápise viacerých súborov a príliš prísnom set -e v inštalačnom skripte. Odporúčam prioritne:

    Nahradiť manuálne parsovanie TOML knižnicou.

    Zaviesť atomický zápis s rollbackom.

    Pridať kontroly existencie binárok v install-session.sh.

    Zjednodušiť decide a rozšíriť testy.

Ak chceš, môžem sa hlbšie pozrieť na konkrétny súbor alebo pripraviť návrh konkrétnej zmeny v kóde.
---

## Odpoveď a stav (26. 9. 2026, Claude — overené v kóde, nie odhadom)

| Bod | Verdikt | Čo sa stalo |
|---|---|---|
| 1a DRM: výsledok `wait_for_drm` sa ignoruje | **Neplatné.** `cmd_select` čaká až 5 s *pred* `Probe::run()`; ak sa karta objaví počas čakania, sonda ju už vidí. Ak sa neobjaví do 5 s, SAFE je správne rozhodnutie. | bez zmeny |
| 1b krehké parsovanie `eglinfo` | Čiastočne. Pri zmene formátu vyjde `ok = false` → sw-gl/SAFE, teda zlyhá **bezpečne**, nie ticho do čiernej obrazovky. | bez zmeny; prípadná zmena formátu Mesa sa ukáže v `latte-boot status` |
| 1c chýbajúce DMI | **Neplatné.** Pri chýbajúcom DMI je záloha cez príznak `hypervisor` v `/proc/cpuinfo`. | bez zmeny |
| 2a zložitá `decide` | Názor. Funkcia je lineárna (prvá platná podmienka vyhráva) a má testy. | bez zmeny |
| 2b nekonzistentný zápis mode.toml | Nízke riziko: súbory sú v `/run` (tmpfs), po reštarte vznikajú nanovo, pri chybe `select` vráti FAILURE a relácia ide do SAFE. | bez zmeny |
| 2c `force_safe` a počítadlo | **Neplatné.** Počítadlo pádov zvyšuje `session-start`, nie `select`; tie dve veci spolu nesúvisia. | bez zmeny |
| 2d zlyhanie zápisu počítadla | Zámer: FAILURE by pri read-only `/var/lib` zablokoval NORMAL navždy. Chyba sa zapíše do žurnálu. | bez zmeny (zváži sa s Atomic, kde je `/var` zapisovateľný vždy) |
| 2e `ppid()` | **Neplatné.** Re-exec zachováva PID; zmena rodiča znamená, že kompozitor skončil — presne to, čo sa má zistiť. | bez zmeny |
| 3a/3b `set -e` a chýbajúce binárky | Platné v tom zmysle, že inštalácia mohla skončiť v polovici. | **Opravené:** zoznam `BINS` sa overí celý pred prvým zásahom do systému. |
| 3c `rpm` | Cieľ je iba Fedora. | bez zmeny |
| 3d `put()` a `.latte-new` | Platné. | **Opravené:** pri zlyhaní sa dočasný súbor zmaže. |
| 4a ručné TOML | **Neplatné** pre `=` v hodnotách (`split_once` delí na prvom `=`); súbor má 3 jednoduché kľúče. Knižnica `toml` by kvôli `cargo --offline` v inštalátore pridala viac rizika než úžitku. | bez zmeny |
| 4b validácia `latte.mode` / `latte.renderer` | Platné (preklep v GRUB sa ticho ignoroval). | **Opravené:** `latte-boot` vypíše varovanie s povolenými hodnotami; nový test. |
| systemd Automatic Boot Assessment | Rieši počítanie štartov **jadra/záznamu v zavádzači**, nie pády grafickej relácie. Hodí sa až s Fedora Atomic (greenboot + rollback). | do ROADMAP k Atomic |
| `start-hyprland` | Zvážené skôr a vedome nepoužité: po páde reštartuje Hyprland s rovnakou grafikou, LatteOS chce prejsť do SAFE (iný renderer). Zdôvodnené v `session/bin/latte-session`. | bez zmeny |

Testy: `cargo test --workspace` 13/13 (pribudol test neplatných parametrov kernelu); `setup/test/dym.sh` na skripty a QML.
