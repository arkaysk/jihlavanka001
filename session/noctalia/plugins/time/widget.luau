--!nonstrict
-- Čas a dátum na lište (napr. „07:33 · št 24. 9.“). Klik otvorí panel Čas · Oznámenia · Kalendár,
-- pravý klik otvorí rovno Kalendár.
local days = { "ne", "po", "ut", "st", "št", "pi", "so" }
local longDays = { "nedeľa", "pondelok", "utorok", "streda", "štvrtok", "piatok", "sobota" }
local months = { "januára", "februára", "marca", "apríla", "mája", "júna", "júla", "augusta", "septembra", "októbra", "novembra", "decembra" }
local tabFile = noctalia.pluginDataDir() .. "/panel-tab"
local home = noctalia.getenv("HOME") or ""
local eventsFile = (noctalia.getenv("XDG_DATA_HOME") or (home .. "/.local/share")) .. "/latteos/events.json"
local reminded = {}      -- pripomenuté udalosti v tomto behu (dátum|čas|názov)

-- pripomenutie z plánovača v čase udalosti (panel Kalendár)
local function remind(t)
  local raw = noctalia.readFile(eventsFile)
  if not raw then return end
  local ok, list = pcall(noctalia.json.decode, raw)
  if not ok or type(list) ~= "table" then return end
  local date, hm = string.format("%04d-%02d-%02d", t.year, t.month, t.day), string.format("%02d:%02d", t.hour, t.min)
  for _, e in ipairs(list) do
    local key = (e.date or "") .. "|" .. (e.time or "") .. "|" .. (e.title or "")
    if e.date == date and e.time == hm and not reminded[key] then
      reminded[key] = true
      noctalia.notify("Kalendár · " .. hm, e.title or "")
    end
  end
end

function update()
  noctalia.setUpdateInterval(15000)
  local t = os.date("*t")
  barWidget.setText(string.format("%02d:%02d  ·  %s %d. %d.", t.hour, t.min, days[t.wday], t.day, t.month))
  barWidget.setTooltip({ { "Dnes", string.format("%s %d. %s %d", longDays[t.wday], t.day, months[t.month], t.year) },
                         { "Klik", "čas, oznámenia, kalendár" } })
  remind(t)
end

local function open(tab)
  if tab then noctalia.writeFile(tabFile, tab) end
  noctalia.togglePanel("latteos/time:panel")
end

function onClick() open(nil) end
function onRightClick() open("kalendar") end
