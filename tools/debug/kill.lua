-- Keep the hero's HP at HP_TO (default 1) from frame KILL_AT on (debug only): the next enemy hit is a defeat, which
-- shows the game over screen. Used by the `gameover` warp (scenes.txt keyword `kill`, warp_all adds this script).
--   emu.py <cue> --script tools/debug/warp.lua --var "SCENE='gameover'" --script tools/debug/kill.lua --var KILL_AT=4700
-- Unit records: 0x801929CC + k*0xE4 (k 0 = hero), x/y +0x2C/+0x2E, HP +0x30, max HP +0x32 (RAM dumps of the
-- tutorial battle: HUD 26 -> 23 on a Gel hit; docs/re/debug.md "Game over"). Only lowers HP, so a hit to 0 sticks.
local m = PCSX.getMemPtr()
local at, to = KILL_AT or 10, HP_TO or 1
local logged = false
L.on_frame(function(f)
  if f < at then return end
  local hp = m[0x1929FC] + m[0x1929FD] * 256
  if hp > to then
    m[0x1929FC] = to % 256; m[0x1929FD] = 0
    if not logged then L.log(string.format("kill: hero HP %d -> %d at f%d", hp, to, f)); logged = true end
  end
end)
