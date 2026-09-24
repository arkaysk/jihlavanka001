--!nonstrict
-- Panel času: Čas · Oznámenia · Kalendár.
--   Čas        veľké hodiny, dátum, týždeň; ďalšie časové pásma (Nastavenia › Systém › Dátum a čas)
--   Oznámenia  Nerušiť, história oznámení Noctalie, oznámenia z mobilu (KDE Connect)
--   Kalendár   mesiac, vlastný plánovač udalostí (~/.local/share/latteos/events.json, pripomenutie
--              v čase udalosti robí widget) a napojenie na kalendáre a to-do cez kalendár Noctalie
local home = noctalia.getenv("HOME") or ""
local cfgHome = noctalia.getenv("XDG_CONFIG_HOME") or (home .. "/.config")
local dataHome = noctalia.getenv("XDG_DATA_HOME") or (home .. "/.local/share")
local eventsFile = dataHome .. "/latteos/events.json"
local tabFile = noctalia.pluginDataDir() .. "/panel-tab"

local longDays = { "nedeľa", "pondelok", "utorok", "streda", "štvrtok", "piatok", "sobota" }
local months = { "január", "február", "marec", "apríl", "máj", "jún", "júl", "august", "september", "október", "november", "december" }
local monthsGen = { "januára", "februára", "marca", "apríla", "mája", "júna", "júla", "augusta", "septembra", "októbra", "novembra", "decembra" }
local zoneNames = { ["Europe/London"] = "Londýn", ["America/New_York"] = "New York", ["America/Los_Angeles"] = "Los Angeles",
                    ["Asia/Tokyo"] = "Tokio", ["Asia/Shanghai"] = "Peking", ["Asia/Kolkata"] = "Dillí", ["Australia/Sydney"] = "Sydney",
                    ["Europe/Moscow"] = "Moskva", ["UTC"] = "UTC" }

local st = { tab = "cas", zones = {}, dnd = false, phone = nil, events = {}, ym = nil, sel = nil, newTitle = "", newTime = "" }

