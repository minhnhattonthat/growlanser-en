-- Text coverage probe: at the printer's entry (0x8006E794) hash the message it is about to draw and log
-- "TEXT <hex>" once per distinct hash (same hash as tools/strings.py). Needs emu.py --debugger.
--   emu.py <cue> --debugger --script tools/debug/warp.lua --var "SCENE='x'" --script tools/debug/textlog.lua
local mem = PCSX.getMemPtr()
local function u8(a) return mem[a % 0x200000] end
local function u16(a) return u8(a) + u8(a + 1) * 256 end
local function u32(a) return u16(a) + u16(a + 2) * 65536 end
local seen = {}
L.on_exec(0x8006E794, function()
  local r = PCSX.getRegisters().GPR.n
  local p = u32(u32(r.sp + 0x1C))
  local h = 0
  for i = 0, 4095 do
    local w = u16(p + 2 * i)
    if w == 0xFFFE or w == 0xFFFF then break end
    h = (h * 31 + w) % 4294967296
  end
  if not seen[h] then
    seen[h] = true
    L.log(string.format("TEXT %X f%d p=%08X", h, L.frame, p))
  end
end)
