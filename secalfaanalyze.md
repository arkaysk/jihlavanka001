# LatteOS gamerdistro — alfa recenzia

**Kontrolovaná revízia:** `3b4663b` (`gamerdistro`), 26. 9. 2026  
**Stav vetvy:** čistá, zhodná s `origin/gamerdistro`  
**Zameranie:** aktuálny stav desktopu a hernej vrstvy, bezpečnostné riziká a porovnanie s Windows 11 a hernými Linux distribúciami.

## Nálezy

### P1 — Okamžité NET sa nemusí rozbehnúť po čistom štarte

V [`session/bin/latte-netd`](session/bin/latte-netd#L59) generuje `apply()` nftables dávku, ktorá najprv vykoná `delete table inet latte_net` a potom tabuľku vytvorí. Ak tabuľka ešte neexistuje, dávka môže zlyhať a pravidlá sa nevytvoria. Služba pri tom pokračuje a skúša aplikáciu opakovať. Navyše [`latte-netd.service`](session/systemd/latte-netd.service#L8) tabuľku maže pri zastavení služby.

**Odporúčanie:** inicializovať tabuľku idempotentne a aktualizovať jej reťazce/pravidlá tak, aby prvé spustenie fungovalo bez existujúcej tabuľky. Pridať integračné overenie po čistom štarte aj reštarte služby.

### P1 — Sandbox zlyháva otvorene, ak chýba `bubblewrap`

Ak má aplikácia zakázané oprávnenia, ale `bwrap` nie je dostupný, [`session/bin/latte-sandbox`](session/bin/latte-sandbox#L119) vypíše varovanie a spustí aplikáciu bez izolácie. Používateľské bezpečnostné nastavenie sa tak potichu ignoruje.

**Odporúčanie:** pri chýbajúcom `bwrap` aplikáciu odmietnuť spustiť a zobraziť jasnú chybu. Testovať aj degradovaný stav a kontrolovať potrebné závislosti pri inštalácii.

### P2 — SSDP môže nasmerovať skener na ľubovoľnú URL

Sieťový inšpektor preberá `LOCATION` z SSDP odpovede a odovzdá ju priamo `urllib.request.urlopen()` ([`session/bin/latte-inspektor`](session/bin/latte-inspektor#L276)). Zariadenie v LAN tak môže vyvolať požiadavku z počítača na localhost alebo iný cieľ.

**Odporúčanie:** povoľovať iba HTTP(S), obmedziť cieľ na IP adresu zariadenia, ktoré odpoveď poslalo, kontrolovať presmerovania a používať prísne časové limity.

## Zhodnotenie

LatteOS má široký a osobitý desktopový prototyp: vlastný shell, nastavenia, správu aplikácií a zariadení, SAFE režim a návrh izolácie aplikácií. Projekt je však podľa vlastnej roadmapy zameraný najprv na Fedora Server vo VM a softvérové vykresľovanie ([`ROADMAP.md`](ROADMAP.md#L12)).

Ako **herná distribúcia na každodenné hranie** zatiaľ nie je pripravená. Herná knižnica prepája Steam a Heroic, ale roadmapa stále uvádza Steam/umu/Proton integráciu aj Gamescope ako nedokončené; zároveň konštatuje, že hranie hier vo VM prakticky nefunguje ([`ROADMAP.md`](ROADMAP.md#L368)). Podpora reálneho GPU, Vulkanu, ovládačov AMD/NVIDIA a funkcií ako HDR/VRR zostáva plánovaná ([`ROADMAP.md`](ROADMAP.md#L374)).

## Porovnanie

| Oblasť | LatteOS teraz | Windows 11 | Bazzite / SteamOS |
|---|---|---|---|
| Herná kompatibilita | Integrácia knižnice, herný režim; reálne hranie a Proton stack nie sú hotové | Výrazne širšia natívna podpora hier, ovládačov a anticheatu | Zrelší Linuxový Steam/Proton stack a gaming režim; kompatibilita sa líši podľa hry |
| Grafika a hardvér | VM-first, bez potvrdenej podpory herného GPU | Široká podpora výrobcov a periférií | Mesa/Vulkan a podpora herného hardvéru sú súčasťou distribučného cieľa |
| Systémové doručovanie | Klasická Fedora Server; obraz pre iné PC a Atomic sú odložené | Hotový inštalátor, aktualizácie a OEM distribúcia | Image-based aktualizácie a rollback sú súčasťou prístupu |
| Vlastné prostredie | Silná vlastná identita, slovenské UI, SAFE režim a integrované nástroje | Zrelé, všeobecné desktopové prostredie | Prostredie orientované na hry, menší dôraz na vlastný desktopový ekosystém |

Windows 11 je najďalej v podpore hier, periférií a anticheatu. Bazzite/SteamOS sú vhodnejšie Linuxové porovnanie pre hotovú hernú distribúciu. LatteOS má zaujímavý vlastný desktopový koncept, ale zatiaľ mu chýba herná a distribučná vrstva, ktorá by z neho spravila produkt „nainštaluj a hraj“.

## Čo chýba pred hernou alfou

1. Opraviť uvedené bezpečnostné chyby a pridať testy čistého štartu, reštartu služby a zlyhania závislostí.
2. Vybrať aspoň jednu reálnu podporovanú hardvérovú konfiguráciu a na nej overiť inštaláciu, ovládače, aktualizáciu, obnovu, spánok/prebudenie a viacero hier.
3. Dokončiť Steam/Proton/umu integráciu a otestovať natívne hry, DX11, DX12/Vulkan, ovládače, gamepad a známe anticheat obmedzenia.
4. Pripraviť reprodukovateľný obraz alebo inštaláciu pre cieľové PC, podporovaný aktualizačný kanál a jasný rollback.
5. Rozšíriť testovanie z Rust jednotkových testov na shell, QML/Lua, systémové služby a čistú VM inštaláciu.

Kým sa neoverí reálny herný hardvér a kompatibilita hier, presnejšie označenie je **desktopová alfa s hernou integráciou**, nie hotová herná distribúcia.

## Overenie

- `cargo test --workspace`: 12/12 testov prešlo.
- Syntax backendu `session/bin/latte-inspektor`: prešla kontrola Pythonu.
- nftables check-only test sa nepodarilo vykonať: prostredie nemalo `CAP_NET_ADMIN`. Nález o inicializácii nftables je preto statická analýza kódu, nie úspešne reprodukovaný runtime test.
- Kontrola prebehla na `3b4663b`; pracovný strom bol čistý a vetva zhodná s `origin/gamerdistro`.

---

## Odpoveď a stav po oprave (26. 9. 2026 ráno, Claude)

| Nález | Overenie | Stav |
|---|---|---|
| P1 nftables pri prvom štarte | **Neplatný.** Dávka v `latte-netd` začína `table inet latte_net` (vytvorí tabuľku, ak nie je), až potom `delete` a nová definícia — štandardný idempotentný postup. Overené naostro s `sudo nft -f`: prejde bez tabuľky aj s ňou. | Doplnený komentár; `ExecStopPost` používa `nft destroy` s `-`, takže zastavenie služby nehlási chybu, keď tabuľka neexistuje. |
| P1 sandbox bez `bwrap` | **Platný.** Aplikácia so zakázanými oprávneniami by sa potichu spustila bez izolácie. | Opravené: `latte-sandbox` ju odmietne (kód 126) a ukáže kritické oznámenie; inštalátor doinštaluje `bubblewrap` a `xdg-dbus-proxy`. Overené testom s podvrhnutým `which`. |
| P2 SSDP `LOCATION` | **Platný a horší, než je opísané:** `urlopen` berie aj `file://`, takže zariadenie v LAN mohlo nechať prečítať miestny súbor (výsledok sa síce zahodil, ale čítal sa). | Opravené: iba `http`, hostiteľ musí byť presne IP adresa, ktorá odpovedala, bez presmerovaní a bez proxy; odpoveď iba 200, najviac 200 kB. Validátor overený aj na trikoch `http://ip@127.0.0.1`, `http://127.0.0.1#@ip`. |
| Bod 5: testy mimo Rustu | — | Pridaný `setup/test/dym.sh`: syntax všetkých skriptov a štart každej QML aplikácie bez obrazovky v izolovanom XDG; hľadá chyby QML. Prvý beh: 22/22 aplikácií a všetky skripty v poriadku. |

Commity: `f885a6f` (bezpečnosť), dymový test v nasledujúcom commite.

## Návrhy

1. **Označenie verzie:** súhlas — do README a na prihlasovaciu obrazovku (dev) „desktopová alfa s hernou integráciou“,
   kým neprejde reálny HW. Herné ciele ostávajú vo fáze H (čaká na testovací stroj).
2. **Bezpečnostné pravidlo pre všetky nástroje, ktoré čítajú zo siete** (inšpektor, tapety online, RSS v greeteri,
   App Manager/Flathub): jedna spoločná pomocná funkcia „bezpečné stiahnutie“ (iba http/https, bez file://, limit veľkosti
   a času, žiadne presmerovanie na localhost/súkromné adresy, ak cieľ nie je v LAN). Prejdem existujúce `urlopen`/`curl`.
3. **Fail closed ako zásada:** každá bezpečnostná funkcia (NET, sandbox, Setup Plan) sa pri chybe závislosti správa
   prísnejšie, nie voľnejšie, a povie to používateľovi. Zapísať do zásad UI a skontrolovať `latte-net`, `latte-apps plan-apply`.
4. **Testy služieb:** do `dym.sh` pridať (so sudo, iba na dev VM) reštart `latte-netd` a kontrolu tabuľky; test čistej
   inštalácie spraviť až s obrazom pre Atomic (rovnaký bod ako v ROADMAP F7).
5. **Porovnanie s Bazzite/SteamOS:** LatteOS nemá súťažiť v „Steam na prvom mieste“, ale v desktope pre bývalých
   používateľov Windows (myš, kontextové ponuky, Správca zariadení, inšpektor siete, slovenčina) s hrami ako plnohodnotnou
   súčasťou. Pre hernú vrstvu prevziať, čo Bazzite rieši dobre (image-based aktualizácie a rollback, Gamescope relácia,
   ovládače NVIDIA v obraze) — to sedí s plánovaným prechodom na Fedora Atomic.
6. **Anticheat:** do Správcu hier pridať stĺpec „Bude to fungovať?“ z databázy areweanticheatyet.com (ako pri .exe v
   App Manageri), aby hráč vedel vopred, ktoré online hry na Linuxe nepôjdu.
