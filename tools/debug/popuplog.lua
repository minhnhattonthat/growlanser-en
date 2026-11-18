-- Log each call of the bubble / place-popup routine 0x8006BA48 (a0 = request struct: +0 id, +2 x, +4 y, +6 source,
-- +7 tail type (s1), +8 string source, +9 style (s0)), so popup and menu-bubble calls can be told apart.
-- Needs --debugger:  emu.py <cue> --debugger --script tools/debug/warp.lua --var "SCENE='bt_bernard'"
--   --script tools/debug/popuplog.lua
local mem = PCSX.getMemPtr()
local function u8(a) return mem[a % 0x200000] end
local function s16(a) local v = u8(a) + u8(a + 1) * 256; return v >= 0x8000 and v - 0x10000 or v end
local last = {}
L.on_exec(0x8006BA48, function()
  local a = PCSX.getRegisters().GPR.n.a0
  if a == 0 then return end
  local key = string.format("id=%d x=%d y=%d src6=%d tail7=%d src8=%d style9=%d", s16(a), s16(a + 2), s16(a + 4),
    u8(a + 6), u8(a + 7), u8(a + 8), u8(a + 9))
  if last[a] ~= key then
    last[a] = key
    L.log(string.format("f%d popup a0=%08X %s", L.frame, a, key))
  end
end)
-- the frame-width site both paths reach (asm popup_width hook): s0 style, s1 tail, s2 request
local seen = {}
L.on_exec(0x8006BBB8, function()
  local r = PCSX.getRegisters().GPR.n
  local key = string.format("s0=%d s1=%d s2=%08X ra=%08X", r.s0, r.s1, r.s2, r.ra)
  if not seen[key] then
    seen[key] = true
    L.log(string.format("f%d width %s", L.frame, key))
  end
end)
