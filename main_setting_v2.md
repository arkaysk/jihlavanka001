# Nastavenia systému LatteOS

**Návrh informačnej architektúry, navigácie, vlastníctva a kompletného zoznamu stránok pre aplikáciu Nastavenia**

**Stav:** návrh pre etapu 8.10
**Verzia:** 2.0
**Aktualizované:** 2026-09-20

---

# 1. Krátke rozhodnutie

LatteOS má mať jedno hlavné **Nastavenie systému**, ktoré je centrálnym miestom pre používateľské voľby, stav systému a vyhľadávanie.

Nemá však preberať všetku funkcionalitu ostatných manažérov.

Platí základné pravidlo:

> **Nastavenia integrujú stav a navigáciu, nie implementácie.**

Nastavenia:

* vysvetlia voľbu;
* zobrazia jej aktuálny stav;
* umožnia bežnú konfiguráciu;
* poskytnú kontext;
* vyhľadajú konkrétne nastavenie;
* otvoria príslušného špecializovaného správcu, ak je potrebná pokročilá operácia.

Špecializované komponenty zostávajú vlastníkmi svojich operácií:

* **App Manager** vlastní aplikácie, balíky, Flatpak, repozitáre, aktualizácie aplikácií a oprávnenia aplikácií;
* **Správca zdrojov** vlastní živé zariadenia, pripojenia, ovládače a hardvérovú diagnostiku;
* **Správca súborov** vlastní prehliadanie a manipuláciu so súbormi;
* **Správca účtov** vlastní používateľov, heslá a autentizačné metódy;
* **`latte-updated`** vlastní systémové aktualizácie a návrat po zlyhaní;
* **`latte-appearance`** vlastní vizuálny systém prostredia;
* **zálohovací nástroj** vlastní zálohy a obnovu;
* **bezpečnostný backend** vlastní bezpečnostné mechanizmy systému.

Pre používateľa to však musí pôsobiť ako jeden konzistentný systém.

---

# 2. Základný architektonický princíp

LatteOS nesmie vytvárať viacero konkurenčných miest, ktoré zapisujú rovnakú hodnotu.

Preto platí:

> **Jedna hodnota má mať jeden zdroj pravdy, ale môže mať ľubovoľný počet bezpečných vstupných bodov.**

Napríklad hlasitosť môže používateľ meniť:

* v Nastaveniach;
* v Quick Settings;
* cez systémové ovládanie zvuku;
* prípadne v Správcovi zdrojov.

Ani jedno z týchto rozhraní však nemá vlastniť samotnú konfiguráciu zvuku.

Princíp:

```text
                         Nastavenia
                             │
                         Quick Settings
                             │
                         systémové UI
                             │
                     Správca zdrojov
                             │
                             ▼
                       Audio backend
                         PipeWire
```

Rovnaký model sa používa pri:

* displejoch;
* sieti;
* Bluetooth;
* úložisku;
* oprávneniach;
* aktualizáciách;
* vzhľade;
* účtoch.

---

# 3. Päť hlavných používateľských oblastí

Kanonické používateľské rozhranie bude mať päť hlavných oblastí:

1. **Softvér**
2. **Dáta**
3. **Hardvér**
4. **Účet**
5. **Prostredie**

Tieto oblasti predstavujú používateľský model systému.

Nie sú totožné s technickými backendmi.

Technické skupiny v `index.toml` môžu byť rozdelené inak. UI ich však používateľovi prezentuje prostredníctvom týchto piatich oblastí.

---

# 4. Systém ako prierezová oblasť

Nie všetko sa prirodzene zmestí do piatich domén.

Preto bude existovať ešte **Systém**, ale nebude sa správať ako šiesta rovnocenná hlavná karta.

Systém predstavuje základné nastavenia platformy:

* jazyk;
* región;
* dátum a čas;
* vstupné metódy;
* bezpečnosť;
* informácie o LatteOS;
* celková diagnostika.

Používateľsky môže byť Systém umiestnený:

* pod piatimi hlavnými kartami;
* alebo ako samostatná menšia karta/položka v spodnej časti navigácie.

Nemá však narušiť základnú päťdielnu mapu.

---

# 5. Domovská stránka Nastavení

Nastavenia nemajú po otvorení okamžite zobrazovať iba zoznam kategórií.

Domovská stránka poskytne:

* stav systému;
* dôležité upozornenia;
* dostupné aktualizácie;
* stav úložiska;
* stav siete;
* stav zálohovania;
* posledné použité nastavenia;
* globálne vyhľadávanie.

Príklad:

```text
Nastavenia

[ 🔍  Hľadať nastavenie                         ]

Stav systému
──────────────────────────────────────────────

● LatteOS
  Systém je aktuálny

● Hardvér
  Všetky zariadenia pracujú normálne

● Dáta
  Posledná záloha pred 3 hodinami

● Sieť
  Wi-Fi pripojená

──────────────────────────────────────────────

Nedávno použité

  Obrazovky
  Motív a farby
  Wi-Fi
  Úložisko

──────────────────────────────────────────────

SOFTVÉR
DÁTA
HARDVÉR
ÚČET
PROSTREDIE
```

Domovská stránka je teda **stavový dashboard**, nie ďalšia kategória.

---

# 6. Navigácia: vrstvené karty

Základom navigácie bude vizuálny systém **prekryvných kariet**.

Koncept vychádza z bočného panela Správcu súborov LatteOS.

Hlavné oblasti nie sú obyčajný zoznam.

Každá oblasť je karta:

```text
SOFTVÉR
DÁTA
HARDVÉR
ÚČET
PROSTREDIE
```

## 6.1 Neaktívne karty

Neaktívna karta sa zmenší na kompaktný „chrbát“:

```text
┌──────────────────┐
│  SOFTVÉR       ● │
└──────────────────┘
```

Obsah podkategórií sa v tomto stave nezobrazuje.

Názov, ikona a stavový indikátor však zostávajú viditeľné.

---

