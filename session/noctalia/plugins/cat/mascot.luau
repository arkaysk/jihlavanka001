--!nonstrict
-- Maskot: snímky /usr/share/latteos/noctalia/plugins/cat/mascots/<maskot>-<snímka>.png
-- Pohyb iba keď hrá hudba (4 obr/s, výmena malého obrázka), inak raz za 2 s — lacné aj pri softvérovom kreslení.
-- Ktulu (Cthulhu mačka): občas jej z hrany lišty vyrastú chápadlá. Útek (zadanie 24. 9.): pri nečinnosti
-- (5 min bez pohybu myši a zmeny okna) alebo z nudy (dlho nepohladkaný) maskot odíde z ostrova a vráti sa,
-- keď sa vrátiš ty. Vypnúť: ~/.config/latteos/mascot = ziadny (celý maskot) · mascot-escape = off (iba útek).
local dir = "/usr/share/latteos/noctalia/plugins/cat/mascots/"
local home = noctalia.getenv("HOME") or ""
local cfg = (noctalia.getenv("XDG_CONFIG_HOME") or (home .. "/.config")) .. "/latteos"
local prefFile = cfg .. "/mascot"
local order = { "macka", "mokka", "zrnko", "ktulu" }
local names = { macka = "Latte mačka", mokka = "Mokka", zrnko = "Zrnko", ktulu = "Ktulu" }

local kind = "macka"
local playing, dnd = false, false
local tick, petUntil, blink = 0, 0, false
local lastPoll = -100
-- útek: tu | odchadza | prec | prichadza
local away, step = "tu", 0
local lastActive, lastPet, lastSeen = os.time(), os.time(), ""
local boredUntil = 0
local tentacles = 0          -- zostávajúce snímky chápadiel (Ktulu)

local function trim(s) return (string.gsub(s or "", "^%s*(.-)%s*$", "%1")) end

local function show(frame)
  barWidget.setImage(dir .. kind .. "-" .. frame .. ".png", false, 44, 36)
end

local function poll()
  noctalia.runAsync({ "sh", "-c", "echo \"hudba=$(playerctl status 2>/dev/null | head -1)\"; echo \"dnd=$(noctalia msg notification-dnd-status 2>/dev/null)\"; "
                      .. "echo \"kurzor=$(hyprctl cursorpos 2>/dev/null)|$(hyprctl activewindow -j 2>/dev/null | grep -m1 '\"title\"')\"" }, function(r)
    local out = r.stdout or ""
    playing = string.match(out, "hudba=(%a*)") == "Playing"
    dnd = string.match(out, "dnd=(%a*)") == "on"
    local seen = string.match(out, "kurzor=([^\n]*)") or ""
    if seen ~= lastSeen then lastSeen = seen; lastActive = os.time() end
    if playing then lastActive = os.time() end       -- pri hudbe ťuká, neodchádza
  end)
end

local function escapeOn() return trim(noctalia.readFile(cfg .. "/mascot-escape") or "") ~= "off" end

function update()
  local pref = trim(noctalia.readFile(prefFile) or "")
  if pref == "ziadny" then barWidget.setVisible(false); noctalia.setUpdateInterval(30000); return end
  barWidget.setVisible(true)
  if names[pref] then kind = pref end
  tick = tick + 1
  local now = os.time()
  if now - lastPoll >= 3 then lastPoll = now; poll() end

  -- útek z nečinnosti alebo z nudy, návrat pri aktivite
  local idle = now - lastActive
  if escapeOn() then
    if away == "tu" and (idle > 300 or (now - lastPet > 1800 and math.random(1, 400) == 1)) then
      away, step = "odchadza", 0
      if idle <= 300 then boredUntil = now + math.random(60, 150) end
    elseif away == "prec" and ((boredUntil > 0 and now > boredUntil and idle < 60) or (boredUntil == 0 and idle < 5)) then
      away, step, boredUntil = "prichadza", 3, 0
    end
  elseif away ~= "tu" then
    away = "tu"
  end
  if away == "odchadza" then
    step = step + 1
    if step > 3 then away = "prec"; show("prazdny") else show("odchod-" .. step) end
    noctalia.setUpdateInterval(450)
    barWidget.setTooltip({ { names[kind], "odchádza na prechádzku…" } })
    return
  elseif away == "prichadza" then
    if step < 1 then away = "tu"; lastPet = now; show("sedi") else show("odchod-" .. step); step = step - 1 end
    noctalia.setUpdateInterval(450)
    return
  elseif away == "prec" then
    show("prazdny"); noctalia.setUpdateInterval(3000)
    barWidget.setTooltip({ { names[kind], boredUntil > 0 and "nudil sa, šiel na prechádzku (klik = zavolať)" or "odišiel, kým si preč — vráti sa s tebou" } })
    return
  end

  local h = os.date("*t").hour
  local asleep = (h >= 23 or h < 6 or dnd) and not playing
  local frame
  if now < petUntil then
    frame = "hlad"; noctalia.setUpdateInterval(500)
  elseif playing then
    frame = (tick % 2 == 0) and "lapka-l" or "lapka-p"; noctalia.setUpdateInterval(250)
  elseif asleep then
    frame = "spi"; noctalia.setUpdateInterval(5000)
  elseif tentacles > 0 then
    tentacles = tentacles - 1
    frame = (tentacles % 2 == 0) and "chapadla-1" or "chapadla-2"; noctalia.setUpdateInterval(350)
  elseif blink then
    blink = false; frame = "zmurk"; noctalia.setUpdateInterval(2000)
  else
    frame = "sedi"
    if kind == "ktulu" and math.random(1, 10) == 1 then tentacles = 8; noctalia.setUpdateInterval(350)     -- chápadlá z lišty
    elseif math.random(1, 5) == 1 then blink = true; noctalia.setUpdateInterval(180) else noctalia.setUpdateInterval(2000) end
  end
  show(frame)
  barWidget.setTooltip({ { names[kind], playing and "ťuká do rytmu ♪" or (asleep and "spí… zZ" or (kind == "ktulu" and "Ph'nglui… mňau" or "sedí pri šálke")) },
                         { "Klik", "pohladkať" }, { "Pravý klik", "iný maskot" } })
end

function onClick()
  lastPet = os.time(); lastActive = os.time()
  if away ~= "tu" then away, step, boredUntil = "prichadza", 3, 0; noctalia.setUpdateInterval(100); return end
  petUntil = os.time() + 2
  show("hlad")
  noctalia.setUpdateInterval(500)
end

function onRightClick()
  local i = 1
  for j, k in ipairs(order) do if k == kind then i = j end end
  kind = order[(i % #order) + 1]
  away = "tu"
  noctalia.mkdirAll(cfg)
  noctalia.writeFile(prefFile, kind .. "\n")
  show("sedi")
  noctalia.notify("Maskot", names[kind])
end
