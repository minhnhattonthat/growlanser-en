-- Open AORI's APPENDIX ROOM (debug only): hold the appendix unlock flags every frame, so the title's APPENDIX shows
-- the room (G4) instead of "Now Closing". Used by the `appendix` warp (scenes.txt keyword `appendix`).
-- Flags (PS cheat codes, docs/re/debug.md "Appendix"): GL chips cards 0x801144D4-D6, music mode 0x801144DA,
-- event CGs 0x801144E4-E7.
local m = PCSX.getMemPtr()
local set = { [0x1144D4] = 0xFF, [0x1144D5] = 0xFF, [0x1144D6] = 0xFF, [0x1144DA] = 0x01,
              [0x1144E4] = 0xFF, [0x1144E5] = 0xFF, [0x1144E6] = 0xFF, [0x1144E7] = 0xFF, [0x1144FD] = 0x01 }
L.on_frame(function(f)
  if f < 60 then return end
  for a, v in pairs(set) do m[a] = v end
end)