## 6.2 Aktívna karta

Aktívna karta sa vysunie dopredu a zväčší:

```text
┌───────────────────────┐
│  HARDVÉR           !  │
│                       │
│  Obrazovky             │
│  Zvuk                  │
│  Sieť                  │
│  Bluetooth             │
│  Úložné zariadenia     │
│  Napájanie              │
│  Tlač a skenovanie     │
│  Diagnostika            │
└───────────────────────┘
```

Ostatné karty zostanú za ňou.

---

# 7. Hlavné karty sa nesmú stratiť v scrollovaní

Päť hlavných oblastí má byť **stále viditeľných**.

Pre hlavné karty sa preto nepoužije klasický vertikálny scroll.

Dôvodom je zachovanie mentálnej mapy:

> používateľ musí vždy vidieť, že systém má päť hlavných oblastí.

Scrollovanie sa použije až **vnútri aktívnej karty**, ak má veľa podstránok.

Teda:

```text
HLAVNÉ OBLASTI
      ↓
bez scrollovania

AKTÍVNA OBLASŤ
      ↓
podstránky
      ↓
scroll podľa potreby
```

---

# 8. Karty nesmú zakrývať ovládacie prvky

Prekrytie je vizuálna metafora.

Nemá byť skutočnou prekážkou.

Neaktívne karty musia zostať:

* klikateľné;
* čitateľné;
* dostupné klávesnicou;
* dostupné cez screen reader;
* viditeľné pri zmene mierky.

Aktívna karta musí byť identifikovateľná:

* polohou;
* textom;
* ikonou;
* stavom fokusu;
* prípadne jemným vizuálnym zvýraznením.

Nie iba farbou.

---

# 9. Animácia kariet

Prechod medzi oblasťami môže byť animovaný.

Pri kliknutí:

```text
DÁTA
   ↓
vysunie sa
   ↓
SOFTVÉR ustúpi
```

Animácia má byť krátka a pokojná.

Nemá meniť:

* šírku hlavného obsahu;
* rozloženie stránky;
* pozíciu ovládacích prvkov;
* výšku okna.

Ak používateľ vypne animácie v prístupnosti, navigácia musí fungovať bez nich.

---

# 10. Vizuálny vzťah k Správcovi súborov

Nastavenia majú používať rovnaký dizajnový jazyk ako Správca súborov.

Spoločné prvky:

* tmavý/priesvitný povrch;
* zaoblené rohy;
* horná zvýrazňovacia línia;
* rovnaké ovládacie prvky;
* rovnaká typografia;
* rovnaké aktívne riadky;
* rovnaké správanie bočného panela;
* rovnaké okno a systémové tlačidlá.

Rozdiel má byť v obsahu, nie v identite aplikácie.

Cieľ:

> **Používateľ nemá mať pocit, že otvoril cudziu aplikáciu. Otvoril ďalšiu časť LatteOS.**

---

# 11. Globálne vyhľadávanie Nastavení

Vyhľadávanie je prvotriedna funkcia.

Musí byť dostupné na hlavnej stránke aj počas prehliadania kategórií.

Horná lišta:

```text
[ 🔍 Hľadať nastavenie ]
```

Vyhľadávanie musí pracovať s:

* názvom;
* synonymami;
* popisom;
* kategóriou;
* konkrétnou hodnotou;
* stavom;
* deep-linkom na cieľovú stránku.

---

# 12. Vyhľadávanie nesmie byť iba filter

Používateľ môže zadať:

> `wifi`

Výsledky:

```text
Wi-Fi
Hardvér > Sieť > Wi-Fi

Automatické pripájanie
Hardvér > Sieť > Wi-Fi

Merané pripojenie
Hardvér > Sieť > Wi-Fi

VPN
Hardvér > Sieť > VPN
```

Pri:

> `mikrofón`

môže dostať:

```text
Mikrofón
Hardvér > Zvuk

Predvolený vstup
Hardvér > Zvuk

Oprávnenie mikrofónu
Softvér > Oprávnenia aplikácií
```

Používateľ nemusí poznať architektúru systému.

---

# 13. Vyhľadávanie môže dočasne obísť kategórie

Počas vyhľadávania sa môže päť kariet dočasne zmeniť na výsledkový panel:

```text
VÝSLEDKY HĽADANIA

🎙 Mikrofón
   Hardvér > Zvuk

🔐 Oprávnenie mikrofónu
   Softvér > Oprávnenia aplikácií
```

Po vymazaní vyhľadávania sa navigácia vráti na päť kariet.

Vyhľadávanie tak funguje ako **rýchla cesta cez celú informačnú architektúru**.

---

# 14. Deep-linking

Každá stránka alebo nastavenie musí mať jednoznačný identifikátor.

Napríklad:

```text
settings://hardware/display
settings://hardware/audio
settings://hardware/network/wifi
settings://software/updates
settings://software/permissions
settings://environment/theme
```

Špecializované aplikácie môžu mať vlastné URI:

```text
app-manager://updates
app-manager://installed
app-manager://permissions
resource-manager://display/DP-1
resource-manager://storage/nvme0
```

Nastavenia nesmú iba povedať:

> „Otvorte Správcu zdrojov.“

Musí byť možné povedať:

> „Otvorte Správcu zdrojov na konkrétnom monitore.“

---

# 15. Softvér

## 15.1 Úloha

Softvér obsahuje používateľské nastavenia súvisiace s:

* aplikáciami;
* aktualizáciami;
* oprávneniami;
* automatickým spúšťaním;
* softvérovými komponentmi;
* súkromím.

---

## 15.2 Aplikácie

**Vlastník:** App Manager

Obsah:

* nainštalované aplikácie;
* veľkosť;
* odinštalovanie;
* aktualizácie aplikácií;
* predvolené aplikácie;
* kompatibilita;
* automatické spúšťanie;
* aplikácie na pozadí.

Nastavenia zobrazia stav a otvoria App Manager.

---

## 15.3 Inštalácia aplikácií

