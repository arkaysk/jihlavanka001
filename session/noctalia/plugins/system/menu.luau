--!nonstrict
-- LatteOS — systémové menu (panel). Sekcie podľa návrhu plochy: Relácia · Systém · LatteOS · Napájanie.
-- Stav číta zo súborov LatteOS; zmeny robí cez latte-boot, hyprctl eval (Lua modul) a noctalia msg.

local home = noctalia.getenv("HOME") or ""
local cfgHome = noctalia.getenv("XDG_CONFIG_HOME") or (home .. "/.config")
local stateHome = noctalia.getenv("XDG_STATE_HOME") or (home .. "/.local/state")
local tierFile = cfgHome .. "/latteos/tier"
local windowFile = stateHome .. "/latteos/window-mode"

local tiers = { "auto", "plny", "standard", "usporny", "minimalny", "softver" }
local tierNames = { "Automaticky (podľa HW)", "Plný", "Štandard", "Úsporný", "Minimálny", "Softvér (VM)" }
local windowModes = { "paska", "dlazdice", "plavajuce" }
local windowNames = { "Nekonečná páska", "Dlaždice", "Plávajúce okná" }

-- témy (id + názov) z /usr/share/latteos/themes
local themeIds, themeNames = {}, {}
for _, f in ipairs(noctalia.listDir("/usr/share/latteos/themes") or {}) do
  local id = string.match(f, "^([%w_-]+)%.theme$")
  if id then
    local body = noctalia.readFile("/usr/share/latteos/themes/" .. f) or ""
    table.insert(themeIds, id)
    table.insert(themeNames, string.match(body, "\nname = ([^\n]+)") or id)
  end
end

local st = {}
local confirm = nil       -- akcia napájania čakajúca na potvrdenie

local function trim(s) return (string.gsub(s or "", "^%s*(.-)%s*$", "%1")) end
local function indexOf(list, v) for i, x in ipairs(list) do if x == v then return i - 1 end end return 0 end

local function load()
  local toml = noctalia.readFile("/run/latteos/mode.toml") or ""
  st.mode = string.match(toml, 'mode = "(%a+)"') or "safe"
  st.renderer = string.match(toml, 'renderer = "([%w%-]+)"') or "?"
  st.tier = string.match(toml, 'tier = "(%a+)"') or "?"
  st.reason = string.match(toml, 'reason = "([^"]*)"') or ""
  local forced = noctalia.fileExists(tierFile) and trim(noctalia.readFile(tierFile)) or ""
  st.tierChoice = (forced ~= "" and forced) or "auto"
  st.window = noctalia.fileExists(windowFile) and trim(noctalia.readFile(windowFile)) or "paska"
  st.forceSafe = noctalia.fileExists("/var/lib/latteos/force-safe")
  st.user = noctalia.getenv("USER") or "používateľ"
  local th = cfgHome .. "/latteos/theme"
  st.theme = noctalia.fileExists(th) and trim(noctalia.readFile(th)) or "latte"
end

local function section(title, children)
  local rows = { ui.label({ text = title, fontSize = 12, fontWeight = "bold", color = "on_surface_variant" }) }
  for _, c in ipairs(children) do table.insert(rows, c) end
  return ui.column({ gap = 6, align = "stretch" }, rows)
end

local function action(label, hint, handler, danger)
  local row = { ui.button({ text = label, onClick = handler, flexGrow = 1, contentAlign = "start",
                            variant = danger and "destructive" or "ghost" }) }
  if hint then table.insert(row, ui.label({ text = hint, fontSize = 11, color = "on_surface_variant" })) end
  return ui.row({ align = "center", gap = 8 }, row)
end

local function latteRows(safe, modeText)
  local rows = { ui.label({ text = modeText, fontSize = 12, color = safe and "primary" or "on_surface" }) }
  if st.reason ~= "" then
    table.insert(rows, ui.label({ text = st.reason, fontSize = 11, color = "on_surface_variant", maxWidth = 330, maxLines = 3 }))
  end
  table.insert(rows, ui.label({ text = "Téma", fontSize = 12, color = "on_surface_variant" }))
  table.insert(rows, ui.select({ options = themeNames, selectedIndex = indexOf(themeIds, st.theme), onChange = "onTheme" }))
  table.insert(rows, ui.label({ text = "Stupeň výkonu", fontSize = 12, color = "on_surface_variant" }))
  table.insert(rows, ui.select({ options = tierNames, selectedIndex = indexOf(tiers, st.tierChoice), onChange = "onTier", enabled = not safe }))
  table.insert(rows, ui.label({ text = "Režim okien (Super+W)", fontSize = 12, color = "on_surface_variant" }))
  table.insert(rows, ui.select({ options = windowNames, selectedIndex = indexOf(windowModes, st.window), onChange = "onWindow", enabled = not safe }))
  table.insert(rows, ui.row({ gap = 10, align = "center" }, {
    ui.toggle({ checked = st.forceSafe, onChange = "onForceSafe" }),
    ui.label({ text = "Nabudúce naštartovať SAFE", flexGrow = 1 }),
  }))
  if safe then
    table.insert(rows, action("Skúsiť NORMAL znova", "odhlási", function()
      run({ "latte-boot", "reset" })
      run({ "noctalia", "msg", "session", "logout" })
    end))
  end
  return rows
