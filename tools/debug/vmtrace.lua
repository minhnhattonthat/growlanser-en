-- Trace the event VM (docs/re/debug.md): each op dispatched at 0x8003AA48 (v1 = op, a0 = pointer past the op byte),
-- plus where each scene entry loads (SCEN request builder 0x80018BD4: a2 = 0/1/2 for entries N-280/N/N+280,
-- a3 = destination). Use with warp.lua and --debugger; tools/vmops.py turns the log into op lengths.
L.on_exec(0x8003AA48, function()
  local g = PCSX.getRegisters().GPR.n
  L.log(string.format("op %02X %08X", tonumber(g.v1), tonumber(g.a0)))
end)
L.on_exec(0x80018BD4, function()
  local g = PCSX.getRegisters().GPR.n
  L.log(string.format("load %d %d %08X", tonumber(g.a0), tonumber(g.a2), tonumber(g.a3)))
end)