**Vlastník:** App Manager

Môže obsahovať:

* Objavovať;
* inštalácia;
* Flatpak;
* repozitáre;
* zdroje aplikácií.

Nemá sa vytvárať druhý obchod v Nastaveniach.

---

# 16. Oprávnenia aplikácií

Oprávnenia sú súčasťou architektúry bezpečnosti LatteOS a capability modelu.

Príklady:

* súbory;
* kamera;
* mikrofón;
* sieť;
* schránka;
* oznámenia;
* obrazovka;
* externé zariadenia;
* ďalšie capability.

App Manager je používateľským vlastníkom správy oprávnení aplikácií.

Nastavenia poskytujú:

* prehľad;
* stav;
* vstup do konkrétneho oprávnenia.

Príklad:

```text
Firefox

Súbory       Povolené
Mikrofón     Zakázané
Kamera       Zakázaná
Sieť         Povolená

[ Spravovať oprávnenia ]
```

---

# 17. Aktualizácie

Aktualizácie sú jedna používateľská úloha, ale viac technických vlastníkov.

```text
                    AKTUALIZÁCIE
                         │
       ┌─────────────────┼─────────────────┐
       ↓                 ↓                 ↓
    LatteOS           Aplikácie         Firmware
latte-updated        App Manager     Resource Manager
```

Používateľ však vidí jednu stránku.

## Aktualizácie

### Systém

* LatteOS;
* systémové balíky;
* jadro;
* systémové komponenty.

### Aplikácie

* aplikácie;
* Flatpak.

### Firmware

* firmware zariadení, ak je podporovaný.

### Nastavenia aktualizácií

* automatické aktualizácie;
* časovanie;
* reštart;
* história;
* návrat po zlyhaní.

---

# 18. Aktualizovať všetko

Ak backendy umožnia bezpečné koordinované aktualizácie, používateľ môže mať:

**[ Aktualizovať všetko ]**

Nastavenia však nevykonávajú aktualizáciu samy.

Orchestrácia prebieha cez príslušné backendy.

To je zásadný rozdiel:

> **jednotné používateľské rozhranie ≠ jednotný technický vlastník.**

---

# 19. Systémové služby a relácia

Používateľská úroveň:

* aplikácie spúšťané po prihlásení;
* aplikácie na pozadí;
* rozšírenia;
* správanie po štarte;
* správanie po odhlásení;
* správanie po uspávaní.

Pokročilé:

* jednotlivé systémové služby;
* zlyhania služieb;
* detailné logy;

patria do diagnostiky alebo administrátorských nástrojov.

Používateľ nemusí vedieť, že pod LatteOS existuje systemd.

---

# 20. Súkromie

Súkromie zahŕňa používateľsky zrozumiteľné voľby:

* kamera;
* mikrofón;
* poloha;
* súbory;
* oznámenia;
* diagnostické údaje;
* zdieľanie dát.

Oprávnenia aplikácií zostávajú technicky v App Manageri a capability portáli.

---

# 21. Dáta

Dáta predstavujú objekty, ktoré používateľ vytvára, uchováva alebo zálohuje.

Patria sem:

* dokumenty;
* fotografie;
* videá;
* osobné priečinky;
* úložisko;
* zálohy;
* synchronizácia;
* dáta aplikácií;
* cache.

---

# 22. Súbory a priečinky

**Vlastník:** Správca súborov

Nastavenia môžu zobrazovať:

* predvolené priečinky;
* predvolené umiestnenia;
* predvolenú aplikáciu;
* stav koša;
* dočasné súbory.

Prehliadanie, presúvanie a mazanie súborov však vykonáva Správca súborov.

---

# 23. Úložisko

Používateľský pohľad patrí pod Dáta.

Technický vlastník zostáva Správca zdrojov.

Používateľ chce vedieť:

```text
Úložisko

ProjectLatteOS
1,82 TB / 2 TB

████████████████░░

Dokumenty       42 GB
Obrázky         88 GB
Aplikácie       310 GB
Systém          21 GB
Ostatné         ...
```

Pokročilé operácie:

* oddiely;
* SMART;
* formátovanie;
* pripájanie;
* odpájanie;
* diagnostika;

→ Správca zdrojov.

---

# 24. Zálohovanie a obnova

**Vlastník:** zálohovací nástroj

Obsah:

* čo sa zálohuje;
* cieľ;
* plán;
* posledná úspešná záloha;
* obnova súborov;
* obnova nastavení;
* obnova systému, ak ju platforma podporuje.

---

# 25. Synchronizácia

Obsah:

* synchronizované priečinky;
* online účty;
* stav synchronizácie;
* dáta aplikácií;
* cache.

Konkrétny synchronizačný backend zostáva vlastníkom operácie.

---

# 26. Hardvér

Hardvér je oblasť, kde Nastavenia zobrazujú používateľsky zrozumiteľnú konfiguráciu, zatiaľ čo Správca zdrojov vlastní živý hardvérový strom.

---

# 27. Obrazovky

Nastavenia:

* rozlíšenie;
* orientácia;
* mierka;
* obnovovacia frekvencia;
* hlavná obrazovka;
* usporiadanie;
* nočné svetlo;
* správanie po pripojení monitora.

Príklad:

```text
Obrazovky

LG 27"
2560 × 1440 @ 144 Hz
Hlavný monitor

[ Nastaviť ]
[ Usporiadať obrazovky ]

────────────────────

[ Spravovať zariadenie ]
```

Posledné tlačidlo otvorí konkrétny objekt v Správcovi zdrojov.

---

# 28. Zvuk

* výstup;
* vstup;
* hlasitosť;
* citlivosť mikrofónu;
* predvolené zariadenie;
* systémové zvuky;
* aplikácie používajúce zvuk.

**Backend:** PipeWire / audio manager.

---

# 29. Sieť

* Wi-Fi;
* káblová sieť;
* VPN;
* hotspot;
* uložené siete;
* automatické pripájanie;
* merané pripojenie;
* IPv4;
* IPv6;
* DNS;
* proxy.

