--!nonstrict
-- Dlaždica Zariadení (pravý roh lišty): zrkadlo dlaždice aplikácií (zadanie 25. 9.) — rovnaká pokojná textúra
-- (vlastná pre pravé L: bar-scene-vpravo, inak bar-scene), v strede pomaly sa striedajúca ikona sieť / zvuk / nastavenia.
-- Klik = Správca zariadení v tvare L (latte-rychle). Zadanie 26. 9.: dlaždica je o niečo širšia a ukazuje silu Wi-Fi
-- a stav batérie (iba ak má počítač batériu / je pripojený cez Wi-Fi); sú to iba ukazovatele, klik otvára okno.
-- Pravidlá starej verzie:
--   - pasívny pohyb (cyklus ~8 s), najviac 10 obr/s; nič sa nemení podľa stavu systému,
--   - statický snímok je vždy čitateľný (ikona), navigácia sa na pohyb nespolieha,
--   - pri softvérovom kreslení (VM, stupeň Softvér/Minimálny) alebo v hernom režime sa hýbe iba pod kurzorom.
local home = noctalia.getenv("HOME") or ""
local cfgHome = noctalia.getenv("XDG_CONFIG_HOME") or (home .. "/.config")
local stateHome = noctalia.getenv("XDG_STATE_HOME") or (home .. "/.local/state")

local W0, H = 88, 34             -- dlaždica ≈ 2,5 : 1 (ostrov lišty má výšku ~40); s ukazovateľmi širšia
local wifi, bat, charging = nil, nil, false      -- sila Wi-Fi 0–100 (nil = nie je Wi-Fi), batéria % (nil = bez batérie)
local polled = -100
local BARS = 7                   -- stĺpce textúry na každej strane ikony
local t0 = 0                     -- čas animácie v s
local hovered = false
local anim, scene, still = "kurzor", "para", false
local devGlyphs, gi, gt = { "wifi", "volume", "adjustments" }, 1, 0

local function trim(s) return (string.gsub(s or "", "^%s*(.-)%s*$", "%1")) end
local function readPref(name, default)
  local v = trim(noctalia.readFile(cfgHome .. "/latteos/" .. name) or "")
  return v ~= "" and v or default
end

local function loadPrefs()
  local tier = string.match(noctalia.readFile("/run/latteos/mode.toml") or "", 'tier = "(%a+)"') or "softver"
  local forced = trim(noctalia.readFile(cfgHome .. "/latteos/tier") or "")
  if forced ~= "" then tier = forced end
  local game = trim(noctalia.readFile(stateHome .. "/latteos/game-mode") or "0") == "1"
  local cheap = tier == "softver" or tier == "minimalny" or tier == "safe" or game
  anim = readPref("bar-anim", cheap and "kurzor" or "vzdy")
  scene = readPref("bar-scene-vpravo", readPref("bar-scene", "para"))
end

local function moving() return anim == "vzdy" or (anim == "kurzor" and hovered) end

-- para: stĺpce ako para nad šálkou, pomaly dýchajú (fáza posunutá po stĺpcoch)
local function para(side)
  local out = {}
  for i = 1, BARS do
    local k = side == "l" and (BARS - i + 1) or i          -- vzdialenosť od ikony
    local phase = t0 * (2 * math.pi / 8) + k * 0.7 + (side == "l" and 0 or 1.9)
    local h = 6 + (H - 14) * (0.5 + 0.5 * math.sin(phase)) * (1 - k / (BARS + 3))
    local a = 0.22 + 0.30 * (1 - k / (BARS + 1))
    table.insert(out, ui.box({ width = 3, height = math.floor(h), radius = 2, fill = string.format("primary/%.2f", a) }))
  end
  return out
end

