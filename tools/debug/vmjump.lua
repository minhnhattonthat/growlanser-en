-- Jump the event VM to a script offset of the loaded scene once, AT frames in (reach one NPC/shop handler from a
-- warp without walking there). Needs --debugger. Use with warp.lua:
--   emu.py <cue> --debugger --script tools/debug/warp.lua --var "SCENE='scene 1'" --script tools/debug/vmjump.lua
--          --var ENTRY=281 --var OFF=0x1A6A --var AT=1500
-- ENTRY = SCEN.DAT entry (scene N's script = 280 + N), OFF = byte offset of the op to run next (tools/scenelinks.py
-- and byte scans give these). The dispatcher reads the op at *(gp+0x428) in 0x8003AA3C (a0 = pointer).
-- The entry's RAM base is found by matching its first 32 bytes in the scene slot.
local mem = PCSX.getMemPtr()
local function u8(a) return mem[a % 0x200000] end
local SLOT, SLOT_END = 0x80128B98, 0x80128B98 + 0x20000
local root = OUT:gsub("\\", "/"):match("^(.*)/work/") or "."
local f = assert(io.open(root .. "/work/disc1/tree/SCEN.DAT", "rb"), "SCEN.DAT")
local all = f:read("*a"); f:close()
-- tools/dat.py: u32 count, then (u16 start sector, u16 sectors) per entry
local sec = all:byte(4 + 4 * ENTRY + 1) + all:byte(4 + 4 * ENTRY + 2) * 256
local first = all:sub(sec * 2048 + 1, sec * 2048 + 32)
local base, done = nil, false
L.on_exec(0x8003AA3C, function()
  if done or L.frame < AT then return end
  if not base then
    for a = SLOT, SLOT_END - 32, 4 do
      local ok = true
      for i = 0, 31 do if u8(a + i) ~= first:byte(i + 1) then ok = false break end end
      if ok then base = a break end
    end
    if not base then L.log("vmjump: entry not in RAM"); done = true; return end
  end
  local r = PCSX.getRegisters().GPR.n
  if r.a0 < base or r.a0 >= base + 0x8000 then return end
  L.log(string.format("vmjump f%d ptr %08X -> %08X (base %08X)", L.frame, r.a0, base + OFF, base))
  r.a0 = base + OFF
  done = true
end)