Diagnostika:

* sieťové rozhranie;
* DNS;
* dostupnosť internetu.

Pokročilé operácie → Správca zdrojov.

---

# 30. Bluetooth a periférie

* Bluetooth;
* klávesnice;
* myši;
* touchpady;
* gamepady;
* USB;
* kamery;
* mikrofóny;
* tlačiarne;
* skenery.

Párovanie a živý hardvér vlastní Správca zdrojov.

---

# 31. Úložné zariadenia

Technická stránka:

* detekcia;
* pripojenie;
* odpojenie;
* stav diskov;
* USB;
* optické médiá;
* čítačky kariet.

Používateľský prehľad spotreby priestoru zostáva v:

**Dáta > Úložisko**

---

# 32. Napájanie

* batéria;
* napájanie zo siete;
* obrazovka;
* uspatie;
* zatvorenie veka;
* úsporný režim;
* vyvážený režim;
* výkonný režim;
* zdravie batérie;
* nabíjanie;
* spotreba.

---

# 33. Tlač a skenovanie

* predvolená tlačiareň;
* front;
* základné predvoľby;
* skenery.

---

# 34. Diagnostika zariadení

**Vlastník:** Správca zdrojov.

Obsah:

* model;
* výrobca;
* ovládače;
* stav zariadení;
* chyby;
* testy;
* podrobnosti.

Nastavenia môžu zobraziť agregovaný stav:

```text
Hardvér

● Všetky zariadenia pracujú normálne

[ Zobraziť diagnostiku ]
```

Podrobné diagnostické operácie nepatria do Nastavení.

---

# 35. Účet

Namiesto pôvodného názvu **Prihlásenie** sa hlavná oblasť nazýva **Účet**.

Dôvod:

„Prihlásenie“ je iba jedna časť problematiky.

Účet zahŕňa:

* používateľov;
* identitu;
* heslo;
* autentizáciu;
* biometriku;
* prihlasovanie;
* uzamknutie;
* reláciu.

---

# 36. Môj účet

* meno;
* profilový obrázok;
* typ účtu;
* používateľské údaje;
* online identita.

---

# 37. Používatelia

**Vlastník:** Správca účtov

* ďalší používatelia;
* typ účtu;
* pridanie používateľa;
* odstránenie používateľa;
* prepínanie používateľov.

---

# 38. Heslo a bezpečnostné metódy

* heslo;
* PIN;
* biometria;
* hardvérový bezpečnostný kľúč;
* ďalšie autentizačné metódy.

Autorizácia citlivých operácií používa systémový mechanizmus, napríklad polkit alebo ekvivalent LatteOS.

---

# 39. Prihlasovanie a uzamknutie

**Vlastník:** `latte-greeter` + správca relácie.

* automatické prihlásenie;
* prihlasovacia obrazovka;
* uzamknutie po nečinnosti;
* správanie po štarte;
* správanie po odhlásení;
* prístupnosť prihlasovania;
* napájacie voľby na greeteri.

---

# 40. Prostredie

Oblasť pôvodne označená ako **Vzhľad** sa rozširuje na **Prostredie**.

Dôvod:

Nie všetky nastavenia sú iba vizuálne.

Patria sem aj:

* okná;
* pracovné plochy;
* lišta;
* oznámenia;
* pracovný priestor;
* animácie;
* správanie shellu.

`latte-appearance` môže zostať technickým názvom backendu.

---

# 41. Motív a farby

* svetlý režim;
* tmavý režim;
* automatický režim;
* akcent;
* kontrast;
* priehľadnosť.

Môže obsahovať živý náhľad.

---

# 42. Písmo a mierka

* rodina písma;
* veľkosť textu;
* mierka prostredia;
* veľkosť ikon;
* hustota rozhrania.

---

# 43. Pozadie

* tapeta plochy;
* spôsob prispôsobenia;
* viac monitorov;
* prihlasovacie pozadie.

Výber súboru môže používať Správcu súborov.

Samotná konfigurácia patrí `latte-appearance`.

---

# 44. Okná

* rohy;
* záhlavie;
* tlačidlá;
* maximalizácia;
* minimalizácia;
* prichytávanie;
* správanie fokusu;
* správanie okien.

---

# 45. Pracovná plocha

* virtuálne pracovné plochy;
* počet plôch;
* prepínanie;
* pracovný priestor;
* rohy;
* automatické skrývanie panelov;
* uvítacie správanie.

Pôvodné duplicitné položky **„Okná a pracovná plocha“** a **„Pracovná plocha a okná“** sa zlúčia.

---

# 46. Lišta a systémové menu

**Vlastník:** `latte-shell`

* obsah lišty;
* hodiny;
* systémové menu;
* prompt;
* oznámenia;
* Quick Settings;
* viditeľnosť položiek;
* automatické skrývanie;
* správanie lišty.

---

# 47. Oznámenia

* povolenia;
* zvuky;
* bannery;
* história;
* Nerušiť;
* aplikácie;
* oznámenia na uzamknutej obrazovke.

---

# 48. Animácie a efekty

* animácie;
* priehľadnosť;
* efekty okien;
* prechody;
* efekty pracovnej plochy.

Pri vypnutí animácií musí byť navigácia funkčná bez vizuálnych prechodov.

---

# 49. Prístupnosť

Prístupnosť musí byť dostupná centrálne.

Obsah:

* čítačka obrazovky;
* zväčšenie;
* veľký text;
* veľký kurzor;
* kontrast;
* farebné filtre;
* obmedzenie animácií;
* titulky;
* vizuálne upozornenia;
* Sticky Keys;
* Slow Keys;
* ďalšie vstupné mechanizmy.

Prístupnosť prihlasovacej obrazovky sa musí prejaviť aj v `latte-greeter`.

---

# 50. Systém

Systém je prierezová oblasť základnej platformy.

## Jazyk a región

