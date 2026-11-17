-- Log every CD read request the game hands to its request handler 0x8001835C (docs/re/text.md "File reads").
--   emu.py <cue> --debugger --script tools/debug/reqlog.lua ...
-- Request records are 12 bytes at 0x80191120 + 12*a0: h type, b ?, b file index (0 MAP 1 SCEN 2 XATBL 3 MSYS ...),
-- b ?, b ?, h entry, w destination.
local mem = PCSX.getMemPtr()
local function u8(a) return mem[a % 0x200000] end
local function u16(a) return u8(a) + u8(a + 1) * 256 end
local function u32(a) return u16(a) + u16(a + 2) * 65536 end
L.on_exec(0x8001835C, function()
  local r = PCSX.getRegisters().GPR.n
  local rec = 0x80191120 + 12 * r.a0
  local b = {}
  for i = 0, 11 do b[#b + 1] = string.format("%02X", u8(rec + i)) end
  L.log(string.format("f%d req slot=%d ra=%08X rec=%s file=%d entry=%d dst=%08X", L.frame, r.a0, r.ra,
    table.concat(b, " "), u8(rec + 3), u16(rec + 6), u32(rec + 8)))
end)
