--!nonstrict
-- Režim AI (/ai): cez latte-ai — lokálne (Ollama), domáci server (LM Studio a pod., aj cez SSH)
-- alebo veľké cloudové AI. Voľba je v Nastaveniach › Softvér › AI (~/.config/latteos/ai.toml).
-- Odpoveď sa zobrazí ako výsledky po riadkoch; Enter skopíruje celú odpoveď.
local st = nil        -- { ok, model, target, error }
local busy = false

local function parse(out)
  local s = {}
  for k, v in string.gmatch(out or "", "(%w+)=([^\n]*)") do s[k] = v end
  return s
end

local function check(after)
  noctalia.runAsync({ "latte-ai", "status" }, function(r)
    st = parse(r.stdout)
    if after then after() end
  end)
end

local function settingsItem()
  return { id = "::settings", title = "Nastaviť AI", subtitle = "Nastavenia › Softvér › AI", glyph = "settings" }
end

function onQuery(text)
  local q = text or ""
  if not st then
    launcher.setResults(text, { { id = "", title = "Zisťujem AI…", glyph = "sparkles" } })
    check(function() onQuery(text) end)
    return
  end
  if st.ok ~= "1" then
    launcher.setResults(text, { { id = "", title = "AI nie je dostupné", subtitle = (st.target or "") .. " — " .. (st.error or ""), glyph = "robot-off" }, settingsItem() })
    st = nil          -- nabudúce skúsiť znova
    return
  end
  local who = (st.model ~= "" and st.model) or "model vyberie server"
  if q == "" then
    launcher.setResults(text, { { id = "", title = "Opýtaj sa AI", subtitle = who .. " · " .. (st.target or ""), glyph = "sparkles" }, settingsItem() })
    return
  end
  if busy then return end
  busy = true
  launcher.setResults(text, { { id = "", title = "Premýšľam…", subtitle = who, glyph = "loader" } })
  noctalia.runAsync({ "latte-ai", "ask", q }, function(r)
    busy = false
    if r.exitCode ~= 0 then
      launcher.setResults(text, { { id = "", title = "AI neodpovedalo", subtitle = string.sub(r.stderr or "", 1, 160), glyph = "robot-off" }, settingsItem() })
      return
    end
    local all = r.stdout or ""
    local items = {}
    for line in string.gmatch(all, "[^\n]+") do
      if #items >= 8 then break end
      table.insert(items, { id = all, title = string.sub(line, 1, 140), subtitle = (#items == 0) and ("Enter skopíruje odpoveď · " .. who) or nil, glyph = (#items == 0) and "sparkles" or "point" })
    end
    if #items == 0 then items = { { id = "", title = "(prázdna odpoveď)", glyph = "sparkles" } } end
    launcher.setResults(text, items)
  end)
end

function onActivate(id)
  if id == "::settings" then noctalia.runAsync({ "latte-app", "nastavenia", "ai" }); return end
  if id and id ~= "" then noctalia.copyToClipboard(id, "text/plain") end
end
