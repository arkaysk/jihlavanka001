--!nonstrict
-- Režim Linux príkaz (/cmd): náhľad príkazu, beh v termináli. Deštruktívne príkazy vyžadujú potvrdenie
-- (druhý výber), sudo sa nikdy nespúšťa potichu — heslo zadáva používateľ v termináli.
local CONFIRM = "  #potvrdit"

local dangerous = {
  "^%s*sudo%s", "rm%s+%-[%a]*[rf]", "%f[%w]dd%s", "mkfs", "wipefs", "shred", "fdisk", "parted",
  "chmod%s+%-R", "chown%s+%-R", ">%s*/dev/sd", ">%s*/dev/nvme", "dnf%s+remove",
  "systemctl%s+stop", "systemctl%s+disable", "systemctl%s+mask",
  ":%(%)%s*{",
}

local function isDangerous(cmd)
  for _, p in ipairs(dangerous) do
    if string.find(cmd, p) then return true end
  end
  return false
end

function onQuery(text)
  local raw = text or ""
  local confirmed = string.sub(raw, -#CONFIRM) == CONFIRM
  local cmd = confirmed and string.sub(raw, 1, #raw - #CONFIRM) or raw
  cmd = string.gsub(cmd, "^%s+", "")
  if cmd == "" then
    launcher.setResults(text, { { id = "", title = "Napíš Linux príkaz", subtitle = "spustí sa v termináli; nebezpečné príkazy treba potvrdiť", glyph = "terminal-2" } })
    return
  end
  if isDangerous(cmd) and not confirmed then
    launcher.setResults(text, {
      { id = "", title = "⚠ Pozor: " .. cmd, subtitle = "Príkaz môže mazať alebo meniť systém. Vyber znova na potvrdenie.",
        glyph = "alert-triangle", query = "/cmd " .. cmd .. CONFIRM },
    })
    return
  end
  launcher.setResults(text, {
    { id = cmd, title = cmd, subtitle = confirmed and "Potvrdené — spustiť v termináli" or "Spustiť v termináli", glyph = "player-play" },
  })
end

function onActivate(id)
  if id == nil or id == "" then return end
  -- terminál ostane otvorený, kým ho používateľ nezavrie Enterom
  noctalia.runInTerminal(id .. "; echo; read -r -p '[LatteOS] Enter zatvorí terminál… ' _")
end
