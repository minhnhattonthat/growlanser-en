-- Log MAP.DAT pair loads by caller, and who writes the scene's map pair word 0x80113D96 (G7 hunt, docs/re/graphics.md).
--   warp_all.py NAME --script tools/debug/maplog.lua   (needs --debugger: warp_all adds it with --script)
-- Loader = 0x80018E58(a0 = pair, a1); its callers with a non-constant pair: 0x8001DC38 (half at 0x80113D96),
-- 0x8003EC48 (gp+0x4BA, the area/sub table 0x80100A10), 0x80017010 (logo table 0x800EF898).
local seen = {}
L.on_exec(0x80018E58, function()
  local r = PCSX.getRegisters().GPR.n
  L.log(string.format("f%d mapload pair=%d ra=%08X", L.frame, r.a0, r.ra))
end)
L.on_write(0x80113D96, 0x80113D97, function(addr)
  local pc = L.pc()
  if seen[pc] then return end
  seen[pc] = true
  L.log(string.format("f%d write3d96 pc=%08X", L.frame, pc))
end)
