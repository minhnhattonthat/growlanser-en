-- Log the message pre-parser's glyph steps (asm/vwf.asm vwf_measure: s1 column, code) and its entry, so a text
-- extent (gp+0x832, the page's print width) can be traced. Needs --debugger.
--   emu.py <cue> --debugger --script tools/debug/warp.lua --var "SCENE='newgame'" --script tools/debug/measurelog.lua
--     --var MEASURE=0x<vwf_measure from work/asm/vwf.sym> [--var FROM=5800]
local mem = PCSX.getMemPtr()
local function u8(a) return mem[a % 0x200000] end
local function u16(a) return u8(a) + u8(a + 1) * 256 end
local from = FROM or 0
local function regs() return PCSX.getRegisters().GPR.n end
L.on_exec(0x800643D0, function()
  if L.frame < from then return end
  local r = regs()
  L.log(string.format("f%d parse text=%08X col=%d row=%d ra=%08X", L.frame, r.a0, r.a1, r.a2, r.ra))
end)
L.on_exec(assert(MEASURE, "--var MEASURE=0x..."), function()
  if L.frame < from then return end
  local r = regs()
  L.log(string.format("f%d measure s1=%d code=%04X scale=%d x832=%d x84a=%d", L.frame, r.s1, u16(r.s2 - 2), r.v0,
    u16(r.gp + 0x832), u16(r.gp + 0x84A)))
end)
L.on_exec(0x80064FC0, function()  -- the parser's loop continuation: s1 after a step
  if L.frame < from then return end
  local r = regs()
  L.log(string.format("f%d next s1=%d s0=%d text=%08X code=%04X", L.frame, r.s1, r.s0, r.s2, u16(r.s2)))
end)
L.on_exec(0x80064FD4, function()  -- the parser's exit test
  if L.frame < from then return end
  local r = regs()
  L.log(string.format("f%d exit s1=%d s0=%d text=%08X a3=%04X", L.frame, r.s1, r.s0, r.s2, r.a3))
end)
L.on_exec(0x80065630, function()  -- page-at-once print call
  if L.frame < from then return end
  local r = regs()
  L.log(string.format("f%d print a0=%d a1=%d a2=%d a3=%d", L.frame, r.a0, r.a1, r.a2, r.a3))
end)