end

local function render()
  local safe = st.mode == "safe"
  local tierShown = (st.tierChoice ~= "auto") and (st.tierChoice .. " (vynútený)") or st.tier
  local modeText = (safe and "SAFE" or "NORMAL") .. " · " .. st.renderer .. " · stupeň " .. tierShown
  local power = {}
  for _, p in ipairs({ { "suspend", "Uspať" }, { "reboot", "Reštartovať" }, { "shutdown", "Vypnúť" } }) do
    local id, label = p[1], p[2]
    table.insert(power, ui.button({
      text = (confirm == id) and ("Naozaj? " .. label) or label,
      variant = (confirm == id) and "destructive" or nil,
      flexGrow = 1,
      onClick = function() onPower(id) end,
    }))
  end

  panel.render(ui.column({ flexGrow = 1, gap = 14, align = "stretch" }, {
    ui.row({ align = "center", justify = "space_between", gap = 8 }, {
      ui.column({ gap = 2 }, {
        ui.label({ text = st.user, fontSize = 17, fontWeight = "bold", color = "on_surface" }),
        ui.label({ text = "Domáci účet", fontSize = 12, color = "on_surface_variant" }),
      }),
      ui.button({ glyph = "close", onClick = function() panel.close() end }),
    }),

    ui.scroll({ flexGrow = 1, gap = 14 }, {
      section("Relácia", {
        action("Zamknúť", "Super+L", function() run({ "noctalia", "msg", "session", "lock" }) end),
        action("Odhlásiť", nil, function() run({ "noctalia", "msg", "session", "logout" }) end),
        ui.button({ text = "Prihlásiť mobilný účet (pripravujeme)", enabled = false, variant = "ghost", contentAlign = "start" }),
      }),

      section("Systém", {
        action("Nastavenia", nil, function() panel.close(); run({ "latte-app", "nastavenia" }) end),
        action("Nastavenia shellu", "lišta, panely", function() run({ "noctalia", "msg", "settings-open" }) end),
        action("Správca procesov", "Ctrl+Shift+Esc", function()
          panel.close()
          noctalia.runInTerminal(noctalia.commandExists("btop") and "btop" or "top")
        end),
      }),

      section("LatteOS", latteRows(safe, modeText)),

      section("Napájanie", { ui.row({ gap = 8 }, power) }),
    }),
  }))
end

function run(argv)
  if not noctalia.runAsync(argv) then
    noctalia.notifyError("LatteOS", "Nepodarilo sa spustiť: " .. table.concat(argv, " "))
  end
end

-- hyprctl eval funguje iba v relácii NORMAL (Hyprland); v SAFE (labwc) sú voľby vypnuté
local function hyprEval(code) run({ "hyprctl", "eval", code }) end

function onTier(index, _text)
  local choice = tiers[(tonumber(index) or 0) + 1]
  if choice == "auto" then
    if noctalia.fileExists(tierFile) then noctalia.removeFile(tierFile) end
  else
    noctalia.mkdirAll(cfgHome .. "/latteos")
    noctalia.writeFile(tierFile, choice .. "\n")
  end
  run({ "hyprctl", "reload" })          -- Lua modul prečíta stupeň znova
  noctalia.notify("Stupeň výkonu", tierNames[(tonumber(index) or 0) + 1])
  load(); render()
end

function onTheme(index, _text)
  local id = themeIds[(tonumber(index) or 0) + 1]
  if id then run({ "latte-theme", "set", id }); st.theme = id; render() end
end

function onWindow(index, _text)
  local m = windowModes[(tonumber(index) or 0) + 1]
  hyprEval('require("latte.windows").apply("' .. m .. '", true)')
  st.window = m
  render()
end

function onForceSafe(value)
  run({ "latte-boot", value == "true" and "force-safe" or "reset" })
  st.forceSafe = value == "true"
  render()
end

function onPower(id)
  if confirm ~= id then
    confirm = id           -- prvé kliknutie iba pripraví, druhé vykoná (nič nevypne priamo)
    render()
    return
  end
  confirm = nil
  panel.close()
  run({ "noctalia", "msg", "session", id })
end

function onOpen(_context)
  confirm = nil
  load()
  render()
end