local function trim(s) return (string.gsub(s or "", "^%s*(.-)%s*$", "%1")) end
local function iso(y, m, d) return string.format("%04d-%02d-%02d", y, m, d) end
local function today() local t = os.date("*t"); return t.year, t.month, t.day end
-- ISO týždeň (Luau os.date nepozná %V)
local function weeksIn(y)
  local function p(x) return (x + x // 4 - x // 100 + x // 400) % 7 end
  return (p(y) == 4 or p(y - 1) == 3) and 53 or 52
end
local function isoWeek(t)
  local wd = (t.wday + 5) % 7 + 1                  -- pondelok = 1 … nedeľa = 7
  local w = (t.yday - wd + 10) // 7
  if w < 1 then return weeksIn(t.year - 1) end
  if w > weeksIn(t.year) then return 1 end
  return w
end
local function daysIn(y, m) return os.date("*t", os.time({ year = y, month = m + 1, day = 0, hour = 12 })).day end

local function loadEvents()
  local raw = noctalia.readFile(eventsFile)
  local ok, list = pcall(function() return raw and noctalia.json.decode(raw) or {} end)
  st.events = (ok and type(list) == "table") and list or {}
end
local function saveEvents()
  table.sort(st.events, function(a, b) return (a.date .. (a.time or "")) < (b.date .. (b.time or "")) end)
  noctalia.mkdirAll(dataHome .. "/latteos")
  noctalia.writeFile(eventsFile, noctalia.json.encode(st.events))
end
local function eventsOn(date)
  local out = {}
  for i, e in ipairs(st.events) do if e.date == date then table.insert(out, { i = i, e = e }) end end
  return out
end

-- počasie (Open-Meteo, bez účtu): poloha z Nastavení (settings.toml [location]), mesto z greeter.conf
local weather, weatherAt = nil, 0
local function wmo(c)
  c = tonumber(c) or 0
  if c == 0 then return "Jasno", "sun" elseif c <= 2 then return "Polojasno", "cloud" elseif c == 3 then return "Zamračené", "cloud"
  elseif c <= 48 then return "Hmla", "cloud" elseif c <= 67 then return "Dážď", "cloud-rain" elseif c <= 77 then return "Sneh", "snowflake"
  elseif c <= 82 then return "Prehánky", "cloud-rain" elseif c <= 86 then return "Snehové prehánky", "snowflake" end
  return "Búrka", "cloud-storm"
end
local function loadWeather()
  if os.time() - weatherAt < 900 and weather then return end
  local st = noctalia.readFile((noctalia.getenv("XDG_STATE_HOME") or (home .. "/.local/state")) .. "/noctalia/settings.toml") or ""
  local loc = string.match(st, "%[location%]([^%[]*)") or ""
  local lat = string.match(loc, "latitude%s*=%s*([%d%.%-]+)") or "48.74"
  local lon = string.match(loc, "longitude%s*=%s*([%d%.%-]+)") or "19.15"
  local place = string.match(noctalia.readFile("/var/lib/latteos/greeter/greeter.conf") or "", 'place = "([^"]*)"') or ""
  local url = "https://api.open-meteo.com/v1/forecast?latitude=" .. lat .. "&longitude=" .. lon
    .. "&current=temperature_2m,weather_code,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min,weather_code&timezone=auto&forecast_days=4"
  noctalia.runAsync({ "curl", "-s", "-m", "6", url }, function(r)
    local ok, d = pcall(noctalia.json.decode, r.stdout or "")
    if ok and type(d) == "table" and d.current then weather = d; weather.place = place; weatherAt = os.time(); render() end
  end, 8000)
end

local function refresh()
  -- ďalšie časové pásma
  local conf = noctalia.readFile(cfgHome .. "/latteos/clock.conf") or ""
  local zs = string.match(conf, 'zones = "([^"]*)"') or ""
  local list = {}
  for z in string.gmatch(zs, "[^,]+") do table.insert(list, z) end
  if #list > 0 then
    local script = "for z in \"$@\"; do printf '%s|' \"$z\"; TZ=\"$z\" date '+%H:%M|%Y-%m-%d'; done"
    local argv = { "sh", "-c", script, "sh" }
    for _, z in ipairs(list) do table.insert(argv, z) end
    noctalia.runAsync(argv, function(r)
      st.zones = {}
      for z, hm, d in string.gmatch(r.stdout or "", "([^|\n]+)|([^|\n]+)|([^|\n]+)") do table.insert(st.zones, { z = z, hm = hm, d = d }) end
      render()
    end)
  else
    st.zones = {}
  end
  noctalia.runAsync({ "noctalia", "msg", "notification-dnd-status" }, function(r)
    local o = string.lower(r.stdout or ""); st.dnd = string.find(o, "on") ~= nil or string.find(o, "true") ~= nil; render()
  end)
  if noctalia.commandExists("kdeconnect-cli") then
    noctalia.runAsync({ "kdeconnect-cli", "-a", "--name-only" }, function(r) st.phone = trim(r.stdout); render() end)
  else
    st.phone = nil
  end
  loadEvents()
end

local function tabButton(id, label, glyph)
  return ui.button({ text = label, glyph = glyph, selected = st.tab == id, variant = st.tab == id and nil or "ghost", flexGrow = 1,
                     onClick = function() st.tab = id; noctalia.writeFile(tabFile, id); render() end })
end
local function heading(t) return ui.label({ text = t, fontSize = 12, fontWeight = "bold", color = "on_surface_variant" }) end
local function note(t) return ui.label({ text = t, fontSize = 12, color = "on_surface_variant", maxWidth = 370, maxLines = 4 }) end
local function card(children) return ui.column({ fill = "surface_variant", radius = 14, padding = 12, gap = 6, align = "stretch" }, children) end

-- ── Čas ──────────────────────────────────────────────────────────────────────
local function tabTime()
  local t = os.date("*t")
  local body = {
    ui.label({ text = string.format("%02d:%02d", t.hour, t.min), fontSize = 54, fontWeight = "bold", color = "on_surface" }),
    ui.label({ text = string.format("%s %d. %s %d", longDays[t.wday], t.day, monthsGen[t.month], t.year), fontSize = 15, color = "on_surface" }),
    ui.label({ text = "týždeň " .. isoWeek(t) .. " · " .. t.yday .. ". deň v roku", fontSize = 12, color = "on_surface_variant" }),
    ui.separator({}),
    heading("ČASOVÉ PÁSMA"),
  }
  local todayIso = iso(t.year, t.month, t.day)
  if #st.zones == 0 then
    table.insert(body, note("Pridaj mestá v Nastaveniach (Systém › Dátum, čas a poloha) a uvidíš tu ich čas."))
  end
  for _, z in ipairs(st.zones) do
    local diff = (z.d > todayIso) and "zajtra" or ((z.d < todayIso) and "včera" or "dnes")
    table.insert(body, ui.row({ align = "center", gap = 8 }, {
      ui.label({ text = zoneNames[z.z] or z.z, fontSize = 14, flexGrow = 1 }),
      ui.label({ text = diff, fontSize = 11, color = "on_surface_variant" }),
      ui.label({ text = z.hm, fontSize = 18, fontWeight = "bold" }),
    }))
  end
  -- počasie
  table.insert(body, ui.separator({}))
  table.insert(body, heading("POČASIE" .. ((weather and weather.place ~= "") and (" · " .. weather.place) or "")))
  if weather and weather.current then
    local txt, g = wmo(weather.current.weather_code)
    table.insert(body, ui.row({ gap = 12, align = "center" }, {
      ui.glyph({ name = g, size = 34, color = "primary" }),
      ui.label({ text = string.format("%d °C", math.floor(weather.current.temperature_2m + 0.5)), fontSize = 26, fontWeight = "bold" }),
      ui.label({ text = txt .. " · vietor " .. math.floor(weather.current.wind_speed_10m + 0.5) .. " km/h", fontSize = 12, color = "on_surface_variant", flexGrow = 1 }),
    }))
    local days = { "ne", "po", "ut", "st", "št", "pi", "so" }
    local row = {}
    for i = 2, math.min(4, #(weather.daily.time or {})) do
      local y, mo, dd = string.match(weather.daily.time[i], "(%d+)-(%d+)-(%d+)")
      local wd = os.date("*t", os.time({ year = tonumber(y), month = tonumber(mo), day = tonumber(dd), hour = 12 })).wday
      local _, dg = wmo(weather.daily.weather_code[i])
      table.insert(row, ui.column({ fill = "surface_variant", radius = 12, padding = 10, gap = 2, flexGrow = 1, align = "center" }, {
        ui.label({ text = days[wd], fontSize = 12, color = "on_surface_variant" }),
        ui.glyph({ name = dg, size = 20, color = "primary" }),
        ui.label({ text = math.floor(weather.daily.temperature_2m_min[i] + 0.5) .. "° / " .. math.floor(weather.daily.temperature_2m_max[i] + 0.5) .. "°", fontSize = 12 }),
      }))
    end
    table.insert(body, ui.row({ gap = 8 }, row))
  else
    table.insert(body, note("Počasie sa načítava… (potrebuje internet)"))
  end
  table.insert(body, ui.button({ text = "Upraviť pásma a polohu", glyph = "settings", variant = "ghost", contentAlign = "start",
                                 onClick = function() panel.close(); noctalia.runAsync({ "latte-app", "nastavenia", "cas" }) end }))
  return body
end

-- ── Oznámenia ────────────────────────────────────────────────────────────────
local function tabNotifications()
  local body = {
    ui.row({ align = "center", gap = 10 }, {
      ui.toggle({ checked = st.dnd, onChange = "onDnd" }),
      ui.label({ text = "Nerušiť", fontSize = 14, flexGrow = 1 }),
    }),
    ui.button({ text = "História oznámení", glyph = "bell", contentAlign = "start",
                onClick = function() panel.close(); noctalia.runAsync({ "noctalia", "msg", "panel-open", "control-center", "notifications" }) end }),
    ui.button({ text = "Vymazať históriu", glyph = "trash", variant = "ghost", contentAlign = "start",
                onClick = function() noctalia.runAsync({ "noctalia", "msg", "notification-clear-history" }); noctalia.notify("Oznámenia", "História vymazaná") end }),
    ui.separator({}),
    heading("OZNÁMENIA Z MOBILU"),
  }
  if st.phone == nil then
    table.insert(body, card({
      ui.label({ text = "KDE Connect nie je nainštalovaný", fontSize = 13, fontWeight = "bold" }),
      note("Android: aplikácia KDE Connect → oznámenia, SMS, schránka a súbory na PC. iPhone: KDE Connect pre iOS (Apple obmedzuje oznámenia)."),
      ui.button({ text = "Nainštalovať (dnf install kde-connect)", glyph = "download", variant = "ghost", contentAlign = "start",
                  onClick = function() panel.close(); noctalia.runAsync({ "latte-app", "instalator", "--nazov=KDE_Connect", "install", "kde-connect" }) end }),
    }))
  elseif st.phone == "" then
    table.insert(body, card({ ui.label({ text = "Žiadny spárovaný mobil", fontSize = 13, fontWeight = "bold" }),
                              note("Otvor KDE Connect v mobile a spáruj ho s týmto PC (rovnaká sieť).") }))
  else
    table.insert(body, card({ ui.label({ text = "Pripojené: " .. st.phone, fontSize = 13, fontWeight = "bold" }),
                              note("Oznámenia z mobilu prichádzajú ako bežné oznámenia LatteOS.") }))
  end
  return body
end

-- ── Kalendár ─────────────────────────────────────────────────────────────────
local function tabCalendar()
  local ty, tm, td = today()
  local y, m = st.ym and st.ym[1] or ty, st.ym and st.ym[2] or tm
  st.sel = st.sel or iso(ty, tm, td)
  local first = os.date("*t", os.time({ year = y, month = m, day = 1, hour = 12 }))
  local lead = (first.wday + 5) % 7          -- pondelok = prvý deň týždňa
  local n = daysIn(y, m)

  local body = {
    ui.row({ align = "center", gap = 4 }, {
      ui.button({ glyph = "chevron-left", variant = "ghost", onClick = function() m = m - 1; if m < 1 then m = 12; y = y - 1 end; st.ym = { y, m }; render() end }),
      ui.label({ text = months[m] .. " " .. y, fontSize = 16, fontWeight = "bold", flexGrow = 1 }),
      ui.button({ text = "Dnes", variant = "ghost", onClick = function() st.ym = nil; st.sel = iso(ty, tm, td); render() end }),
      ui.button({ glyph = "chevron-right", variant = "ghost", onClick = function() m = m + 1; if m > 12 then m = 1; y = y + 1 end; st.ym = { y, m }; render() end }),
    }),
  }
  local head = {}
  for _, d in ipairs({ "po", "ut", "st", "št", "pi", "so", "ne" }) do
    table.insert(head, ui.button({ text = d, width = 46, controlSize = "sm", variant = "ghost", enabled = false }))
  end
  table.insert(body, ui.row({ gap = 4 }, head))
  local day = 1 - lead
  for _ = 1, 6 do
    if day > n then break end
    local row = {}
    for _ = 1, 7 do
      if day >= 1 and day <= n then
        local date = iso(y, m, day)
        local isToday = (y == ty and m == tm and day == td)
        local busy = #eventsOn(date) > 0          -- deň s udalosťou: iný štýl tlačidla (nie iba farba: aj výplň)
        table.insert(row, ui.button({ text = tostring(day), width = 46, controlSize = "sm",
                                      tooltip = busy and (#eventsOn(date) .. " udalosť(i)") or nil,
                                      variant = (st.sel == date) and "primary" or (isToday and "outline" or (busy and "secondary" or "ghost")),
                                      onClick = function() st.sel = date; render() end }))
      else
        table.insert(row, ui.spacer({ width = 46 }))
      end
      day = day + 1
    end
    table.insert(body, ui.row({ gap = 4 }, row))
  end

  -- plánovač vybraného dňa
  local sy, sm, sd = string.match(st.sel, "(%d+)-(%d+)-(%d+)")
  table.insert(body, ui.separator({}))
  table.insert(body, heading(string.upper(string.format("%d. %s", tonumber(sd), monthsGen[tonumber(sm)]))))
  local list = eventsOn(st.sel)
  if #list == 0 then table.insert(body, note("Žiadne udalosti.")) end
  for _, it in ipairs(list) do
    table.insert(body, ui.row({ align = "center", gap = 8 }, {
      ui.label({ text = (it.e.time and it.e.time ~= "") and it.e.time or "celý deň", fontSize = 12, color = "primary", width = 64 }),
      ui.label({ text = it.e.title, fontSize = 13, flexGrow = 1, maxWidth = 250, maxLines = 2 }),
      ui.button({ glyph = "x", variant = "ghost", controlSize = "sm", tooltip = "Odstrániť",
                  onClick = function() table.remove(st.events, it.i); saveEvents(); render() end }),
    }))
  end
  table.insert(body, ui.row({ gap = 6, align = "center" }, {
    ui.input({ placeholder = "14:00", width = 70, onChange = "onNewTime", onSubmit = "onAdd" }),
    ui.input({ placeholder = "Nová udalosť… (Enter pridá)", flexGrow = 1, onChange = "onNewTitle", onSubmit = "onAdd" }),
  }))

  table.insert(body, ui.separator({}))
  table.insert(body, heading("KALENDÁRE A ÚLOHY"))
  table.insert(body, note("Google Kalendár, Apple iCloud, Nextcloud/CalDAV a odkazy ICS (Outlook, Proton, Todoist, TickTick, Microsoft To Do) sa pripájajú v kalendári Noctalie; ich udalosti uvidíš tam."))
  table.insert(body, ui.button({ text = "Otvoriť kalendár a účty", glyph = "calendar", contentAlign = "start",
                                 onClick = function() panel.close(); noctalia.runAsync({ "noctalia", "msg", "panel-open", "control-center", "calendar" }) end }))
  return body
end

function render()
  local content = st.tab == "oznamenia" and tabNotifications() or (st.tab == "kalendar" and tabCalendar() or tabTime())
  panel.render(ui.column({ flexGrow = 1, gap = 12, align = "stretch" }, {
    ui.row({ gap = 6, align = "center" }, {
      tabButton("cas", "Čas", "clock"),
      tabButton("oznamenia", "Oznámenia", "bell"),
      tabButton("kalendar", "Kalendár", "calendar"),
      ui.button({ glyph = "close", variant = "ghost", onClick = function() panel.close() end }),
    }),
    ui.scroll({ flexGrow = 1, gap = 10, align = "stretch" }, content),
  }))
end

function onDnd(value)
  st.dnd = value == "true"
  noctalia.runAsync({ "noctalia", "msg", "notification-dnd-set", st.dnd and "on" or "off" }, function() refresh() end)
end
function onNewTitle(t) st.newTitle = t or "" end
function onNewTime(t) st.newTime = t or "" end
function onAdd(_t)
  local title = trim(st.newTitle)
  if title == "" then return end
  local time = trim(st.newTime)
  if time ~= "" and not string.match(time, "^%d%d?:%d%d$") then noctalia.notifyError("Kalendár", "Čas v tvare 14:00"); return end
  if string.match(time, "^%d:%d%d$") then time = "0" .. time end
  table.insert(st.events, { date = st.sel, time = time, title = title })
  saveEvents()
  st.newTitle = ""
  render()
end

function onOpen(_ctx)
  loadWeather()
  local saved = trim(noctalia.readFile(tabFile) or "")
  if saved == "cas" or saved == "oznamenia" or saved == "kalendar" then st.tab = saved end
  loadEvents()
  render()
  refresh()
end
