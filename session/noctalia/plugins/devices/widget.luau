--!nonstrict
-- Ikona Zariadení na lište: striedavo sieť / zvuk (návrh: „pomaly sa striedajúca ikona“), klik = panel.
local glyphs = { "wifi", "volume", "adjustments" }
local i = 1
function update()
  noctalia.setUpdateInterval(6000)       -- pomalé striedanie; v Nastaveniach neskôr „obmedziť pohyb“
  barWidget.setGlyph(glyphs[i])
  i = i % #glyphs + 1
  barWidget.setTooltip("Zariadenia: sieť, zvuk, jas, herný režim")
end
-- klik = rýchle nastavenia v tvare L vyrastajúce z ostrova (apps/rychle.qml); panel.luau ostáva v plugine ako záloha
function onClick() noctalia.runAsync({ "latte-rychle" }) end
