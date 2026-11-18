-- Log the high-water mark of the game's heap bump pointer gp+0xD0C (0x801145E8). The heap runs 0x80146778-0x80186778
-- (base gp+0xCC4, set at 0x800C1AD4); vwf/MSYS growth moves its base up (docs/re/text.md "RAM map").
--   emu.py <cue> --script tools/debug/warp.lua --var "SCENE='bt_tutorial'" --script tools/debug/heapwatch.lua ...
local mem = PCSX.getMemPtr()
local function u8(a) return mem[a % 0x200000] end
local function u32(a) return u8(a) + u8(a + 1) * 256 + u8(a + 2) * 65536 + u8(a + 3) * 16777216 end
local hi = 0
L.on_frame(function(n)
  local v = u32(0x801145E8)
  if v > hi and v < 0x80200000 and v >= 0x80000000 then
    hi = v
    L.log(string.format("f%d heap top %08X (%d KB used of 256, base %08X)", n, v, math.floor((v - 0x80146778) / 1024),
      u32(0x801145A0)))
  end
end)
