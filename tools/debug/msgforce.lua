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
local others, ko = {}, 0  -- FFFF-terminated strings (speaker names, tags): cycled through the tag calls
local page, pending, done = 0, nil, false

-- HOST='file': a text section (another scene's, cover.py writes it) whose strings are shown instead of this scene's
-- own: each forced string is copied into this section's text area (buf; speaker strings buf2) and the printer
-- pointed there, so one working scene (warp to scene 0) prints every scene's text. Strings are kept as {b = bytes}.
local host, buf, buf2 = nil, nil, nil
if HOST then
  local f = assert(io.open(HOST, "rb"))
  local d = f:read("*a")
  f:close()
  local function w(i) return d:byte(i + 1) + d:byte(i + 2) * 256 end
  host = { msgs = {}, others = {} }
  local seen = {}
  for i = 0, (w(4) - 4) / 2 - 1 do
    local off = w(4 + 2 * i)
    if not seen[off] and off + 2 <= #d then
      seen[off] = true
      local j = off
      while j + 2 <= #d and w(j) ~= 0xFFFE and w(j) ~= 0xFFFF do j = j + 2 end
      if j + 2 <= #d then
        local s = { b = d:sub(off + 1, j + 2), off = off }
        assert(#s.b <= 0x1000, "string longer than the host buffer")
        if w(j) == 0xFFFE then host.msgs[#host.msgs + 1] = s else host.others[#host.others + 1] = s end
      end
    end
  end
end
local function put(a, b)
  for i = 1, #b do mem[(a + i - 1) % 0x200000] = b:byte(i) end
  return a
end

local entry_base = SLOT
local function find_section()
  for base = SLOT, SLOT + 0x1000, 4 do
    if u32(base) == 0x64 then
      local s = base + u32(base + 88)
      local size, first = u32(s), u16(s + 4)
      if s < SLOT_END and size > 8 and s + size <= SLOT_END and first >= 6 and first % 2 == 0 then
        entry_base = base
        return s, (first - 4) / 2
      end
    end
  end
end

local function load()
  local s, n = find_section()
  if not s then return false end
  sec, msgs, starts, others, ko = s, {}, {}, {}, 0
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
      starts[a] = term
      if term == 0xFFFE then msgs[#msgs + 1] = { a = a, off = off } else others[#others + 1] = a end
    end
  end
  L.log(string.format("FORCE section %08X offsets %d messages %d", s, n, #msgs))
  if host then  -- show the host file's strings instead, copied one at a time into this section's text area
    buf, buf2 = s + 4 + 2 * n, s + 4 + 2 * n + 0x1000
    msgs, others = host.msgs, host.others
    L.log(string.format("FORCE host %s messages %d others %d", HOST, #msgs, #others))
  end
  return true
end

-- Loop (LOOP=1, default): remember the op the VM dispatched last before the first forced message (the message op);
-- when the VM later dispatches an op just past it (the scene moving on), send it back to the message op, so the
-- scene keeps showing messages and every message of the section goes through the real printer.
local LOOP_ON = (LOOP == nil) or LOOP == 1
local last_a0, loop_op, loops = nil, nil, 0
local INJECT_ON, INJECT_F = (INJECT == nil) or INJECT == 1, INJECT_AT or 2600
L.on_exec(0x8003AA3C, function()
  local r = PCSX.getRegisters().GPR.n
  if r.a0 < SLOT or r.a0 >= SLOT_END then return end
  if loop_op and not done and r.a0 > loop_op and r.a0 <= loop_op + 0x40 then
    r.a0 = loop_op
    loops = loops + 1
    if loops <= 3 then L.log(string.format("FORCE loop f%d -> %08X", L.frame, loop_op)) end
    return
  end
  last_a0 = r.a0
  -- INJECT: a scene that shows no message by itself (it waits for the player): once INJECT_AT frames have passed,
  -- jump the VM to the script's first `20 FF 00 00` (the message op scene 0 loops on; byte scan, so maybe a false
  -- hit) and loop there. (Writing that op over the current one crashed the game: scene 1.)
  if LOOP_ON and not loop_op and INJECT_ON and L.frame >= INJECT_F then
    local s = find_section()
    if s and s ~= sec then load() end
  end
  if LOOP_ON and not loop_op and INJECT_ON and L.frame >= INJECT_F and sec and r.a0 >= entry_base and r.a0 < sec then
    local site
    for a = entry_base + 0x64, sec - 4 do
      if u8(a) == 0x20 and u8(a + 1) == 0xFF and u8(a + 2) == 0 and u8(a + 3) == 0 then site = a; break end
    end
    INJECT_ON = false  -- one try
    if site then
      r.a0 = site
      loop_op = site
      L.log(string.format("FORCE inject f%d jump +%X -> +%X", L.frame, last_a0 - entry_base, site - entry_base))
    else
      L.log("FORCE inject: no 20 FF 00 00 in the script")
    end
  end
end)

L.on_exec(0x8006E794, function()
  if done then return end
  local s = find_section()  -- the slot is refilled on every scene load (title, New Game, the warp target)
  if not s then return end
  if s ~= sec or not msgs then load() end
  local r = PCSX.getRegisters().GPR.n
  local pp = u32(r.sp + 0x1C)
  local p = u32(pp)
  if starts[p] then
    if starts[p] == 0xFFFE then
      k = k + 1
      local m = msgs[k]
      if not m and LOOP_ON and ko < #others then  -- speaker strings no name tag showed: print them as messages
        ko = ko + 1
        m = host and others[ko] or { a = others[ko], off = others[ko] - sec }
      end
      if not m then done = true; L.log("FORCE done " .. #msgs); return end
      w32(pp, host and put(buf, m.b) or m.a)
      page = 0
      if LOOP_ON and not loop_op and last_a0 then
        loop_op = last_a0
        L.log(string.format("FORCE loop op %08X (entry +%X, op %02X)", loop_op, loop_op - entry_base, u8(loop_op)) .. string.format(" %02X %02X %02X %02X %02X %02X",
          u8(loop_op + 1), u8(loop_op + 2), u8(loop_op + 3), u8(loop_op + 4), u8(loop_op + 5), u8(loop_op + 6)))
      end
      L.log(string.format("FORCE %d %04X f%d", k, m.off, L.frame))
    elseif LOOP_ON and loop_op and ko < #others then  -- a name tag: show the next speaker string instead
      ko = ko + 1
      w32(pp, host and put(buf2, others[ko].b) or others[ko])
    end
  end
  page = page + 1
  pending = { at = L.frame + WAIT_F, name = string.format("m%04d_%02d.png", k, page) }
end)

-- With the loop on, end the run once the section is done or nothing was forced for STALL frames (scene without a
-- message flow): final.png then quit, so a coverage run doesn't idle out its --frames.
local STALL_F, last_force = STALL or 2500, 0
L.on_frame(function(f)
  if pending and f >= pending.at then
    if SHOTS_ON ~= 0 then L.shot(pending.name) end
    pending = nil; last_force = f
  end
  if LOOP_ON and f > 4000 and (done or f - last_force > STALL_F) then
    L.log(string.format("FORCE end f%d %s forced %d", f, done and "done" or "stalled", k - (FROM or 0)))
    L.shot("final.png"); L.finish(0)
  end
end)