* jazyk;
* región;
* formáty;
* časové pásmo;
* jednotky;
* formát dátumu;
* formát času.

## Dátum a čas

* automatické nastavenie;
* časové pásmo;
* 12/24-hodinový formát;
* synchronizácia času.

## Klávesnica a vstup

* rozloženie;
* vstupné metódy;
* klávesové skratky;
* správanie klávesnice.

---

# 51. Bezpečnosť

Bezpečnosť je vlastnosť celého systému, preto nemá byť iba pod Softvérom.

Môže byť dostupná cez:

**Systém > Bezpečnosť**

Obsah:

* stav zabezpečenia;
* šifrovanie;
* Secure Boot;
* firewall;
* autentizácia;
* bezpečnostné aktualizácie;
* stav oprávnení aplikácií.

Oprávnenia aplikácií sa však nemenia na druhom mieste. Bezpečnostná stránka iba zobrazí stav a odkaz.

---

# 52. O LatteOS

Samostatná informačná stránka:

* verzia LatteOS;
* verzia jadra;
* verzia shellu;
* verzia App Managera;
* nainštalované komponenty;
* hardvérová platforma;
* licencia;
* licencie komponentov;
* identifikácia systému.

**O LatteOS nie je diagnostika.**

---

# 53. Diagnostika

Diagnostika je samostatná funkcia.

Rozdeľuje sa podľa vlastníka:

### Softvér

* aplikácie;
* služby;
* balíky;
* logy;
* pády.

### Hardvér

* zariadenia;
* ovládače;
* disky;
* sieť;
* zvuk.

### Dáta

* miesto;
* zálohy;
* poškodené dáta.

Nastavenia môžu vytvoriť agregovaný stav:

```text
Diagnostika

● Softvér
● Hardvér
● Dáta

Systém je v normálnom stave.
```

Detail otvorí správneho vlastníka.

---

# 54. Kontinuita a zdieľanie

Kontinuita môže byť budúcou funkciou LatteOS.

Potenciálne:

* zdieľanie obrazovky;
* zdieľanie súborov;
* prenos schránky;
* zariadenie-zariadenie;
* nadväzujúce funkcie medzi zariadeniami.

Kým nebude funkčne implementovaná, nemá byť samostatnou hlavnou stránkou.

Po implementácii môže vzniknúť:

**Systém > Zdieľanie a kontinuita**

---

# 55. Stavové indikátory

Každá hlavná karta môže zobrazovať stav.

Odporúčaná minimálna sada:

```text
●  OK
!  Pozornosť
×  Problém
↻  Prebieha
```

Indikátor nesmie používať iba farbu.

Musí mať:

* symbol;
* textový význam;
* prípadne farbu;
* stav dostupný pre accessibility API.

Príklad:

```text
SOFTVÉR       ●
DÁTA          ●
HARDVÉR       !
ÚČET          ●
PROSTREDIE    ●
```

---

# 56. Stavové súhrny na kartách

Neaktívna karta môže okrem názvu zobrazovať krátky stav.

Napríklad:

```text
SOFTVÉR
2 aktualizácie

DÁTA
Záloha pred 3 h

HARDVÉR
1 zariadenie

ÚČET
Prihlásený

PROSTREDIE
Tmavý motív
```

Tieto informácie nesmú nahradiť podstránky.

Majú iba pomôcť používateľovi orientovať sa.

---

# 57. Odkazy medzi Nastaveniami a manažérmi

Každá prepojená stránka má tri úrovne:

### 1. Bežná voľba

Ak je bezpečná a stabilná, používateľ ju môže meniť priamo.

### 2. Stav

Napríklad:

> Wi-Fi pripojená

> 2 aktualizácie

> Záloha pred 3 hodinami

### 3. Špecializovaná akcia

Napríklad:

> **Spravovať zariadenia**

> **Otvoriť App Manager**

> **Zobraziť diagnostiku**

Deep-link musí smerovať čo najpresnejšie.

---

# 58. Kanonický strom

## 1. Softvér

* Aplikácie
* Inštalácia aplikácií
* Aktualizácie
* Oprávnenia aplikácií
* Spúšťanie a aplikácie na pozadí
* Systémové služby
* Súkromie

## 2. Dáta

* Súbory a priečinky
* Úložisko
* Zálohovanie a obnova
* Synchronizácia a dáta aplikácií

## 3. Hardvér

* Obrazovky
* Zvuk
* Sieť
* Bluetooth a periférie
* Úložné zariadenia
* Napájanie
* Tlač a skenovanie
* Diagnostika zariadení

## 4. Účet

* Môj účet
* Používatelia
* Heslo a bezpečnostné metódy
* Prihlasovanie
* Uzamknutie

## 5. Prostredie

* Motív a farby
* Písmo a mierka
* Pozadie
* Okná
* Pracovná plocha
* Lišta a systémové menu
* Oznámenia
* Animácie a efekty
* Prístupnosť

## 6. Systém

* Jazyk a región
* Dátum a čas
* Klávesnica a vstup
* Bezpečnosť
* O LatteOS
* Diagnostika

---

# 59. Vlastníctvo

| Používateľská oblasť | Hlavný vlastník                    |
| -------------------- | ---------------------------------- |
| Softvér              | App Manager + `latte-updated`      |
| Dáta                 | Správca súborov + dátové nástroje  |
| Hardvér              | Správca zdrojov                    |
| Účet                 | Správca účtov + `latte-greeter`    |
| Prostredie           | `latte-appearance` + `latte-shell` |
| Systém               | systémové backendy                 |

---

# 60. Pravidlá vlastníctva

Platí:

> **Jedna hodnota = jeden zdroj pravdy.**

A zároveň:

> **Jedna hodnota môže mať viac používateľských vstupov.**

Ďalšie pravidlá:

