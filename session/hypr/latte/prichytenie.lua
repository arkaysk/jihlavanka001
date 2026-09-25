-- latte/prichytenie.lua — prichytenie okna ťahaním k okraju ako vo Windows 7–11 (alfatest 1). Platí v režime
-- plávajúcich okien; v páske a dlaždiciach okná rozkladá Hyprland (ako Linux), preto sa tu nič nedeje.
--   kurzor na hornom okraji            → celá obrazovka (maximalizovať)
--   kurzor na ľavom / pravom okraji    → polovica
--   … a pri hornom / dolnom rohu       → štvrtina
--   odtiahnutie prichyteného okna      → vráti pôvodnú veľkosť pod kurzor
-- Počas ťahania ukáže priehľadný náhľad cieľa (nahlad.qml, IPC „prichytenie“). Udalosti ťahania posiela plugin
-- latte-okna (/usr/lib64/latteos/latte-okna.so), Hyprland 0.56.2 ich sám nemá. Vypnutie: ~/.config/latteos/bez-prichytenia
local P = {}
local S = require("latte.snap")

P.plugin = "/usr/lib64/latteos/latte-okna.so"
local EDGE = 8           -- px od okraja monitora, kde sa prichytenie spustí (Windows: kurzor na okraji)
local CORNER = 0.18      -- podiel výšky / šírky pri rohu = štvrtina

local cfgdir = (os.getenv("XDG_CONFIG_HOME") or ((os.getenv("HOME") or "") .. "/.config")) .. "/latteos"
local function file_exists(p) local f = io.open(p, "r"); if f then f:close(); return true end; return false end
local function floating_mode() local ok, W = pcall(require, "latte.windows"); return ok and W.current == "plavajuce" end

--- zóna pod kurzorom: meno rozloženia zo snap.lua, "max" alebo nil
function P.zone(m, x, y)
    local scale = m.scale or 1
    local mx, my, mw, mh = m.x, m.y, m.width / scale, m.height / scale
    local left, right, top = x <= mx + EDGE, x >= mx + mw - 1 - EDGE, y <= my + EDGE
    local upper, lower = y < my + mh * CORNER, y > my + mh * (1 - CORNER)
    if left then return upper and "lh" or lower and "ld" or "lava" end
    if right then return upper and "ph" or lower and "pd" or "prava" end
    if top then
        if x < mx + mw * CORNER / 2 then return "lh" end
        if x > mx + mw * (1 - CORNER / 2) then return "ph" end
        return "max"
    end
    return nil
end

local function preview(r)
    local call = r and string.format("ukaz %d %d %d %d", r.x, r.y, r.w, r.h) or "skry"
    hl.exec_cmd("latte-prichytenie " .. call)
end

local drag = nil         -- { address, zone, restored }

local function on_motion(w, x, y)
    if not w or not floating_mode() or file_exists(cfgdir .. "/bez-prichytenia") then return end
    if not drag or drag.address ~= w.address then
        drag = { address = w.address, zone = nil }
        -- odtiahnutie prichyteného okna: vráti pôvodnú veľkosť, kurzor ostane v titulku (ako Windows)
        if S.is_snapped(w) then S.restore(w, x, y) end
    end
    local m = hl.get_monitor_at(x, y) or w.monitor
    if not m then return end
    local z = P.zone(m, x, y)
    if z == drag.zone then return end
    drag.zone = z
    if not z then preview(nil); return end
    local r = S.rect(z == "max" and "cela" or z, m)
    preview(r)
end

local function on_end(w, x, y)
    local d = drag
    drag = nil
    if not d or not d.zone then return end
    preview(nil)
    if not w then return end
    local m = hl.get_monitor_at(x, y) or w.monitor
    if d.zone == "max" then
        S.apply("cela", w, m)                  -- zapamätá pôvodnú veľkosť
        hl.dispatch(hl.dsp.window.fullscreen({ mode = "maximized", action = "set", window = "address:" .. w.address }))
    else
        S.apply(d.zone, w, m)
    end
end

-- pre testy (hyprctl eval): rovnaká cesta ako udalosti z pluginu
P.motion, P.finish = on_motion, on_end

function P.setup()
    if not file_exists(P.plugin) then return false end
    local ok = pcall(hl.plugin.load, P.plugin)
    if not ok then return false end
    -- udalosti existujú, iba ak sa plugin naozaj načítal (pri --verify-config nie; hl.on by zapísal chybu konfigurácie)
    local loaded = false
    for _, pl in ipairs(hl.get_loaded_plugins() or {}) do
        if pl.name == "latte-okna" then loaded = true end
    end
    if not loaded then return false end
    hl.on("latte.drag_motion", on_motion)
    hl.on("latte.drag_end", on_end)
    return true
end

return P
