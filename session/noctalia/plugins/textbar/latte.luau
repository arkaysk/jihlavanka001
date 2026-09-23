--!nonstrict
-- Režim Lokálne: nastavenia a akcie LatteOS, hľadané aj bez prefixu (spolu s aplikáciami Noctalie).
local home = noctalia.getenv("HOME") or ""
local cfgHome = noctalia.getenv("XDG_CONFIG_HOME") or (home .. "/.config")

local function hypr(code) return { "hyprctl", "eval", code } end
local function tier(name)
  return { "sh", "-c", "mkdir -p '" .. cfgHome .. "/latteos' && printf '%s\\n' " .. name .. " > '" .. cfgHome .. "/latteos/tier' && hyprctl reload" }
end

-- { title, subtitle, glyph, kľúčové slová, príkaz }
local items = {
  { "Systémové menu LatteOS", "Relácia, systém, režim, napájanie", "coffee", "system menu latte napajanie", { "noctalia", "msg", "panel-toggle", "latteos/system:menu" } },
  { "Režim okien: nekonečná páska", "Super+W prepína", "layout-columns", "okna paska scrolling rezim", hypr('require("latte.windows").apply("paska", true)') },
  { "Režim okien: dlaždice", "Super+W prepína", "layout-grid", "okna dlazdice tiling rezim", hypr('require("latte.windows").apply("dlazdice", true)') },
  { "Režim okien: plávajúce", "Super+W prepína", "app-window", "okna plavajuce floating rezim", hypr('require("latte.windows").apply("plavajuce", true)') },
  { "Stupeň výkonu: Plný", "Sklo, blur, žiara, animácie", "bolt", "stupen vykon plny efekty blur", tier("plny") },
  { "Stupeň výkonu: Štandard", "Menší blur, animácie", "bolt", "stupen vykon standard", tier("standard") },
  { "Stupeň výkonu: Úsporný", "Bez blur a tieňov, krátke animácie", "leaf", "stupen vykon usporny", tier("usporny") },
  { "Stupeň výkonu: Softvér", "Bez efektov (VM, slabé PC)", "cpu", "stupen vykon softver vm", tier("softver") },
  { "Stupeň výkonu: automaticky", "Podľa hardvéru (latte-boot)", "wand", "stupen vykon auto automaticky", { "sh", "-c", "rm -f '" .. cfgHome .. "/latteos/tier' && hyprctl reload" } },
  { "Nabudúce naštartovať SAFE", "Núdzový režim pri ďalšom štarte", "shield", "safe nudzovy rezim start", { "latte-boot", "force-safe" } },
  { "Nastavenia", "Vzhľad, lišta, panely, tapeta", "settings", "nastavenia settings vzhlad", { "noctalia", "msg", "settings-open" } },
  { "Tapeta", "Vybrať tapetu LatteOS", "photo", "tapeta wallpaper pozadie", { "noctalia", "msg", "panel-toggle", "wallpaper" } },
  { "Riadiace centrum", "Wi-Fi, Bluetooth, zvuk, jas", "adjustments", "riadiace centrum wifi bluetooth zvuk device", { "noctalia", "msg", "panel-toggle", "control-center" } },
  { "Sieť", "Pripojenia (nmtui)", "wifi", "siet wifi internet network", { "foot", "-e", "nmtui" } },
  { "Správca procesov", "Ctrl+Shift+Esc", "activity", "procesy task manager aktivita", { "foot", "-e", "top" } },
  { "Súbory", "Domovský priečinok", "folder", "subory files data manager", { "xdg-open", home } },
  { "Terminál", "foot", "terminal-2", "terminal konzola shell", { "foot" } },
  { "Zamknúť obrazovku", "Super+L", "lock", "zamknut lock", { "noctalia", "msg", "session", "lock" } },
}

function onQuery(text)
  local q = string.lower(text or "")
  local results = {}
  if q == "" then
    launcher.setResults(text, results)
    return
  end
  for i, it in ipairs(items) do
    local score = noctalia.fuzzyScore(q, string.lower(it[1] .. " " .. it[4]))
    if score then
      table.insert(results, { id = tostring(i), title = it[1], subtitle = it[2], glyph = it[3], score = score })
    end
  end
  launcher.setResults(text, results)
end

function onActivate(id)
  local it = items[tonumber(id) or 0]
  if it then noctalia.runAsync(it[5]) end
end
