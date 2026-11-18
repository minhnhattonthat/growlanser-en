-- Run on disc 2 as if it were the expected disc (debug only): pass with warp.lua on the disc 2 cue.
--   emu.py "<disc 2 cue>" --script tools/debug/warp.lua --script tools/debug/disc2.lua --var "SCENE='...'"
-- The disc check 0x80054968 searches names[gp+0x724] (EXE 0x8001294C: \SLPS_023.80;1, \SLPS_023.81;1). Holding
-- that byte (0x80114000) at 1 makes New Game accept disc 2, so late story points need no disc swap.
local m = PCSX.getMemPtr()
L.on_frame(function() m[0x114000] = 1 end)