1. Nastavenia nesmú vytvárať druhý parser rovnakej konfigurácie.
2. Nastavenia nesmú vytvárať druhý backend.
3. Špecializovaný manažér nesmie vytvárať konkurenčnú konfiguráciu Nastavení.
4. Zdieľané hodnoty sa musia meniť cez spoločné API alebo backend.
5. Deep-link musí smerovať na konkrétnu funkciu.
6. Stav môže byť agregovaný, zápis musí mať jednoznačného vlastníka.
7. Technická architektúra nemusí kopírovať používateľskú informačnú architektúru.

---

# 61. Technická a používateľská architektúra nemusia byť totožné

Napríklad:

```text
Používateľ:

DÁTA
 └── Úložisko

Technicky:

Správca zdrojov
 └── udisks2
      └── block devices
```

Ďalší príklad:

```text
Používateľ:

SOFTVÉR
 └── Aktualizácie

Technicky:

latte-updated
App Manager
Firmware backend
```

A:

```text
Používateľ:

ÚČET
 └── Heslo

Technicky:

account manager
PAM
polkit
greeter
```

Používateľ nemusí poznať technickú topológiu.

---

# 62. Čo nepatrí do Nastavení

Do hlavného Nastavenia nepatrí:

* celý katalóg aplikácií;
* obchodný obsah;
* živý hardvérový strom;
* kernelové detaily;
* terminál;
* editovanie konfiguračných súborov;
* pokročilé firewall pravidlá;
* administrátorské sieťové pravidlá;
* detailné systémové logy;
* správca súborov;
* interné diagnostické nástroje;
* konfigurácia konkrétnej aplikácie, ktorú vlastní samotná aplikácia.

---

# 63. App Manager a Nastavenia

Používateľ môže aplikácie spravovať z dvoch miest:

### App Manager

Priamy vstup:

```text
Objavovať
Aktualizácie
Nainštalované
Oprávnenia
```

### Nastavenia

```text
Softvér
 ├── Aplikácie
 ├── Aktualizácie
 └── Oprávnenia
```

Obe cesty vedú na rovnaké funkcie.

Nesmú vytvárať dve implementácie.

---

# 64. Správca zdrojov a Nastavenia

Nastavenia:

```text
Hardvér
 ├── Obrazovky
 ├── Zvuk
 ├── Sieť
 ├── Bluetooth
 └── Napájanie
```

Správca zdrojov:

```text
Zariadenia
 ├── PCI
 ├── USB
 ├── Disks
 ├── Network interfaces
 ├── Displays
 ├── Audio
 └── Drivers
```

Používateľský pohľad je zjednodušený.

Technický pohľad je úplný.

---

# 65. `index.toml`

Technický register môže zostať rozdelený podľa backendov.

Napríklad:

```text
apps
updates
devices
network
accounts
personalization
accessibility
system
```

UI však tieto technické skupiny mapuje do používateľských vrstiev.

Príklad:

| UI         | Technické skupiny                           |
| ---------- | ------------------------------------------- |
| Softvér    | `apps`, `updates`, časť `system`            |
| Dáta       | `storage`, časť `system`                    |
| Hardvér    | `devices`, `network`, `power`               |
| Účet       | `accounts`, `greeter`                       |
| Prostredie | `personalization`, `shell`, `accessibility` |
| Systém     | `system`, `security`                        |

---

# 66. Odstránenie duplicít

Z existujúceho registra treba odstrániť alebo zlúčiť konkurenčné vstupy:

```text
updates
+
app updates
→
Aktualizácie
```

```text
storage
+
data storage
→
Úložisko
```

```text
wifi
+
network
→
Sieť
```

```text
lockscreen
+
login
→
Účet > Prihlasovanie a uzamknutie
```

```text
permissions
+
camera/microphone/privacy
→
Oprávnenia aplikácií + Súkromie
```

```text
appearance
+
desktop visuals
→
Prostredie
```

```text
clock
+
language
→
Systém
```

---

# 67. Špeciálne pravidlo pre kameru a mikrofón

Kamera a mikrofón majú dve používateľské perspektívy.

### Hardvér

> Existuje kamera/mikrofón?

→ Hardvér.

### Súkromie

> Ktorá aplikácia ich môže používať?

→ Softvér > Oprávnenia / Súkromie.

Tieto stránky nesmú vytvoriť dva zdroje pravdy.

---

# 68. Domovská stránka ako agregátor

Domov môže zobrazovať:

```text
● Systém aktuálny
● Sieť pripojená
● Úložisko 78 %
! 1 aktualizácia
● Záloha úspešná
```

Ale agregovaný stav neznamená vlastníctvo.

Napríklad:

```text
Domov
  ↓
Hardvér
  ↓
Správca zdrojov
```

---

# 69. Rýchle nastavenia

Quick Settings zostávajú súčasťou LatteOS Shellu.

Môžu meniť najčastejšie hodnoty:

* Wi-Fi;
* Bluetooth;
* hlasitosť;
* jas;
* nočný režim;
* Nerušiť;
* výkonový režim.

Nastavenia poskytujú úplnú konfiguráciu.

Quick Settings poskytujú rýchlu zmenu.

---

# 70. Nedávne nastavenia

Domovská stránka môže obsahovať:

```text
Nedávno použité

Obrazovky
Motív a farby
Wi-Fi
Úložisko
```

História má byť lokálna používateľská funkcia a nemá vytvárať nové kategórie.

---

# 71. Prístupnosť navigácie

Karty musia byť ovládateľné:

* myšou;
* klávesnicou;
* dotykom;
* screen readerom.

Klávesová navigácia:

```text
Tab
  ↓
Softvér
  ↓
Dáta
  ↓
Hardvér
  ↓
Účet
  ↓
Prostredie
```

Aktívna karta sa musí dať rozbaliť klávesou Enter/Space.

Podkategórie musia mať normálnu hierarchiu fokusu.

---

# 72. Responsivita

Pri širokom okne:

```text
[ Softvér ]
[ Dáta ]
[ Hardvér ]
[ Účet ]
[ Prostredie ]
```

Pri menšom okne:

* karta sa zmenší;
* zobrazí ikonu;
* názov zostane čitateľný;
* stav zostane dostupný.

