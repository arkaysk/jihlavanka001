--!nonstrict
-- Šálka Latte na lište: klik otvorí systémové menu. V režime SAFE je šálka zvýraznená.
local mode = "normal"

function update()
  noctalia.setUpdateInterval(30000)
  local toml = noctalia.readFile("/run/latteos/mode.toml") or ""
  mode = string.match(toml, 'mode = "(%a+)"') or "safe"
  barWidget.setGlyph("coffee")
  barWidget.setText(mode == "safe" and "SAFE" or "")
end

function onClick()
  noctalia.togglePanel("latteos/system:menu")
end
