-- Log every call of the SCEN load-request builder 0x80018BD4 (docs/re/debug.md): args and caller.
--   emu.py <cue> --debugger --script tools/debug/scenelog.lua ...
L.on_exec(0x80018BD4, function()
  local g = PCSX.getRegisters().GPR.n
  local function r(n) return tonumber(g[n]) end
  L.log(string.format("f%d scenreq ra=%08X a0=%08X a1=%08X a2=%08X a3=%08X", L.frame, r("ra"), r("a0"), r("a1"),
    r("a2"), r("a3")))
end)
