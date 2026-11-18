-- Growlanser debug warp: cold boot -> New Game -> straight into any scene, by name from tools/debug/scenes.txt.
--   emu.py <cue> --out work/qa/warp --script tools/debug/warp.lua --var "SCENE='<name>'" --frames 3000 --sheet
--   --var "SCENE='scene 42'" (a raw scene id 0-279, optional "area A sub S") works too.
-- How it works (docs/re/debug.md): the New Game branch at 0x800166E8 sets area 2 / sub 5 (the map) and zeroes the
-- scene request 0x80113D62/0x80113D66, then the field loader loads scene 0x80113D66. Before the title menu we patch
-- that code in RAM (debug only, never in a build): area/sub immediates replaced, the two zeroing stores NOPed, and
-- the request set to the wanted scene. Then the script presses Start (logos) / Circle (title: START) for you.
-- The scene's own script runs from its start with story flags clear (New Game state).
-- Disc 2 story points (休暇8 on): run on the disc 2 cue with tools/debug/disc2.lua (docs/re/debug.md "Disc 2").
-- Globals: SCENE (required), THEN (extra route after landing, "60 -;6 triangle"), VOICE=1 (keep voices).
local mem = PCSX.getMemPtr()
local function u8(a) return mem[a % 0x200000] end
local function u16(a) return u8(a) + u8(a + 1) * 256 end
local function w16(a, v) a = a % 0x200000; mem[a] = v % 256; mem[a + 1] = math.floor(v / 256) % 256 end
local function w32(a, v) w16(a, v % 0x10000); w16(a + 2, math.floor(v / 0x10000)) end

local REQ_A, REQ_B = 0x80113D62, 0x80113D66   -- scene request (two copies the loader reads)
local LOADED = 0x80196D24                      -- save block 0x80196A70 + 0x2B4: scene now loaded (0xFFFF none)
local AREA, SUB = 0x80196D2A, 0x80196D2B        -- save block + 0x2BA / 0x2BB: map area / sub
local MODE = 0x80113D68                         -- 2 once boot init has run (title / new game path)
local FRONT = 0x80113B68                        -- gp+0x28C front-end state: 8 = title menu up
local title_for, chosen = 0, false             -- frames the title menu has been up; START picked

-- tools/debug/scenes.txt: "name  scene N [area A sub S] [then ROUTE]" or "name  title [then ROUTE]"
local root = OUT:match("^(.*)/work/") or "."
local function parse(line)
  local spec = {}
  local body, route = line:match("^(.-)%s+then%s+(.+)$")
  spec.route = route
  body = body or line
  spec.kind = body:match("^(%a+)")
  spec.scene = tonumber(body:match("scene%s+(%d+)"))
  spec.area = tonumber(body:match("area%s+(%d+)"))
  spec.sub = tonumber(body:match("sub%s+(%d+)"))
  return spec
end
local spec
local want = assert(SCENE, "set --var \"SCENE='<name>'\" (tools/debug/scenes.txt)")
if want:match("^scene%s") or want == "title" then
  spec = parse(want)
else
  local f = assert(io.open(root .. "/tools/debug/scenes.txt", "r"), "tools/debug/scenes.txt not found under " .. root)
  for line in f:lines() do
    local name, rest = line:gsub("#.*", ""):match("^(%S+)%s+(.-)%s*$")
    if name == want then spec = parse(rest) end
  end
  f:close()
  assert(spec, "scene not in tools/debug/scenes.txt: " .. want)
end
if THEN then spec.route = THEN end
spec.area, spec.sub = spec.area or 2, spec.sub or 5   -- New Game's own map (the moonlit cliff)

local patched, landed, routed = false, nil, false
local function patch()
  w32(0x80016614, 0x24040000 + spec.area)   -- addiu a0, zero, AREA (two delay slots on the way to 0x800166E8)
  w32(0x8001662C, 0x24040000 + spec.area)
  w32(0x800166E8, 0x24050000 + spec.sub)    -- addiu a1, zero, SUB
  w32(0x8001670C, 0)                        -- nop: sh zero, 0x3D62(at)
  w32(0x80016714, 0)                        -- nop: sh zero, 0x3D66(at)
  patched = true
end

L.on_frame(function(f)
  -- voice off (bit 0x10 of 0x80194AA5, tested by the voice player 0x80053F74): headless PCSX hangs mid-dialogue
  -- waiting on XA voice. VOICE=1 keeps voices.
  if not VOICE and f > 800 then mem[0x194AA5] = bit.bor(mem[0x194AA5], 0x10) end
  if u8(FRONT) == 8 then title_for = title_for + 1 else title_for = 0 end
  if spec.kind == "title" then
    if not landed and title_for >= 90 then landed = f; L.log("landed title at f" .. f) end
  else
    if not patched and u8(MODE) == 2 then patch(); L.log("patched at f" .. f) end
    if patched and not landed then
      w16(REQ_A, spec.scene); w16(REQ_B, spec.scene)
      if u16(LOADED) == spec.scene and u8(AREA) == spec.area and u8(AREA + 1) == spec.sub then
        landed = f
        L.log(string.format("landed scene %d area %d sub %d at f%d", spec.scene, spec.area, spec.sub, f))
      end
    end
  end
  if not landed and L.route_done() then   -- boot input: Start skips logos; Circle picks START on the title
    if spec.kind ~= "title" and (chosen or title_for >= 60) then  -- Circle: START on the title, then dialogue
      chosen = true; L.press("circle", 4); L.press("-", 30)
    elseif title_for == 0 then L.press("-", 26); L.press("start", 4)  -- Start skips the logos
    else L.press("-", 1) end
  end
  if landed and not routed and spec.route then
    routed = true
    local function press(keys, n) L.press(keys, n) end
    for step in spec.route:gmatch("[^;]+") do
      local k = step:match("^%s*pick%s+(%d+)%s*$")   -- pick N: menu cursor down N times, then Circle
      if k then
        for _ = 1, tonumber(k) do press("down", 6); press("-", 24) end
        press("circle", 6); press("-", 120)
      else
        local n, keys, rep = step:match("^%s*(%d+)%s+([%w%+%-]+)%*?(%d*)%s*$")
        assert(n, "bad route step: " .. step)
        if rep ~= "" then  -- "6 circle*20": press, 30 frames idle, 20 times
          for _ = 1, tonumber(rep) do press(keys, tonumber(n)); press("-", 30) end
        else press(keys, tonumber(n)) end
      end
    end
  end
  if FRAMES and f >= FRAMES - 1 and not landed then L.fail("warp: never landed in " .. want) end
end)
