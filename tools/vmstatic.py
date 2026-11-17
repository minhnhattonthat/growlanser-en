"""vmstatic.py: guess event-VM op lengths from the handler code (docs/re/debug.md).

The dispatcher (0x8003AA3C) reads the op byte, stores ptr+1 at 0x428($gp) and jumps through the table at
0x800114F0 (0xD6 ops). A handler that advances the script does `lw r, 0x428($gp)` ... `addiu r2, r, K` ...
`sw r2, 0x428($gp)`. This walks each handler's fall-through path (following plain `j`, stopping at the common exit
0x8003DCA8 or a `jr`) and reports every K it sees: op length = 1 + K. Ops whose handler calls out or adds a
register are marked '?', for vmops.py (dynamic) to settle.

    python -X utf8 tools/vmstatic.py [EXE]
"""
import re
import struct
import sys

from capstone import CS_ARCH_MIPS, CS_MODE_32, CS_MODE_LITTLE_ENDIAN, Cs

BASE = 0x80010000 - 0x800
TABLE, NOPS, EXIT = 0x800114F0, 0xD6, 0x8003DCA8


def handler_lengths(exe, addr, md, limit=80):
    """Return (set of K, flags) along the fall-through path of one handler."""
    regs, ks, flags = {}, set(), set()
    pc = addr
    for _ in range(limit):
        ins = next(md.disasm(exe[pc - BASE:pc - BASE + 4], pc), None)
        if ins is None:
            break
        m, ops = ins.mnemonic, ins.op_str
        if m == "lw" and ops.endswith("0x428($gp)"):
            regs[ops.split(",")[0]] = 0
        elif m == "addiu":
            d, s, k = [x.strip() for x in ops.split(",")]
            if s in regs:
                regs[d] = regs[s] + int(k, 0)
            else:
                regs.pop(d, None)
        elif m == "sw" and ops.endswith("0x428($gp)"):
            r = ops.split(",")[0]
            if r in regs:
                ks.add(regs[r])
            else:
                flags.add("reg")
        elif m in ("addu", "subu", "move", "lbu", "lhu", "lw", "lb", "lh", "or", "sll", "andi", "ori"):
            d = ops.split(",")[0]
            if m == "move" and ops.split(",")[1].strip() in regs:
                regs[d] = regs[ops.split(",")[1].strip()]
            else:
                regs.pop(d, None)
        elif m == "jal":
            flags.add("call")
        if m == "j":
            tgt = int(ops, 0)
            if tgt == EXIT:
                # delay slot first
                nxt = next(md.disasm(exe[pc + 4 - BASE:pc + 8 - BASE], pc + 4), None)
                if nxt and nxt.mnemonic == "sw" and nxt.op_str.endswith("0x428($gp)"):
                    r = nxt.op_str.split(",")[0]
                    if r in regs:
                        ks.add(regs[r])
                break
            pc = tgt
            continue
        if m == "jr":
            break
        pc += 4
    return ks, flags


if __name__ == "__main__":
    exe = open(sys.argv[1] if len(sys.argv) > 1 else "work/disc1/tree/SLPS_023.80", "rb").read()
    md = Cs(CS_ARCH_MIPS, CS_MODE_32 + CS_MODE_LITTLE_ENDIAN)
    table = struct.unpack_from("<%dI" % NOPS, exe, TABLE - BASE)
    for op, a in enumerate(table):
        ks, flags = handler_lengths(exe, a, md)
        lens = sorted(1 + k for k in ks) if ks else [1]
        print(f"{op:02X} {a:08X} len {','.join(map(str, lens))} {' '.join(sorted(flags))}")