-- matrix: stekajúce číslice v akcente témy (stĺpec = jeden znak, jas podľa „kvapky“)
local glyphs = { "0", "1", "L", "7", "A", "3", "T", "9", "E", "5" }   -- iba znaky, ktoré má každé písmo
local function matrix(side)
  local out = {}
  for i = 1, BARS do
    local seed = (side == "l" and i or i + 11)
    local drop = (t0 * 1.2 + seed * 0.37) % 1
    local ch = glyphs[(math.floor(t0 * 2 + seed * 3) % #glyphs) + 1]
    table.insert(out, ui.label({ text = ch, fontSize = 9, color = string.format("primary/%.2f", 0.15 + 0.6 * drop), width = 5, textAlign = "center" }))
  end
  return out
end

-- textúry okien v tvare L (apps/common/Scena.qml): matrix a para kreslí dlaždica sama; jedna farba a pomalé svetlo
-- menia výplň; ozubené kolesá a obrázok/GIF dlaždica nevie, ukáže paru (v okne L sa kreslia celé)
local function render()
  local kind, arg = string.match(scene, "^(%a+):?(.*)$")
  kind = kind or "para"
  local tex = kind == "matrix" and matrix or para
  local row = {}
  local plain = kind == "solid" or kind == "glow"
  if not plain then for _, n in ipairs(tex("r")) do table.insert(row, n) end end
  -- ukazovatele Wi-Fi a batérie (iba ak sú), inak striedajúca sa ikona zariadení
  local ind = {}
  if wifi then
    local g = wifi >= 70 and "wifi" or (wifi >= 45 and "wifi-2" or (wifi >= 20 and "wifi-1" or "wifi-0"))
    table.insert(ind, ui.glyph({ name = g, size = 16, color = "on_surface" }))
  end
  if bat then
    local g = charging and "battery-charging" or (bat >= 85 and "battery-4" or (bat >= 60 and "battery-3" or (bat >= 35 and "battery-2" or "battery-1")))
    table.insert(ind, ui.glyph({ name = g, size = 16, color = (bat < 15 and not charging) and "error" or "on_surface" }))
    table.insert(ind, ui.label({ text = tostring(bat), fontSize = 10, color = "on_surface" }))
  end
  if #ind > 0 then table.insert(row, ui.row({ gap = 3, align = "center" }, ind))
  else table.insert(row, ui.glyph({ name = devGlyphs[gi], size = 18, color = "on_surface" })) end
  if not plain then for _, n in ipairs(tex("l")) do table.insert(row, n) end end
  local fill = hovered and "primary/0.14" or "primary/0.06"
  if kind == "solid" and string.match(arg or "", "^#%x%x%x%x%x%x$") then fill = arg
  elseif kind == "glow" then fill = string.format("primary/%.2f", 0.08 + 0.14 * (0.5 + 0.5 * math.sin(t0 * 2 * math.pi / 8)) + (hovered and 0.06 or 0)) end
  local W = W0 + (wifi and 20 or 0) + (bat and 38 or 0)
  barWidget.render(ui.row({ width = W, height = H, gap = 2, align = "center", justify = "center", radius = 12,
                            fill = fill,
                            onHover = function(state) hovered = state == "true"; noctalia.setUpdateInterval(moving() and 100 or 30000); render() end,
                            tooltip = "Správca zariadení" .. (wifi and (" · Wi-Fi " .. wifi .. " %") or "")
                                      .. (bat and (" · batéria " .. bat .. " %" .. (charging and " (nabíja sa)" or "")) or "") }, row))
end

-- Wi-Fi a batéria raz za 30 s (pri pohybe 15 s), bez skenovania siete; LATTE_TEST_INDIK="70:45:1" = test bez hardvéru
local function poll()
  local test = noctalia.getenv("LATTE_TEST_INDIK")
  if test and test ~= "" then
    local w, b, c = string.match(test, "^(%d*):(%d*):(%d?)$")
    wifi = tonumber(w or ""); bat = tonumber(b or ""); charging = c == "1"; return
  end
  noctalia.runAsync({ "sh", "-c", 'nmcli -t -f ACTIVE,SIGNAL dev wifi list --rescan no 2>/dev/null | sed -n "s/^yes://p" | head -1; echo @; '
                        .. 'for b in /sys/class/power_supply/BAT*; do [ -r "$b/capacity" ] && { cat "$b/capacity"; cat "$b/status"; break; }; done' }, function(r)
    local w, rest = string.match(r.stdout or "", "^(.-)@(.*)$")
    wifi = tonumber(trim(w or ""))
    local cap, st = string.match(rest or "", "(%d+)%s+(%a+)")
    bat = tonumber(cap or ""); charging = st == "Charging" or st == "Full"
    render()
  end)
end

function update()
  loadPrefs()
  polled = polled + 1
  if polled >= (moving() and 150 or 1) or polled < 0 then polled = 0; poll() end
  gt = gt + 1
  if gt % (moving() and 60 or 1) == 0 then gi = gi % #devGlyphs + 1 end
  if moving() then
    t0 = t0 + 0.1
    noctalia.setUpdateInterval(100)          -- 10 obr/s
  else
    noctalia.setUpdateInterval(30000)        -- statický snímok, prefs raz za 30 s
  end
  render()
end

-- klik = App Manager: rýchle spustenie (vyskakovacie okno); ak je plný App Manager otvorený, iba ho vytiahne dopredu
function onClick() noctalia.runAsync({ "latte-rychle" }) end
