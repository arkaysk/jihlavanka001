--!nonstrict
-- Zvonček oznámení s počtom neprečítaných (medzi hodinami a dátumom). Klik = panel Oznámenia.
-- Neprečítané = prišli po poslednom otvorení zvončeka (história Noctalie). Pri Nerušiť je zvonček prečiarknutý.
local C = require("./common.luau")
local dnd = false

function update()
  noctalia.setUpdateInterval(4000)
  local n = C.unread()
  noctalia.runAsync({ "noctalia", "msg", "notification-dnd-status" }, function(r)
    local o = string.lower(r.stdout or ""); dnd = string.find(o, "on") ~= nil or string.find(o, "true") ~= nil
  end)
  local children = { ui.glyph({ name = dnd and "bell-off" or "bell", size = 16, color = n > 0 and "primary" or "on_surface" }) }
  if n > 0 then
    table.insert(children, ui.row({ fill = "primary", radius = 8, paddingH = 5, minWidth = 16, height = 16, align = "center", justify = "center" },
                                  { ui.label({ text = tostring(math.min(n, 99)), fontSize = 11, fontWeight = "bold", color = "on_primary" }) }))
  end
  barWidget.render(ui.row({ gap = 4, align = "center", paddingH = 4 }, children))
  barWidget.setTooltip({ { "Oznámenia", n > 0 and (n .. " nových") or "žiadne nové" }, { "Klik", "oznámenia a Nerušiť" } })
end

function onClick() C.markSeen(); C.open("oznamenia"); update() end
function onRightClick()
  noctalia.runAsync({ "noctalia", "msg", "notification-dnd-toggle" })
  noctalia.notify("Oznámenia", "Nerušiť prepnuté")
end