Nesmie sa okamžite premeniť na neidentifikovateľné hamburger menu.

Pri veľmi malom priestore môže aktívna karta prejsť do compact režimu.

---

# 73. Stav karty v compact režime

Napríklad:

```text
[ ◉ ]
[ ▣ ]
[ ⚙ ]
[ 👤 ]
[ ◈ ]
```

Po hover/fokuse:

```text
[ ⚙ HARDVÉR ! ]
```

Toto však musí byť doplnok.

Na bežnej desktopovej obrazovke má zostať:

**ikona + názov + stav.**

---

# 74. Odporúčaný model jednej stránky

Každá stránka Nastavení by mala mať rovnakú vnútornú štruktúru:

```text
Názov
Krátke vysvetlenie

┌─────────────────────────────┐
│ Hlavná konfigurácia         │
└─────────────────────────────┘

┌─────────────────────────────┐
│ Ďalšie nastavenia           │
└─────────────────────────────┘

Stav
─────────────────────────────

[ Spravovať v ... ]
```

Používateľ tak postupne spozná jeden jazyk Nastavení.

---

# 75. Stav + voľba + špecializovaný správca

Každá prepojená stránka má ideálne:

```text
VOĽBA
↓
AKTUÁLNY STAV
↓
DETAIL
↓
ŠPECIALIZOVANÝ SPRÁVCA
```

Príklad:

```text
Obrazovka

2560 × 1440
144 Hz
100 %

[ Zmeniť ]

────────────────────

[ Spravovať zariadenie ]
```

---

# 76. Bezpečné operácie vs. administrátorské operácie

Bežné:

* zmena jazyka;
* zmena motívu;
* zmena rozlíšenia;
* výber zvukového výstupu.

Citlivé:

* pridanie používateľa;
* zmena systémových oprávnení;
* formátovanie disku;
* firewall;
* šifrovanie.

Citlivé operácie musia vyvolať systémovú autorizáciu.

---

# 77. MVP

Prvá použiteľná verzia Nastavení má obsahovať:

1. päť hlavných vrstvených kariet;
2. domovskú stránku;
3. globálne vyhľadávanie;
4. Prostredie;
5. Obrazovky;
6. Zvuk;
7. Wi-Fi;
8. Bluetooth;
9. Úložisko;
10. Účet;
11. Jazyk a čas;
12. Aktualizácie;
13. základný stav systému;
14. deep-linking do App Managera;
15. deep-linking do Správcu zdrojov;
16. O LatteOS;
17. základnú diagnostiku.

---

# 78. Neskoršia fáza

Neskôr:

* komplexná zálohovacia integrácia;
* synchronizácia;
* bezpečnostný dashboard;
* kontinuita;
* device-to-device funkcie;
* pokročilá diagnostika;
* podrobné energy reporting;
* inteligentné odporúčania Nastavení.

AI však nesmie byť základnou súčasťou architektúry Nastavení.

Ak bude LatteOS AI používať, AI má pracovať **nad existujúcim Settings API**, nie vytvárať vlastný paralelný systém konfigurácie.

---

# 79. Princíp pre budúce AI rozhranie

Používateľ môže napríklad povedať:

> „Nastav tmavý režim.“

AI nesmie sama obchádzať Nastavenia.

Namiesto toho musí vyvolať rovnakú operáciu ako používateľ:

```text
AI
 ↓
Settings API
 ↓
latte-appearance
 ↓
appearance.toml
```

Pri citlivých operáciách musí existovať potvrdenie.

Tým zostáva zachovaný základný princíp LatteOS:

> **AI je klient systému, nie vlastník systému.**

---

# 80. Stavové a diagnostické informácie

Diagnostika sa rozhoduje podľa toho, **čo diagnostikuje**, nie podľa toho, kde sa výsledok zobrazí.

### Softvér

App Manager / `latte-diagd`

### Hardvér

Správca zdrojov

### Dáta

Správca súborov / zálohovací nástroj

### Celkový stav

Nastavenia môžu výsledky agregovať.

---

# 81. Praktická mapa vlastníctva

| Funkcia                | Používateľské miesto        | Vlastník                   |
| ---------------------- | --------------------------- | -------------------------- |
| Rozlíšenie             | Hardvér > Obrazovky         | display backend            |
| Monitory               | Hardvér > Obrazovky         | Správca zdrojov            |
| Hlasitosť              | Hardvér > Zvuk              | PipeWire                   |
| Wi-Fi                  | Hardvér > Sieť              | NetworkManager             |
| Bluetooth              | Hardvér > Bluetooth         | BlueZ                      |
| Disky                  | Hardvér > Úložné zariadenia | udisks2 / Resource Manager |
| Miesto na disku        | Dáta > Úložisko             | dátový/storage backend     |
| Aplikácie              | Softvér > Aplikácie         | App Manager                |
| Aktualizácie aplikácií | Softvér > Aktualizácie      | App Manager                |
| Aktualizácie LatteOS   | Softvér > Aktualizácie      | `latte-updated`            |
| Firmware               | Softvér > Aktualizácie      | firmware backend           |
| Používatelia           | Účet > Používatelia         | Account Manager            |
| Heslo                  | Účet > Heslo                | Account Manager/PAM        |
| Motív                  | Prostredie > Motív          | `latte-appearance`         |
| Lišta                  | Prostredie > Lišta          | `latte-shell`              |
| Oprávnenia             | Softvér > Oprávnenia        | App Manager/portal         |
| Firewall               | Systém > Bezpečnosť         | security backend           |
| Zálohy                 | Dáta > Zálohovanie          | backup manager             |

---

# 82. Hlavné menu LatteOS

Systémové menu môže obsahovať:

```text
Nastavenia systému
App Manager
Správca zdrojov
Správca súborov
```

Ich úlohy:

### Nastavenia systému

Celková konfigurácia a stav.

### App Manager

Aplikácie.

### Správca zdrojov

Hardvér a technické zdroje.

