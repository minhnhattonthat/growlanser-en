-- Message tour probe (phase 8): every time the scene shows a message, show the next message of the scene's text
-- section instead, so mashing Circle walks through all of them, and shoot each page. Needs emu.py --debugger.
--   emu.py <cue> --debugger --script tools/debug/warp.lua --var "SCENE='scene 2'" --var "THEN='6 circle*400'"
--          --script tools/debug/msgforce.lua [--var FROM=0] [--var WAIT=20]
-- The printer (0x8006E794) gets the text pointer at *(*(sp+0x1C)). A call whose pointer is a message start in the
-- loaded scene's section (any offset-table target ending in FFFE) is a new message: the pointer is replaced with
-- message k (offset-table order, FROM first). Other calls (name tags, continuation pages, menus) are left alone.
-- Shots: mKKKK_PP.png WAIT frames after each call. Log: "FORCE k off" per message, "FORCE done n" at the end.
-- Scene entry = first u32 0x64 header after the slot base 0x80128B98 whose word 22 points at a sane section.
local mem = PCSX.getMemPtr()
local function u8(a) return mem[a % 0x200000] end
local function u16(a) return u8(a) + u8(a + 1) * 256 end
local function u32(a) return u16(a) + u16(a + 2) * 65536 end
local function w32(a, v)
  for i = 0, 3 do mem[(a + i) % 0x200000] = math.floor(v / 256 ^ i) % 256 end
end
local SLOT, SLOT_END = 0x80128B98, 0x80128B98 + 0x7000
local WAIT_F = WAIT or 20
local k, msgs, starts, sec = FROM or 0, nil, nil, nil
local page, pending, done = 0, nil, false

local function find_section()
  for base = SLOT, SLOT + 0x1000, 4 do
    if u32(base) == 0x64 then
      local s = base + u32(base + 88)
      local size, first = u32(s), u16(s + 4)
      if s < SLOT_END and size > 8 and s + size <= SLOT_END and first >= 6 and first % 2 == 0 then
        return s, (first - 4) / 2
      end
    end
  end
end

local function load()
  local s, n = find_section()
  if not s then return false end
  sec, msgs, starts = s, {}, {}
  local seen = {}
  for i = 0, n - 1 do
    local off = u16(s + 4 + 2 * i)
    if not seen[off] then
      seen[off] = true
      local a, term = s + off, nil
      for j = 0, 4095 do
        local w = u16(a + 2 * j)
        if w == 0xFFFE or w == 0xFFFF then term = w; break end
      end
      starts[a] = true
      if term == 0xFFFE then msgs[#msgs + 1] = { a = a, off = off } end
    end
  end
  L.log(string.format("FORCE section %08X offsets %d messages %d", s, n, #msgs))
  return true
end

L.on_exec(0x8006E794, function()
  if done then return end
  local s = find_section()  -- the slot is refilled on every scene load (title, New Game, the warp target)
  if not s then return end
  if s ~= sec or not msgs then load() end
  local r = PCSX.getRegisters().GPR.n
  local pp = u32(r.sp + 0x1C)
  local p = u32(pp)
  if starts[p] then
    local is_msg = false
    for j = 0, 4095 do
      local w = u16(p + 2 * j)
      if w == 0xFFFE then is_msg = true; break elseif w == 0xFFFF then break end
    end
    if is_msg then
      k = k + 1
      local m = msgs[k]
      if not m then done = true; L.log("FORCE done " .. #msgs); return end
      w32(pp, m.a)
      page = 0
      L.log(string.format("FORCE %d %04X f%d", k, m.off, L.frame))
    end
  end
  page = page + 1
  pending = { at = L.frame + WAIT_F, name = string.format("m%04d_%02d.png", k, page) }
end)

L.on_frame(function(f)
  if pending and f >= pending.at then L.shot(pending.name); pending = nil end
end)
