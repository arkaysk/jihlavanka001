--!nonstrict
-- Maskot: snímky /usr/share/latteos/noctalia/plugins/cat/mascots/<maskot>-<snímka>.png
-- Pohyb iba keď hrá hudba (4 obr/s, výmena malého obrázka), inak raz za 2 s — lacné aj pri softvérovom kreslení.
local dir = "/usr/share/latteos/noctalia/plugins/cat/mascots/"
local home = noctalia.getenv("HOME") or ""
local prefFile = (noctalia.getenv("XDG_CONFIG_HOME") or (home .. "/.config")) .. "/latteos/mascot"
local order = { "macka", "mokka", "zrnko" }
local names = { macka = "Latte mačka", mokka = "Mokka", zrnko = "Zrnko" }

local kind = "macka"
local playing, dnd = false, false
local tick, petUntil, blink = 0, 0, false
local lastPoll = -100

local function trim(s) return (string.gsub(s or "", "^%s*(.-)%s*$", "%1")) end

local function show(frame)
  barWidget.setImage(dir .. kind .. "-" .. frame .. ".png", false, 44, 36)
end

local function poll()
  noctalia.runAsync({ "sh", "-c", "echo \"hudba=$(playerctl status 2>/dev/null | head -1)\"; echo \"dnd=$(noctalia msg notification-dnd-status 2>/dev/null)\"" }, function(r)
    local out = r.stdout or ""
    playing = string.match(out, "hudba=(%a*)") == "Playing"
    dnd = string.match(out, "dnd=(%a*)") == "on"
  end)
end

function update()
  local pref = trim(noctalia.readFile(prefFile) or "")
  if pref == "ziadny" then barWidget.setVisible(false); noctalia.setUpdateInterval(30000); return end
  barWidget.setVisible(true)
  if names[pref] then kind = pref end
  tick = tick + 1
  local now = os.time()
  if now - lastPoll >= 3 then lastPoll = now; poll() end

  local h = os.date("*t").hour
  local asleep = (h >= 23 or h < 6 or dnd) and not playing
  local frame
  if now < petUntil then
    frame = "hlad"; noctalia.setUpdateInterval(500)
  elseif playing then
    frame = (tick % 2 == 0) and "lapka-l" or "lapka-p"; noctalia.setUpdateInterval(250)
  elseif asleep then
    frame = "spi"; noctalia.setUpdateInterval(5000)
  elseif blink then
    blink = false; frame = "zmurk"; noctalia.setUpdateInterval(2000)
  else
    frame = "sedi"
    if math.random(1, 5) == 1 then blink = true; noctalia.setUpdateInterval(180) else noctalia.setUpdateInterval(2000) end
  end
  show(frame)
  barWidget.setTooltip({ { names[kind], playing and "ťuká do rytmu ♪" or (asleep and "spí… zZ" or "sedí pri šálke") },
                         { "Klik", "pohladkať" }, { "Pravý klik", "iný maskot" } })
end

function onClick()
  petUntil = os.time() + 2
  show("hlad")
  noctalia.setUpdateInterval(500)
end

function onRightClick()
  local i = 1
  for j, k in ipairs(order) do if k == kind then i = j end end
  kind = order[(i % #order) + 1]
  noctalia.mkdirAll((noctalia.getenv("XDG_CONFIG_HOME") or (home .. "/.config")) .. "/latteos")
  noctalia.writeFile(prefFile, kind .. "\n")
  show("sedi")
  noctalia.notify("Maskot", names[kind])
end
