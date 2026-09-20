#zbierka napadov#

# okná. forlift design. zistit okna v složke ideas. lavy priehladny panel je cez cele okno. odhora dole. či je to vlastnost progaramu forklift pre mac, alebo je to bežne mac prostredie. a či to ide zrealizovat. a použit defakto takmer pre každe okno lateOS aplikacii a rozhrania. . 
#ked už sa dokaže takto zmenit vzhlad hornej lišty, skrz viacero aplikacii, neda sa doprava vedla minimalize preidat aj placeholder kde neskorej bude tlačidlo NET ? 
# spravca suborov. kliknutie  vlavom panely na složku ju umožni premenovat. čo keby v tom kontextovom menu bola aj farba. zmenit farebne označenie opisu složky. 
spominal som že v zaklade je originalne latte OS editor dokumentov. možeme ho nazvat Heidelberg.ten bude vediet otvorit upravit uložit formatovat rozne druhy textovych suborov. txt,rtf,doc, mobi, epub, md, xml, html,json,.pages, oddt. vratane pdf ak to nie je nemožne. 
nie ako predinstalovana ,ale ako originalne aplikacie aj zakladny balik potrebnych app. nielen text editor ale aj napr kalkulačka, doom, quake2, steam dokaže spolupracovat s latte skinon? latte farby? podpora pre vlc player. tiež podprora pre najoblubenejšie to-do a kalendarove aplikacie. integrovanu welbeing službu a time management.

# Latte System Monitor / Process Manager

Nie je to dalsia uroven nastaveni aplikacii ani hardware manager. Je to nastroj na sledovanie a spravu realneho aktualneho stavu systemu.

- zobrazuje zive udaje o CPU, RAM, diskoch, sieti, GPU, teplotach a spotrebe
- ukazuje okamzitu aj kratku historicku zataz, nie konfiguraciu zariadeni
- spravuje aktivne procesy: strom procesov, vlastnik, cesta, systemovy alebo pouzivatelsky proces, ukoncenie a nasilne ukoncenie
- rozlisuje systemove, desktopove, pouzivatelske a pomocne procesy
- poskytuje udaje cez standardne lokalne rozhranie pre OLED displeje vodneho chladenia, Stream Deck pluginy, panel a dalsie zobrazovace
- distribuuje telemetry bez toho, aby sam preberal konfiguraciu cieloveho zariadenia alebo pluginu
- identifikuje polozky spustene pri starte: desktop autostart, systemd sluzby a timery, cron a dalsie podporovane autorun mechanizmy
- umoznuje autorun polozku zakazat, povolit a zobrazit jej povod, vlastnika a spustany prikaz
- pri zasahu zobrazuje varovanie, ci ide o systemovy proces alebo proces pouzivatela

Hranice kompetencii:

- App Manager nastavuje a konfiguruje aplikacie
- Device Manager nastavuje hardver a zariadenia
- Latte System Monitor cita aktualny stav, identifikuje jeho zdroje, poskytuje telemetry a umoznuje bezpecne ukoncit proces alebo upravit autorun

Odporucane rozhranie: hlavna obrazovka s prehladom ziveho stavu, karta Procesy, karta Autorun a karta Vystupy telemetry. Pokrocile diagnosticke udaje maju byt volitelne, aby nastroj zostal rychly a sustredeny na aktualne dianie.