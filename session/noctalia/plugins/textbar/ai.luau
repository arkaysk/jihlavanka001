--!nonstrict
-- Režim AI (/ai): lokálne AI cez Ollamu (radar: Qwen3-14B-sk na silnom HW, malý model inak).
-- Bez nainštalovaného modelu povie, čo chýba. Odpoveď sa zobrazí ako výsledok (prvé riadky).
local model = nil
local checked = false

local function checkModels(after)
  noctalia.runAsync({ "ollama", "list" }, function(r)
    checked = true
    model = nil
    if r.exitCode == 0 then
      for line in string.gmatch(r.stdout or "", "[^\n]+") do
        local name = string.match(line, "^(%S+)")
        if name and name ~= "NAME" then model = name; break end
      end
    end
    if after then after() end
  end)
end

function onQuery(text)
  local q = text or ""
  if not checked then
    launcher.setResults(text, { { id = "", title = "Zisťujem lokálne AI…", glyph = "sparkles" } })
    checkModels(function() onQuery(text) end)
    return
  end
  if not model then
    launcher.setResults(text, { { id = "", title = "Lokálne AI zatiaľ nie je pripravené",
      subtitle = "Ollama nemá model. Na VM: malý model (ollama pull …), na HW: Qwen3-14B-sk.", glyph = "robot-off" } })
    return
  end
  if q == "" then
    launcher.setResults(text, { { id = "", title = "Opýtaj sa (" .. model .. ")", subtitle = "odpoveď príde sem", glyph = "sparkles" } })
    return
  end
  launcher.setResults(text, { { id = "", title = "Premýšľam… (" .. model .. ")", subtitle = q, glyph = "loader" } })
  noctalia.runAsync({ "ollama", "run", model, q }, function(r)
    local answer = string.gsub(r.stdout or "", "%s+", " ")
    launcher.setResults(text, { { id = r.stdout or "", title = string.sub(answer, 1, 120), subtitle = "Enter skopíruje celú odpoveď", glyph = "sparkles" } })
  end)
end

function onActivate(id)
  if id and id ~= "" then noctalia.copyToClipboard(id, "text/plain") end
end
