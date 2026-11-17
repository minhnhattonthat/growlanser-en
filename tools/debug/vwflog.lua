-- Log every vwf_draw call (asm/vwf.asm): col a0, row a1, code a2, scale a3, canvas base1/split, the printer's
-- caller and the matching slot. Address from work/asm/vwf.sym (pass --var VWF_DRAW=0x...; default = last build).
--   emu.py <cue> --debugger --script tools/debug/warp.lua --var "SCENE='newgame'" --script tools/debug/vwflog.lua
local mem = PCSX.getMemPtr()
local function u8(a) return mem[a % 0x200000] end
local function u16(a) return u8(a) + u8(a + 1) * 256 end
local function u32(a) return u16(a) + u16(a + 2) * 65536 end
local addr = VWF_DRAW or 0x800FF56C
local state = addr - 0x64                       -- vwf_state sits 0x64 before vwf_draw
local n = 0
L.on_exec(addr, function()
  n = n + 1
  if n > (VWF_MAX or 4000) then return end
  local r = PCSX.getRegisters().GPR.n
  local slots = {}
  for i = 0, 3 do
    local s = state + 16 + 16 * i
    slots[#slots + 1] = string.format("%08X:%d/%d/%d", u32(s), u32(s + 4), u32(s + 8) | 0, u32(s + 12) | 0)
  end
  L.log(string.format("f%d col=%d row=%d code=%04X sc=%d ra=%08X sp_ra=%08X base1=%08X split=%d base2=%08X | %s",
    L.frame, r.a0, r.a1, r.a2, r.a3, r.ra, u32(r.sp + 0x34), u32(0x801D2808), u32(0x801D2810), u32(0x801D2818),
    table.concat(slots, " ")))
end)
-- Print wrapper 0x8006777C (11 callers): args, stack args, and the printer's return value.
L.on_exec(0x8006777C, function()
  local r = PCSX.getRegisters().GPR.n
  local st = {}
  for i = 0, 6 do st[#st + 1] = string.format("%X", u32(r.sp + 0x10 + 4 * i)) end
  L.log(string.format("f%d wrap a0=%X a1=%X a2=%X a3=%X ra=%08X stk=%s", L.frame, r.a0, r.a1, r.a2, r.a3, r.ra,
    table.concat(st, ",")))
end)
L.on_exec(0x800677FC, function()
  local r = PCSX.getRegisters().GPR.n
  L.log(string.format("f%d wrap ret v0=%X", L.frame, r.v0))
end)
-- The game's own glyph routines and the printer entry: any hit here bypasses the VWF.
for _, a in ipairs({0x800711E0, 0x80071650, 0x8006E794}) do
  L.on_exec(a, function()
    n = n + 1
    if n > (VWF_MAX or 4000) then return end
    local r = PCSX.getRegisters().GPR.n
    L.log(string.format("f%d hit %08X a0=%08X a1=%08X a2=%08X ra=%08X base1=%08X", L.frame, a, r.a0, r.a1, r.a2,
      r.ra, u32(0x801D2808)))
  end)
end
