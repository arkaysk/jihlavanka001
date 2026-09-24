--!nonstrict
-- Kapsa: navrchu posledná odložená vec (veľká karta, pri obrázku náhľad), pod ňou sloty histórie.
-- Klik na slot ju vytiahne navrch (skopíruje späť), pravý klik ju vyhodí. „Vysypať“ vymaže históriu.
local C = require("./common.luau")
local items = {}
local preview = noctalia.pluginDataDir() .. "/navrchu.png"
local vecFile = (noctalia.getenv("XDG_STATE_HOME") or ((noctalia.getenv("HOME") or "") .. "/.local/state")) .. "/latteos/kapsa-vec"

local function load()
  noctalia.runAsync({ "sh", "-c", "cliphist list 2>/dev/null | head -24" }, function(r)
    items = C.parse(r.stdout)
    local top = items[1]
    if top and top.image then
      noctalia.runAsync({ "sh", "-c", "cliphist decode \"$1\" > \"$2\"", "sh", top.id, preview }, function() render() end)
    end
    render()
  end)
end

local function pick(it)
  noctalia.runAsync({ "sh", "-c", "cliphist decode \"$1\" | wl-copy", "sh", it.id }, function() load() end)
end
local function drop(it)
  noctalia.runAsync({ "sh", "-c", "cliphist list | awk -F '\t' -v id=\"$1\" '$1 == id' | cliphist delete", "sh", it.id }, function() load() end)
end

function render()
  local top = items[1]
  local body = {}
  -- vec vo výreze (súbor pretiahnutý na Kapsu na lište)
  local vec = string.match(noctalia.readFile(vecFile) or "", "^%s*(.-)%s*$") or ""
  if vec ~= "" then
    table.insert(body, ui.row({ fill = "surface_variant", radius = 14, padding = 10, gap = 8, align = "center" }, {
      ui.glyph({ name = "file", size = 18, color = "primary" }),
      ui.column({ flexGrow = 1, gap = 2 }, {
        ui.label({ text = "VO VÝREZE", fontSize = 10, fontWeight = "bold", color = "on_surface_variant" }),
        ui.label({ text = string.match(vec, "[^/]+$") or vec, fontSize = 13, maxWidth = 280, maxLines = 1 }),
      }),
      ui.button({ glyph = "external-link", variant = "ghost", tooltip = "Otvoriť", onClick = function() noctalia.runAsync({ "xdg-open", vec }) end }),
      ui.button({ glyph = "x", variant = "ghost", tooltip = "Vybrať z Kapsy", onClick = function() noctalia.removeFile(vecFile); render() end }),
    }))
  else
    table.insert(body, ui.label({ text = "Výrez je prázdny: pretiahni súbor na jamku Kapsy na lište.", fontSize = 12, color = "on_surface_variant", maxWidth = 400, maxLines = 2 }))
  end
  if top then
    local card = { ui.label({ text = "NAVRCHU", fontSize = 11, fontWeight = "bold", color = "on_primary" }) }
    if top.image then
      table.insert(card, ui.image({ path = preview, width = 380, height = 180, fit = "contain" }))
    end
    table.insert(card, ui.label({ text = C.label(top, 300), fontSize = 14, color = "on_primary", maxWidth = 390, maxLines = 5 }))
    table.insert(body, ui.column({ fill = "primary", radius = 16, padding = 14, gap = 6, align = "stretch" }, card))
  else
    table.insert(body, ui.label({ text = "Kapsa je prázdna. Skopíruj niečo (Ctrl+C) a odloží sa sem.", fontSize = 13, color = "on_surface_variant", maxWidth = 400, maxLines = 3 }))
  end
  if #items > 1 then
    table.insert(body, ui.label({ text = "V KAPSE", fontSize = 12, fontWeight = "bold", color = "on_surface_variant" }))
    local row = {}
    for i = 2, #items do
      local it = items[i]
      table.insert(row, ui.column({ fill = "surface_variant", radius = 12, padding = 10, gap = 4, width = 196, height = 74,
                                    onClick = function() pick(it) end, tooltip = "klik: navrch · pravý klik na × : vyhodiť" }, {
        ui.row({ gap = 6, align = "center" }, {
          ui.glyph({ name = it.image and "photo" or "file-text", size = 14, color = "primary" }),
          ui.label({ text = it.image and "obrázok" or "text", fontSize = 10, color = "on_surface_variant", flexGrow = 1 }),
          ui.button({ glyph = "x", variant = "ghost", controlSize = "sm", onClick = function() drop(it) end }),
        }),
        ui.label({ text = C.label(it, 60), fontSize = 12, maxWidth = 176, maxLines = 2 }),
      }))
      if #row == 2 then table.insert(body, ui.row({ gap = 8 }, row)); row = {} end
    end
    if #row > 0 then table.insert(body, ui.row({ gap = 8 }, row)) end
  end
  panel.render(ui.column({ flexGrow = 1, gap = 12, align = "stretch" }, {
    ui.row({ gap = 8, align = "center" }, {
      ui.glyph({ name = "basket", size = 20, color = "primary" }),
      ui.label({ text = "Kapsa", fontSize = 17, fontWeight = "bold", flexGrow = 1 }),
      ui.button({ text = "Vysypať", glyph = "trash", variant = "ghost", onClick = function()
        noctalia.runAsync({ "cliphist", "wipe" }, function() load() end) end }),
      ui.button({ glyph = "close", variant = "ghost", onClick = function() panel.close() end }),
    }),
    ui.scroll({ flexGrow = 1, gap = 10, align = "stretch" }, body),
  }))
end

function onOpen(_ctx) render(); load() end
