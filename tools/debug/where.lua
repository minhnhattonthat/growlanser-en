-- Log the loaded scene and map every WHERE_EVERY frames (default 500) and on each change: "WHERE f scene area sub".
local m = PCSX.getMemPtr()
local every, last = WHERE_EVERY or 500, nil
L.on_frame(function(f)
  local s = string.format("%d %d %d", m[0x196D24] + m[0x196D25] * 256, m[0x196D2A], m[0x196D2B])
  if s ~= last or f % every == 0 then L.log("WHERE f" .. f .. " " .. s); last = s end
end)
