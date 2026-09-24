-- latte/snap.lua — rozloženia okna ako vo Windows 11 (Win+Z): polovice, štvrtiny, tretiny, stred.
-- Aktívne okno sa uvoľní (pláva) a presunie do zvolenej časti obrazovky bez lišty (reserved area).
-- Volá panel „Rozloženie okna“ (Super+Z): hyprctl eval 'require("latte.snap").apply("lava")'
local S = {}

local GAP = 10
-- časti obrazovky ako zlomky pracovnej plochy: { x, y, šírka, výška }
S.layouts = {
    lava   = { 0, 0, 1/2, 1 },     prava = { 1/2, 0, 1/2, 1 },
    hore   = { 0, 0, 1, 1/2 },     dole  = { 0, 1/2, 1, 1/2 },
    lh     = { 0, 0, 1/2, 1/2 },   ph    = { 1/2, 0, 1/2, 1/2 },
    ld     = { 0, 1/2, 1/2, 1/2 }, pd    = { 1/2, 1/2, 1/2, 1/2 },
    l23    = { 0, 0, 2/3, 1 },     p13   = { 2/3, 0, 1/3, 1 },
    l13    = { 0, 0, 1/3, 1 },     p23   = { 1/3, 0, 2/3, 1 },
    stred  = { 0.15, 0.1, 0.7, 0.8 },
    cela   = { 0, 0, 1, 1 },
}

function S.apply(name)
    local l = S.layouts[name]
    local w = hl.get_active_window()
    if not l or not w then return end
    local m = w.monitor or hl.get_active_monitor()
    if not m then return end
    local scale = m.scale or 1
    local r = m.reserved or { top = 0, right = 0, bottom = 0, left = 0 }
    local ax, ay = m.x + r.left + GAP, m.y + r.top + GAP
    local aw = m.width / scale - r.left - r.right - 2 * GAP
    local ah = m.height / scale - r.top - r.bottom - 2 * GAP
    local x = math.floor(ax + l[1] * aw + (l[1] > 0 and GAP / 2 or 0))
    local y = math.floor(ay + l[2] * ah + (l[2] > 0 and GAP / 2 or 0))
    local ww = math.floor(l[3] * aw - ((l[1] > 0 or l[1] + l[3] < 1) and GAP / 2 or 0))
    local wh = math.floor(l[4] * ah - ((l[2] > 0 or l[2] + l[4] < 1) and GAP / 2 or 0))
    local sel = "address:" .. w.address
    if not w.floating then hl.dispatch(hl.dsp.window.float({ action = "enable", window = sel })) end
    hl.dispatch(hl.dsp.window.resize({ x = ww, y = wh, window = sel }))
    hl.dispatch(hl.dsp.window.move({ x = x, y = y, window = sel }))
end

return S
