# Bughunt 1 — LatteOS gamerdistro

**VM:** `latteOSdev`, Fedora Linux 44, VirtualBox, Hyprland/Noctalia  
**Revízia:** `63e9cff` (`gamerdistro`), čistý pracovný strom pri kontrole  
**Pravidlo:** audit je read-only; nebol upravený systém ani zdrojový kód. Snímky obrazovky sú v `bughunt/`.

## Stavový prelet

- Žiadne zlyhané systemd jednotky pri prvom prelete; koreňový disk 50 % a dostupná RAM približne 8.5 GiB.
- Grafická relácia beží; testovací proces `latte-autoplay` je aktívny. Počas jeho behu som neposielal vstup ani nemenil okná.
- Zatiaľ bez potvrdeného vizuálneho bugu. `bughunt/00-session-baseline.png` je len referenčná snímka, nie nález.

## BH-001 — Autoplay testovací USB obraz sa automaticky nepripojil

**Priorita:** P2, predbežný nález  
**Stav:** reprodukovaný stav v testovacej VM; fyzické USB zatiaľ neoverené  
**Oblasť:** Automatické prehrávanie / UDisks

**Nastavenie a podmienky:** Beží `latte-autoplay` s `LATTE_AUTOPLAY_TEST=1` a `LATTE_AUTOPLAY_PREF=nic`. V systéme je testovací 20 MiB FAT16 loop disk `/dev/loop0`, label `TESTUSB`.

**Očakávané:** Voľba `nic` znamená médium pripojiť, ale nevykonať ďalšiu akciu. Po rozpoznaní testovacieho média by malo mať pripojovací bod.

**Pozorované:** `udisksctl info -b /dev/loop0` uvádza prázdne `MountPoints`; `findmnt --source /dev/loop0` nič nevracia. Súčasne log monitora obsahuje GLib runtime warning:

```text
runtime check failed: (g_strv_length ((gchar **) invalidated_properties) == 0)
```

**Reprodukcia / overenie:** V testovacom režime vytvoriť alebo pripojiť testovací loop disk s podporovaným filesystemom, ponechať preferenciu `nic` a overiť, či ho LatteOS pripojí. V tejto relácii zostal `TESTUSB` nepripojený. Keďže ide o loop disk s `HintSystem=true`, treba ešte overiť rovnaký scenár na skutočnom USB; príčina môže byť obmedzením testovacieho média/UDisks, nie samotného autoplay.

**Dôkaz:** [Snímka aktuálnej relácie](bughunt/01-autoplay-observed.png). Snímka je kontextová; rozhodujúci dôkaz stavu pripojenia je výpis `udisksctl info` a `findmnt` z auditu.

## BH-002 — Hyprland spadol v Mesa llvmpipe pri vykresľovaní

**Priorita:** P1  
**Stav:** opakovane potvrdené core dumpmi a journalom; príčina neznáma  
**Oblasť:** NORMAL relácia / VM softvérové vykresľovanie

**Pozorované:** Hlavný Hyprland skončil signálom `SIGSEGV` najmenej päťkrát medzi 23. a 26. 9. 2026. Core dumpy z 23. 9. (PID 2492, 6980), 25. 9. (PID 50493, 749888) a 26. 9. (PID 1548) obsahujú rovnaké Mesa `libgallium-26.2.3.so` / llvmpipe rasterizačné rámce. Posledný pád nastal 26. 9. približne o 13:47:30 po 23 805 sekundách behu. O 13:47:29 sa spustil Flatpak Akizip; tesne pred pádom jadro dvakrát hlásilo `vmwgfx: Failed to open channel`. Časová súvislosť neurčuje príčinu. O 13:47:33 Akizip zalogoval `Lost connection to Wayland compositor`; tento záznam je následok pádu, nie dôkaz jeho príčiny.

**Dopad:** Pád kompozitora prerušil Wayland reláciu a rozpojil jej klientov. `latte-session` ho automaticky spustil znova približne o tri sekundy neskôr (`reštart 1/3`); aplikácie/portály sa obnovovali v novej relácii. Spúšťač pádu nie je určený.

**Dôkaz:** Core dumpy uvedených PIDov a journal z 13:47:28–13:47:37. Po poslednom páde `latte-session` Hyprland automaticky spustil znova (`reštart 1/3`); následný `latte-boot status` potvrdil `mode=normal`, `crash_count_now=0`, `force_safe=false`, čiže zdravá obnova počítadlo vynulovala. Dva pády `xdg-desktop-portal-hyprland` nasledovali bezprostredne po compositor pádoch a vyzerajú kaskádovo; osobitný portal core dump z 24. 9. ešte nie je vysvetlený. [Snímka po poslednom páde/obnovení](bughunt/02-after-crash-recovery.png) zachytáva až aktuálny stav; okamih pádu už spätne snímať nemožno.

## bug001 — Hľadanie softvéru pre ZIP spúšťa chýbajúci GNOME Software

**Priorita:** P2  
**Stav:** používateľom reprodukované a doložené snímkou; presný volajúci zatiaľ neurčený  
**Oblasť:** otvorenie stiahnutého súboru / hľadanie aplikácie

**Kroky:** V Súboroch otvoriť stiahnutý `.zip` a zvoliť funkciu na nájdenie vhodného softvéru pre príponu.

**Očakávané:** LatteOS otvorí vlastný App Manager alebo inú dostupnú cestu k vhodnej aplikácii pre archív.

**Pozorované:** Pokus o spustenie `gnome-software` zlyhá. V systéme balík `gnome-software` nie je nainštalovaný.

**Dôkazy:** [Používateľova snímka bug001](bughunt/bug001.png). Používateľ potvrdil, že Akizip nainštaloval ručne až po tomto incidente; dnešný ZIP handler a MIME asociácia preto nepreukazujú, čo bolo nastavené v čase chyby, a nie sú workaroundom, ktorý vtedy fungoval. Aktuálne na VM balík `gnome-software` nie je nainštalovaný a `x-scheme-handler/appstream` nemá predvolenú aplikáciu. Aktívny LatteOS zdroj nemá priame volanie `gnome-software`; Súbory majú vlastnú funkciu „Otvoriť archív ako priečinok“ a App Manager má kontrolu `latte-apps check`. To ukazuje na chýbajúcu integráciu systémovej akcie „nájsť softvér“, ale presný komponent, ktorý `gnome-software` žiada spustiť, ešte nie je určený.

**Dopad / rozsah:** Zlyháva objavenie aplikácie z tejto akcie. Presná MIME detekcia ani následné ručné otvorenie archívu v pôvodnom čase incidentu nie sú spätne potvrdené.

## Poznámky, zatiaľ nie nálezy

- Pri staršom reštarte `latte-netd` o 07:45 journal zaznamenal `ExecStopPost` s `Permission denied` pri spustení `/usr/sbin/nft`. Aktuálny unit používa `nft destroy` a toleruje chybu; dopad na stav firewallu nebol bezpečne overený bez zastavenia služby, preto to zatiaľ neoznačujem za potvrdený bug.
- Predchádzajúci nález o spustení aplikácie bez sandboxu pri chýbajúcom `bubblewrap` je v revízii `63e9cff` opravený: aktuálny `latte-sandbox` aplikáciu odmietne spustiť.
