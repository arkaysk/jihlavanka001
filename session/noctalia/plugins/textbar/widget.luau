--!nonstrict
-- Text Bar na lište: ikona = režim (pravý klik / koliesko prepína), klik otvorí spúšťač v tom režime.
local modes = {
  { id = "local", glyph = "search",     name = "Lokálne",      prefix = "" },
  { id = "web",   glyph = "world",      name = "Web",          prefix = "/web " },
  { id = "ai",    glyph = "sparkles",   name = "AI",           prefix = "/ai " },
  { id = "cmd",   glyph = "terminal-2", name = "Linux príkaz", prefix = "/cmd " },
}
local modeFile = noctalia.pluginDataDir() .. "/mode"
local index = 1

local saved = noctalia.readFile(modeFile)
if saved then
  for i, m in ipairs(modes) do if string.find(saved, m.id, 1, true) then index = i end end
end

local function show()
  local m = modes[index]
  barWidget.setGlyph(m.glyph)
  barWidget.setText(index == 1 and "Hľadaj, pýtaj sa, spúšťaj…" or (m.name .. "…"))
  barWidget.setTooltip({ { "Režim", m.name }, { "Zmeniť", "pravý klik / koliesko" } })
end

local function setMode(i)
  index = ((i - 1) % #modes) + 1
  noctalia.writeFile(modeFile, modes[index].id)
  show()
end

function update()
  noctalia.setUpdateInterval(60000)
  show()
end

function onClick()
  local p = modes[index].prefix
  if p == "" then
    noctalia.runAsync({ "noctalia", "msg", "panel-toggle", "launcher" })
  else
    noctalia.runAsync({ "noctalia", "msg", "panel-open", "launcher", p })
  end
end

function onRightClick() setMode(index + 1) end

function onScroll(_axis, steps)
  setMode(index + ((steps or 0) > 0 and 1 or -1))
end