### Správca súborov

Dáta a súbory.

Tak vzniká jasný ekosystém špecializovaných aplikácií.

---

# 83. Dôležité pravidlo navigácie

Používateľ môže začať na ktoromkoľvek mieste.

Napríklad:

```text
App Manager
  ↓
Oprávnenia
```

alebo:

```text
Nastavenia
  ↓
Softvér
  ↓
Oprávnenia
```

Obe cesty musia viesť na rovnaký objekt.

Rovnako:

```text
Nastavenia
  ↓
Hardvér
  ↓
Obrazovky
  ↓
Spravovať
```

môže otvoriť:

```text
Správca zdrojov
  ↓
Monitor LG
```

Nie jeho domovskú stránku.

---

# 84. Čo je teda Nastavenie systému LatteOS

Nie je to:

> jedna obrovská aplikácia, ktorá vlastní celý počítač.

Nie je to ani:

> obyčajný zoznam odkazov na iné aplikácie.

Je to:

> **jednotná používateľská mapa systému nad modulárnou architektúrou backendov.**

Jej tri hlavné úlohy sú:

```text
               NASTAVENIA
                    │
       ┌────────────┼────────────┐
       ↓            ↓            ↓
    KONFIGURÁCIA    STAV      NAVIGÁCIA
       │            │            │
       └────────────┼────────────┘
                    ↓
              ŠPECIALIZOVANÉ
                BACKENDY
```

---

# 85. Finálna informačná architektúra

Celé Nastavenia možno teda chápať takto:

```text
Nastavenia
│
├── Domov
│   ├── Stav systému
│   ├── Upozornenia
│   ├── Nedávne
│   └── Odporúčané
│
├── SOFTVÉR
│   ├── Aplikácie
│   ├── Aktualizácie
│   ├── Oprávnenia aplikácií
│   ├── Spúšťanie
│   ├── Služby
│   └── Súkromie
│
├── DÁTA
│   ├── Súbory
│   ├── Úložisko
│   ├── Zálohovanie
│   └── Synchronizácia
│
├── HARDVÉR
│   ├── Obrazovky
│   ├── Zvuk
│   ├── Sieť
│   ├── Bluetooth
│   ├── Úložné zariadenia
│   ├── Napájanie
│   ├── Tlač
│   └── Diagnostika
│
├── ÚČET
│   ├── Môj účet
│   ├── Používatelia
│   ├── Heslo a bezpečnostné metódy
│   ├── Prihlasovanie
│   └── Uzamknutie
│
├── PROSTREDIE
│   ├── Motív a farby
│   ├── Písmo a mierka
│   ├── Pozadie
│   ├── Okná
│   ├── Pracovná plocha
│   ├── Lišta
│   ├── Oznámenia
│   ├── Animácie
│   └── Prístupnosť
│
└── SYSTÉM
    ├── Jazyk a región
    ├── Dátum a čas
    ├── Klávesnica a vstup
    ├── Bezpečnosť
    ├── O LatteOS
    └── Diagnostika
```

---

# 86. Finálne UX pravidlá

Pre implementáciu Nastavení LatteOS platí:

1. **Päť hlavných oblastí je stále viditeľných.**
2. **Hlavné oblasti sa nescrollujú.**
3. **Podstránky aktívnej oblasti sa môžu scrollovať.**
4. **Aktívna oblasť sa vysúva dopredu ako karta.**
5. **Prekrytie je vizuálna metafora, nie blokovanie ovládacích prvkov.**
6. **Vyhľadávanie je globálne a prvotriedne.**
7. **Vyhľadávanie môže obísť kategórie a otvoriť konkrétnu hodnotu.**
8. **Každá hodnota má jeden zdroj pravdy.**
9. **Jedna hodnota môže mať viac vstupných bodov.**
10. **Nastavenia môžu meniť bežné hodnoty priamo.**
11. **Pokročilé operácie otvárajú špecializovaného manažéra.**
12. **Deep-link musí smerovať na konkrétnu funkciu alebo objekt.**
13. **Stav systému môže byť agregovaný, vlastníctvo nie.**
14. **Technická architektúra backendov nemusí kopírovať používateľskú architektúru.**
15. **Farba nikdy nesmie byť jediným nositeľom stavu.**
16. **Karty a stránky musia byť prístupné klávesnicou a screen readerom.**
17. **Animácia je doplnok, nie podmienka navigácie.**
18. **Nastavenia nemajú používateľovi odhaľovať Linuxovú technickú architektúru, pokiaľ ju nepotrebuje.**
19. **AI môže byť klientom Settings API, nie jeho vlastníkom.**
20. **LatteOS má používateľovi ukázať jeden systém, aj keď ho technicky tvorí viacero špecializovaných komponentov.**

---

# 87. Záver

Nastavenia LatteOS sa týmto návrhom definujú ako **centrálna mapa operačného systému**, nie ako monolitický správca všetkých jeho funkcií.

Používateľ vidí:

**Softvér · Dáta · Hardvér · Účet · Prostredie**

a medzi nimi sa pohybuje pomocou vrstvených kariet.

Technicky však za nimi zostávajú samostatné komponenty:

**App Manager · Správca zdrojov · Správca súborov · Správca účtov · `latte-updated` · `latte-appearance` · bezpečnostné a systémové backendy.**

Tým vzniká dôležitá kombinácia:

> **Jednoduché rozhranie navonok. Modulárny systém pod ním.**

A najdôležitejšie architektonické pravidlo celej aplikácie je:

> **Jedna hodnota má jeden zdroj pravdy, ale môže mať viac bezpečných vstupných bodov.**

To umožňuje, aby používateľ nastavil napríklad Wi-Fi z Nastavení, Quick Settings alebo Správcu zdrojov bez toho, aby LatteOS vytváral tri rôzne systémy pre správu Wi-Fi.

Nastavenia teda nie sú ďalší správca.

Sú **vrstva, ktorá dáva celému systému používateľsky pochopiteľnú mapu**.
