-- Stress cases "full lists" + "max numbers" (debug only, phase 8): at frame STRESS_AT (default 5000) fill every item
-- list of the field menu, each with its category's item ids in order, so every item name shows on some page and
-- the scroll arrows, page counts and last rows are drawn. Run after a gear_* warp (the check menu gives the gear
-- first, then the field menu opens at ~f5300):
--   emu.py <cue> --debugger --script tools/debug/warp.lua --var "SCENE='gear_items'" --script tools/debug/stress.lua
-- Inventory (docs/re/debug.md "Inventory"): u32 list pointers at 0x8010D740 per category (0 weapon, 1 armor,
-- 2 accessory, 3 goods, 4 key items), each a u16 item id array (-1 = empty); item counts per category u16 at
-- 0x801DE22E; quantity = byte at 0x801DDA90 + 2 * id (ids < 0x13B; high byte = flags; reader 0x8008A4F8), set
-- to QTY (default 9: the menu draws one digit, 99 showed "x9"; QTY=1 for the singular case). Category id ranges are read off the item names (exe.items), not from game data.
local m = PCSX.getMemPtr()
local at = STRESS_AT or 5000
local CATS = { {0, 99}, {100, 152}, {153, 178, 267, 359}, {179, 245}, {246, 266} }
local function u32(a) a = a - 0x80000000; return m[a] + m[a + 1] * 256 + m[a + 2] * 65536 + m[a + 3] * 16777216 end
local function w16(a, v) a = a - 0x80000000; v = v % 65536; m[a] = v % 256; m[a + 1] = math.floor(v / 256) end
-- Max numbers: party unit records 0x801929CC + k * 0xE4 (live in the field menu too) held every 30 frames:
-- +0x19 LV, +0x1A AT, +0x1C DF, +0x20 MV, +0x22 EXP, +0x24 NEXT, +0x30/+0x32 HP, +0x34/+0x36 MP (u16 but the
-- status screen draws 3 digits: 9999 showed 999). STR/INT on screen are derived (they showed 255).
local function stats()
  for k = 0, 5 do
    local s = 0x801929CC + k * 0xE4
    if m[s - 0x80000000 + 0x19] ~= 0 then
      m[s - 0x80000000 + 0x19] = 99; m[s - 0x80000000 + 0x20] = 199
      for off, v in pairs({ [0x1A] = 999, [0x1C] = 999, [0x22] = 65535, [0x24] = 9999, [0x30] = 999, [0x32] = 999,
                            [0x34] = 999, [0x36] = 999 }) do w16(s + off, v) end
    end
  end
end
local done = false
L.on_frame(function(f)
  if f < at then return end
  if f % 30 == 0 then stats() end
  if done then return end
  done = true
  local money = MONEY or 999999  -- u32 0x80194304; the field menu shows 6 digits (1234567 drew "234567")
  for i = 0, 3 do m[0x194304 + i] = math.floor(money / 256 ^ i) % 256 end
  for c = 0, 4 do
    local p, cap = u32(0x8010D740 + 4 * c), nil
    local nxt = c < 4 and u32(0x8010D740 + 4 * (c + 1)) or 0x801DE22E
    cap = math.floor((nxt - p) / 2)
    local n, r = 0, CATS[c + 1]
    for k = 1, #r, 2 do
      for id = r[k], r[k + 1] do
        if n < cap then
          w16(p + 2 * n, id); n = n + 1
          if id < 0x13B then m[0x1DDA90 + 2 * id] = QTY or 9 end
        end
      end
    end
    local old = m[0x1DE22E + 2 * c]  -- clear only slots that held items: past the last list is other data
    for k = n, math.min(old, cap) - 1 do w16(p + 2 * k, -1) end
    w16(0x801DE22E + 2 * c, n)
    L.log(string.format("stress: category %d at %08X cap %d filled %d", c, p, cap, n))
  end
end)
