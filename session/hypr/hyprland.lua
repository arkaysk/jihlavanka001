-- LatteOS — Hyprland, relácia NORMAL (/usr/share/latteos/hypr/hyprland.lua).
-- Lua modul LatteOS (ROADMAP F2): stupeň výkonu z latte-boot, režimy okien (páska / dlaždice /
-- plávajúce), vzhľad Latte, skratky a gestá. Vlastné úpravy: ~/.config/latteos/hyprland.lua
-- (načíta sa na konci, takže môže prepísať čokoľvek).

package.path = "/usr/share/latteos/hypr/?.lua;/usr/share/latteos/hypr/?/init.lua;" .. package.path

local modemod = require("latte.mode")
local mode    = modemod.load()
local theme   = modemod.theme()
local tiers   = require("latte.tiers")
local windows = require("latte.windows")

-- ── farby Latte (session/noctalia/palettes/Latte.json) ────────────────────────
local colors = {
    active   = { colors = { "rgb(" .. (theme.border_active or "e4b283") .. ")",
                            "rgb(" .. ((theme.id == "latte") and "c98a55" or (theme.border_active or "e4b283")) .. ")" }, angle = 45 },
    inactive = "rgba(" .. (theme.border_inactive or "4a3b30") .. "aa)",
    shadow   = 0xcc0b0806,
    glow          = 0xaae4b283,
    glow_inactive = 0x00000000,
}

-- ── monitory ──────────────────────────────────────────────────────────────────
-- mierka 1: „auto“ vo VM zvolil 2 (lišta dvojnásobná). Na HW ju neskôr nastaví Device Manager.
hl.monitor({ output = "", mode = "preferred", position = "auto", scale = 1 })


-- ── prostredie ────────────────────────────────────────────────────────────────
hl.env("XDG_CURRENT_DESKTOP", "Hyprland")
hl.env("XDG_SESSION_DESKTOP", "latteos")
hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")

-- ── vzhľad (spoločný pre všetky stupne) ───────────────────────────────────────
hl.config({
    general = {
        gaps_in = 5,
        gaps_out = 10,
        border_size = 2,
        col = { active_border = colors.active, inactive_border = colors.inactive },
        resize_on_border = true,
    },
    decoration = { rounding = 14, rounding_power = 2 },     -- jeden polomer pre okná aj panely (radar)
    misc = {
        disable_hyprland_logo = true,
        disable_splash_rendering = true,
        force_default_wallpaper = 0,
    },
    ecosystem = { no_update_news = true, no_donation_nag = true },
    input = {
        kb_layout = "sk,us",
        kb_options = "grp:alt_shift_toggle",
        follow_mouse = 1,
        touchpad = { natural_scroll = true },
    },
})

-- grafika vo VM: bez HW kurzora; pri vm-3d bez commit timingu (setup/f1/RESULTS.md)
if mode.renderer ~= "hw" then
    hl.config({ cursor = { no_hardware_cursors = true } })
end
if mode.renderer == "vm-3d" then
    hl.config({ render = { commit_timing_enabled = false } })
end

-- téma bez efektov (Úsporná, klasické) obmedzí aj efekty kompozitora
local tier = mode.tier
if theme.effects == "ziadne" and (tier == "plny" or tier == "standard" or tier == "usporny") then tier = "minimalny" end
tiers.apply(tier, colors)
windows.setup()

-- herný režim (riadiace centrum Zariadenia / Text Bar): bez efektov a animácií, po vypnutí späť na stupeň.
-- Stav ~/.local/state/latteos/game-mode (1/0). Volá sa: hyprctl eval 'latte.game(true)'
local game_file = (os.getenv("XDG_STATE_HOME") or ((os.getenv("HOME") or "") .. "/.local/state")) .. "/latteos/game-mode"
latte = latte or {}
function latte.game(on)
    tiers.apply(on and "minimalny" or tier, colors)
    hl.config({ decoration = { rounding = on and 0 or 14 }, general = { gaps_in = on and 0 or 5, gaps_out = on and 0 or 10 } })
    local f = io.open(game_file, "w"); if f then f:write(on and "1\n" or "0\n"); f:close() end
    hl.exec_cmd("notify-send -a LatteOS 'Herný režim' '" .. (on and "zapnutý — bez efektov" or "vypnutý") .. "'")
end
do  -- herný režim prežije reload konfigurácie
    local f = io.open(game_file, "r")
    if f then local v = f:read("*l"); f:close(); if v == "1" then latte.game(true) end end
end

-- ── skratky ───────────────────────────────────────────────────────────────────
local mod = "SUPER"
local function bind(keys, action, opts) hl.bind(keys, action, opts) end

