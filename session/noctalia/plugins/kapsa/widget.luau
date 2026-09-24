--!nonstrict
-- Kapsa na lište: ikona a jediná odložená vec navrchu (skrátená). Zmena schránky príde cez wl-paste --watch.
local C = require("./common.luau")
local top = nil

local function refresh()
  noctalia.runAsync({ "sh", "-c", "cliphist list 2>/dev/null | head -1" }, function(r)
    local items = C.parse(r.stdout)
    top = items[1]
    barWidget.setGlyph(top and "basket-filled" or "basket")
    barWidget.setText(top and C.label(top, 14) or "")
    barWidget.setTooltip({ { "Kapsa", top and C.label(top, 60) or "prázdna" }, { "Klik", "história schránky" } })
  end)
end

local watching = false
function update()
  noctalia.setUpdateInterval(60000)
  if not watching then
    watching = true
    -- každá zmena schránky vypíše riadok → obnoviť (cliphist store beží zvlášť v relácii)
    noctalia.runStream("wl-paste --watch echo zmena", function(_line) refresh() end)
  end
  refresh()
end

function onClick() noctalia.togglePanel("latteos/kapsa:panel") end