bind(mod .. " + Return", hl.dsp.exec_cmd("foot"))
bind(mod .. " + Space",  hl.dsp.exec_cmd("noctalia msg panel-toggle launcher"))     -- Text Bar / spúšťač
bind(mod .. " + Tab",    hl.dsp.exec_cmd("noctalia msg window-switcher"))            -- prehľad pásky
bind(mod .. " + A",      hl.dsp.exec_cmd("noctalia msg panel-toggle control-center"))
bind(mod .. " + E",      hl.dsp.exec_cmd("latte-app subory"))                        -- Súbory (Data Manager)
bind("CTRL + SHIFT + Escape", hl.dsp.exec_cmd("latte-app monitor"))                   -- Monitor (správca procesov)
bind(mod .. " + Q",      hl.dsp.window.close())
bind(mod .. " + F",      hl.dsp.window.fullscreen())
bind(mod .. " + V",      hl.dsp.window.float({ action = "toggle" }))
bind(mod .. " + W",      function() windows.cycle() end)                            -- páska → dlaždice → plávajúce
bind(mod .. " + SHIFT + M", hl.dsp.exit())

-- „Zobraziť plochu“ (Super+D): prepne na prázdnu plochu a rovnakou skratkou späť
local desktop_from = nil
bind(mod .. " + D", function()
    local ws = hl.get_active_workspace()
    if desktop_from and ws and ws.id ~= desktop_from then
        hl.dispatch(hl.dsp.focus({ workspace = desktop_from }))
        desktop_from = nil
    else
        desktop_from = ws and ws.id or nil
        hl.dispatch(hl.dsp.focus({ workspace = "empty" }))
    end
end)

-- fokus a presun okien (v páske posúva stĺpce)
for key, dir in pairs({ left = "left", right = "right", up = "up", down = "down" }) do
    bind(mod .. " + " .. key,          hl.dsp.focus({ direction = dir }))
    bind(mod .. " + CTRL + " .. key,   hl.dsp.window.move({ direction = dir }))
end
-- Super+Shift+šípka: okno na iný monitor (radar: „Presun okna na iný monitor – rozhodnuté“)
bind(mod .. " + SHIFT + left",  hl.dsp.window.move({ monitor = "l" }))
bind(mod .. " + SHIFT + right", hl.dsp.window.move({ monitor = "r" }))

for i = 1, 9 do
    bind(mod .. " + " .. i,           hl.dsp.focus({ workspace = i }))
    bind(mod .. " + SHIFT + " .. i,   hl.dsp.window.move({ workspace = i }))
end
bind(mod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
bind(mod .. " + mouse_up",   hl.dsp.focus({ workspace = "e-1" }))
bind(mod .. " + mouse:272",  hl.dsp.window.drag(),   { mouse = true })
bind(mod .. " + mouse:273",  hl.dsp.window.resize(), { mouse = true })

-- multimédiá
bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"), { locked = true, repeating = true })
bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"),      { locked = true, repeating = true })
bind("XF86AudioMute",        hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"),     { locked = true })
bind("XF86MonBrightnessUp",  hl.dsp.exec_cmd("brightnessctl set 5%+"),                         { locked = true, repeating = true })
bind("XF86MonBrightnessDown",hl.dsp.exec_cmd("brightnessctl set 5%-"),                         { locked = true, repeating = true })

-- ── gestá (touchpad) ──────────────────────────────────────────────────────────
hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace" })

-- ── pravidlá okien ────────────────────────────────────────────────────────────
hl.window_rule({ name = "latte-bez-maximalizacie", match = { class = ".*" }, suppress_event = "maximize" })

-- OOM (F5, session/oom): okná aplikácií majú pri nedostatku pamäte prednosť pred kompozitorom a shellom
hl.on("window.open", function(w)
    if w and w.pid and w.pid > 0 then hl.exec_cmd("choom -n 300 -p " .. math.floor(w.pid)) end
end)

-- ── autoštart ─────────────────────────────────────────────────────────────────
hl.on("hyprland.start", function()
    hl.exec_cmd("dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP XDG_SESSION_TYPE LATTE_MODE LATTE_RENDERER LATTE_TIER")
    hl.exec_cmd("noctalia")
    -- relácia je zdravá, ak po 60 s beží shell → počítadlo pádov = 0
    hl.exec_cmd("latte-boot ok --after 60 --require noctalia")
end)

-- ── vlastné úpravy používateľa ────────────────────────────────────────────────
do
    local home = os.getenv("HOME") or ""
    local user = (os.getenv("XDG_CONFIG_HOME") or (home .. "/.config")) .. "/latteos/hyprland.lua"
    local f = io.open(user, "r")
    if f then
        f:close()
        local ok, err = pcall(dofile, user)
        if not ok then hl.exec_cmd("notify-send -u critical 'LatteOS' 'Chyba v " .. user .. ": " .. tostring(err):gsub("'", "") .. "'") end
    end
end
