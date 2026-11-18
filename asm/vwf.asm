; vwf.asm: proportional English text for Growlanser (armips, applied by tools/insert.py to SLPS_023.80).
;
; The text printer (0x8006E794) draws into a 4bpp RAM canvas (struct 0x801D2808: base1, stride1, split, -, base2,
; stride2; texels from split*12 on go to canvas 2, low nibble = left texel). Two glyph routines read the font:
;   0x800711E0 (col, row+1, code): normal text, 1 texel per font pixel, 1 canvas row per font row, y = row*16+2,
;                                  x = col*12 texels; the printer then adds 1 to its column s6. (jal 0x8006F3A8)
;   0x80071650 (col, row, code):   double size, 2x2 texels per font pixel, y = row*16+6, x = col*12 texels;
;                                  the printer adds 2. (jal 0x8006F49C)
; vwf_std / vwf_big replace those calls. They keep their own texel x, draw pair codes (tools/enfont.py) as two
; proportional glyphs, dictionary codes (tools/dictenc.py) as their entry's pairs, and game glyphs 12 px wide,
; and return the column ceil(x / 12), which the printer stores in
; s6. The texel x resyncs to col*12 whenever the printer moves (new line, page, window, indent).
; Code and data live in the font's last kanji cells (0x6A0-0x7CA), unused once the script is English.
; Tested under unicorn: tests/test_vwf.py (tools/vwfemu.py).

.psx
.open "SLPS_023.80", 0x8000F800

WAIT       equ 0x80069D64        ; called by the printer after each glyph
PAIR       equ 0x0800
FREE_START equ 0x800FF508        ; font cell 0x6A0
FREE_END   equ 0x80100A0E        ; end of the font (cell 0x7CB)
DICT       equ 0x4800            ; codes DICT + i = dictionary entry i (tools/dictenc.py)
.include "gen.inc"               ; written by tools/insert.py: DICT_TAB (u16 offsets from DICT_BASE), DICT_BASE,
                                 ; DICT_N; HEAP_BASE (MSYS text buffer 0x80141778 grows up to it)

; The heap (0x80146778-0x80186778, base kept at gp+0xCC4) starts right after the MSYS text buffer, which holds
; MSYS subfile 6 (item descriptions) or 7 (magic + skills). insert.py moves grown subfiles to the end of MSYS.DAT
; and raises the heap base past the largest; tools/debug/heapwatch.lua measured the heap's high-water mark.
.org 0x800C1AA8
    lui     v0, hi(HEAP_BASE)
    addiu   v0, v0, lo(HEAP_BASE)
.org 0x800C1AD8
    lui     v0, hi(HEAP_BASE)
    addiu   v0, v0, lo(HEAP_BASE)
.org 0x800C2D58
    lui     v0, hi(HEAP_BASE)
    addiu   v0, v0, lo(HEAP_BASE)

.org 0x8006F3A8
    jal     vwf_std              ; was jal 0x800711E0 (a0 = s6, a1 = s2 + 1, a2 = code)
    nop                          ; was addiu s6, s6, 1
    move    s6, v0               ; was jal WAIT (vwf_draw calls it); delay slot "move a0, zero" stays
.org 0x8006F49C
    jal     vwf_big              ; was jal 0x80071650 (a0 = s6, a1 = s2, a2 = code)
.org 0x8006F4A4
    move    s6, v0               ; was jal WAIT; delay slot "move a0, zero" stays
.org 0x8006F4AC
    nop                          ; was addiu s6, s6, 2

; Dialogue typewriter (gp+0x87E = 1): it prints one code per frame through a 1-column window at the cursor column
; and adds the columns used, so every pair sat in its own 12 px cell (clipped when wider). Take the game's own
; page-at-once path instead (the one it uses when 0x87E = 0): the printer then draws whole lines and the VWF runs
; across them. Text appears a page (or up to the next wait code) at a time. docs/re/text.md "Typewriter".
.org 0x80065444
    b       0x800655C8           ; was bne s0, v1, 0x800655C8 (s0 = gp+0x87E, v1 = 1)
.org 0x800658F0
    b       0x80065A4C           ; was bne s0, v1, 0x80065A4C (second typewriter, same test)

; Message pre-parser (0x800643D0): it walks the text, moving a column s1 by 1 per glyph code (2 at double size),
; wraps at 24 and keeps the text's extent at gp+0x832 / 0x834 (max column of a glyph start), which later becomes
; the printer's width and the canvas size: a line of dictionary codes (wider than one column each) was cut there
; ("I want you to have" for "... have it.", "Oh, Big" for "Oh, Big Brother."). Advance s1 the way the printer's s6
; moves instead, s1 = ceil(x / 12) with x in pixels, and stretch the extent to the glyph's last column (vwf_measure).
.org 0x8006496C
    j       vwf_measure
    ori     v0, zero, 1          ; was j 0x80064FC0 / addiu s1, s1, 1
.org 0x80064AB4
    j       vwf_measure
    ori     v0, zero, 2          ; was j 0x80064FC0 / addiu s1, s1, 2

; MSYS descriptions (items, magic, skills) are Huffman-packed (tools/msyspack.py). The six getters 0x80070EC0..
; 0x80071174 end alike: addu v0, v1, v0 (string pointer); lw ra, 0x14(sp); lw s0, 0x10(sp); jr ra; addiu sp, 0x18.
; Each now jumps to msys_get, which unpacks a pointer into the load buffer to a slot and finishes the epilogue.
.if MSYS_MODEL != 0
.org 0x80070F18
    j       msys_get
    addu    v0, v1, v0
.org 0x80070F84
    j       msys_get
    addu    v0, v1, v0
.org 0x80070FF0
    j       msys_get
    addu    v0, v1, v0
.org 0x800710F4
    j       msys_get
    addu    v0, v1, v0
.org 0x80071160
    j       msys_get
    addu    v0, v1, v0
.org 0x800711CC
    j       msys_get
    addu    v0, v1, v0
.endif

; Place / scene popup (0x8006BA48): its frame is 12 px per code (s4 = code count, used only for that at
; 0x8006BC94); make s4 the text's pixel width and the frame s4 px.
.org 0x8006BBB8
    jal     popup_width          ; a1 = string start (was subu v0, a0, a1 / srl / addu / sra s4, v0, 1)
    nop
    move    s4, v0
    nop
.org 0x8006BCA0
    move    a0, s4               ; was sll a0, v0, 2 (v0 = 3 * s4)

.org FREE_START
; Windows draw interleaved (typewriter text beside a name tag), so the x is kept per canvas: 4 slots of
; (canvas base1, texel x, last col returned, last row), replaced round-robin.
vwf_state:                       ; 0 scale, 4 y0, 8 next slot to replace, 12 -, 16 slots
    .word 1, 0, 0, 0
    .word 0, 0, -1, -1
    .word 0, 0, -1, -1
    .word 0, 0, -1, -1
    .word 0, 0, -1, -1

vwf_std:
    li      a3, 1
    b       vwf_draw
    li      t0, 2
vwf_big:
    li      a3, 2
    li      t0, 6

; a0 col, a1 row, a2 code, a3 scale, t0 y offset in the row. v0 = new col.
vwf_draw:
    addiu   sp, sp, -0x28
    sw      ra, 0x24(sp)
    sw      s0, 0x10(sp)
    sw      s1, 0x14(sp)
    sw      s2, 0x18(sp)
    sw      s3, 0x1C(sp)
    la      s3, vwf_state
    sw      a3, 0(s3)
    sll     t1, a1, 4
    addu    t1, t1, t0
    sw      t1, 4(s3)            ; y0 = row * 16 + offset
    lui     t0, 0x801D
    lw      t9, 0x2808(t0)       ; canvas base1 now
    addiu   t4, s3, 16
    li      t5, 4
@@find:
    lw      t6, 0(t4)
    nop
    beq     t6, t9, @@found
    addiu   t5, t5, -1
    bnez    t5, @@find
    addiu   t4, t4, 16
    lw      t6, 8(s3)            ; no slot for this canvas: take the next one
    nop
    addiu   t7, t6, 1
    andi    t7, t7, 3
    sw      t7, 8(s3)
    sll     t6, t6, 4
    addu    t4, s3, t6
    addiu   t4, t4, 16
    sw      t9, 0(t4)
    b       @@resync
    nop
@@found:
    lw      t1, 8(t4)
    lw      t2, 12(t4)
    lw      s0, 4(t4)
    bne     t1, a0, @@resync
    nop
    beq     t2, a1, @@go
    nop
@@resync:
    sll     s0, a0, 1
    addu    s0, s0, a0
    sll     s0, s0, 2            ; x = col * 12
@@go:
    move    s3, t4               ; this canvas's slot
    move    s1, a1
    move    s2, a2
    li      t0, DICT             ; dictionary code: draw the entry's letter pairs
    sltu    t1, s2, t0
    bnez    t1, @@notdict
    subu    t0, s2, t0
    sltiu   t1, t0, DICT_N
    beqz    t1, @@notdict
    sll     t0, t0, 1
    la      t1, DICT_TAB
    addu    t1, t1, t0
    lhu     t0, 0(t1)
    la      t1, DICT_BASE
    addu    s2, t1, t0           ; s2 = entry (u16 pair codes, 0000 ends)
@@dloop:
    lhu     t0, 0(s2)
    nop
    beqz    t0, @@done
    addiu   s2, s2, 2
    addiu   t0, t0, -PAIR
    sw      t0, 0x20(sp)
    move    a0, s0
    jal     vwf_index
    srl     a2, t0, 7            ; first letter
    move    s0, v0
    lw      t0, 0x20(sp)
    nop
    andi    a2, t0, 0x7F         ; second letter, 0 = none
    beqz    a2, @@dloop
    nop
    jal     vwf_index
    move    a0, s0
    b       @@dloop
    move    s0, v0
@@notdict:
    sltiu   t0, s2, PAIR
    bnez    t0, @@legacy
    nop
    sltiu   t0, s2, PAIR + 0x4000
    beqz    t0, @@legacy
    nop
    addiu   t0, s2, -PAIR
    move    a0, s0
    jal     vwf_index
    srl     a2, t0, 7            ; first letter
    move    s0, v0
    andi    a2, s2, 0x7F         ; second letter, 0 = none
    beqz    a2, @@done
    nop
    jal     vwf_index
    move    a0, s0
    b       @@done
    move    s0, v0
@@legacy:
    lw      t0, 0x9A0(gp)        ; game font base
    sll     t1, s2, 3
    addu    t1, t1, s2
    sll     t1, t1, 1
    addu    a2, t0, t1
    move    a0, s0
    jal     vwf_glyph
    li      a3, 12
    move    s0, v0
@@done:
    addiu   t0, s0, 11
    li      t1, 12
    divu    t0, t1
    mflo    s2                   ; col = ceil(x / 12)
    sw      s0, 4(s3)
    sw      s2, 8(s3)
    sw      s1, 12(s3)
    jal     WAIT
    move    a0, zero
    move    v0, s2
    lw      ra, 0x24(sp)
    lw      s0, 0x10(sp)
    lw      s1, 0x14(sp)
    lw      s2, 0x18(sp)
    lw      s3, 0x1C(sp)
    jr      ra
    addiu   sp, sp, 0x28

; vwf_glyph for charset index a2 at texel a0. v0 = new texel x.
vwf_index:
    la      t0, en_widths
    addu    t0, t0, a2
    lbu     a3, 0(t0)
    sll     t1, a2, 3
    addu    t1, t1, a2
    sll     t1, t1, 1
    la      a2, en_glyphs
    j       vwf_glyph
    addu    a2, a2, t1

; Draw one 12x12 1bpp glyph (18 bytes, rows MSB-first) at texel a0, font columns 0..a3-1, scaled by
; vwf_state.scale (1 or 2) from canvas row vwf_state.y0, with the game's drop shadow (colour 5 below and
; below-right of ink). v0 = a0 + a3 * scale.
; Registers: a0 x, a2 src, a3 columns, t0 canvas struct, t2 split texel S, t3 colour, t8 y0, t9 previous row,
; v1 row, t4 row bits, t5 shadow bits, s0/s1 canvas 1 row + stride, s2/s3 canvas 2 row + stride, s4 scale,
; s5 sub-column, s6 column, s7 column mask, fp texel x of the column.
vwf_glyph:
    addiu   sp, sp, -0x28
    sw      s0, 0x00(sp)
    sw      s1, 0x04(sp)
    sw      s2, 0x08(sp)
    sw      s3, 0x0C(sp)
    sw      s4, 0x10(sp)
    sw      s5, 0x14(sp)
    sw      s6, 0x18(sp)
    sw      s7, 0x1C(sp)
    sw      fp, 0x20(sp)
    la      t0, vwf_state
    lw      s4, 0(t0)            ; scale
    lw      t8, 4(t0)            ; y0
    lui     t0, 0x801D
    addiu   t0, t0, 0x2808       ; canvas struct
    lw      t1, 8(t0)            ; split column
    lbu     t3, 0x99C(gp)        ; text colour
    sll     t2, t1, 1
    addu    t2, t2, t1
    sll     t2, t2, 2            ; S = split * 12 texels
    andi    t3, t3, 0xF
    move    v1, zero             ; glyph row r = 0..12 (12 = shadow only)
    move    t9, zero             ; previous row bits
@@row:
    move    t4, zero
    sltiu   t5, v1, 12
    beqz    t5, @@have
    sll     t5, v1, 1
    addu    t5, t5, v1
    srl     t6, t5, 1            ; byte = 12r / 8
    addu    t6, a2, t6
    lbu     t4, 0(t6)
    lbu     t7, 1(t6)
    andi    t5, v1, 1
    bnez    t5, @@odd
    nop
    sll     t4, t4, 4
    b       @@cmb
    srl     t7, t7, 4
@@odd:
    andi    t4, t4, 0xF
    sll     t4, t4, 8
@@cmb:
    or      t4, t4, t7
    sll     t4, t4, 4            ; bit 15 = column 0
@@have:
    srl     t5, t9, 1
    or      t5, t5, t9
    nor     t6, t4, zero
    and     t5, t5, t6           ; shadow = (prev | prev >> 1) & ~cur
    move    t9, t4
    or      t6, t4, t5
    beqz    t6, @@next
    nop
    mult    v1, s4
    lw      s1, 4(t0)            ; stride1
    lw      s3, 0x14(t0)         ; stride2
    mflo    t6
    addu    t6, t6, t8           ; canvas y = y0 + r * scale
    nop
    mult    t6, s1
    lw      s0, 0(t0)
    lw      s2, 0x10(t0)
    mflo    t7
    addu    s0, s0, t7           ; canvas 1 row
    nop
    mult    t6, s3
    mflo    t7
    addu    s2, s2, t7           ; canvas 2 row (its texel 0 = S)
    move    s6, zero             ; font column
    ori     s7, zero, 0x8000     ; column mask
@@px:
    and     t6, t4, s7
    bnez    t6, @@put
    move    t7, t3               ; ink
    and     t6, t5, s7
    beqz    t6, @@pnext
    nop
    li      t7, 5                ; shadow
@@put:
    mult    s6, s4
    move    s5, zero
    mflo    fp
    addu    fp, fp, a0           ; texel x of this font column
@@sub:
    addu    t1, fp, s5           ; X
    andi    a1, t1, 1
    sll     a1, a1, 2            ; nibble shift: odd texel = high nibble
    sltu    t6, t1, t2
    beqz    t6, @@c2
    nop
    srl     t1, t1, 1
    addu    t1, t1, s0           ; byte in canvas 1
    b       @@rmw
    move    v0, s1
@@c2:
    subu    t1, t1, t2
    srl     t1, t1, 1
    addu    t1, t1, s2           ; byte in canvas 2
    move    v0, s3
@@rmw:
    li      t6, 0xF
    sllv    t6, t6, a1
    nor     t6, t6, zero         ; keep mask
    sllv    a1, t7, a1           ; value in place
    lbu     at, 0(t1)
    nop
    and     at, at, t6
    or      at, at, a1
    sb      at, 0(t1)
    addiu   at, s4, -1
    beqz    at, @@subnext        ; scale 1: one canvas row
    addu    t1, t1, v0
    lbu     at, 0(t1)            ; scale 2: the row below too
    nop
    and     at, at, t6
    or      at, at, a1
    sb      at, 0(t1)
@@subnext:
    addiu   s5, s5, 1
    sltu    t6, s5, s4
    bnez    t6, @@sub
    nop
@@pnext:
    addiu   s6, s6, 1
    sltu    t6, s6, a3
    bnez    t6, @@px
    srl     s7, s7, 1
@@next:
    addiu   v1, v1, 1
    sltiu   t6, v1, 13
    bnez    t6, @@row
    nop
    mult    a3, s4
    lw      s0, 0x00(sp)
    lw      s1, 0x04(sp)
    lw      s2, 0x08(sp)
    lw      s3, 0x0C(sp)
    lw      s4, 0x10(sp)
    lw      s5, 0x14(sp)
    lw      s6, 0x18(sp)
    lw      s7, 0x1C(sp)
    lw      fp, 0x20(sp)
    mflo    v0
    addu    v0, v0, a0
    jr      ra
    addiu   sp, sp, 0x28

; vwf_measure: pre-parser glyph step (v0 = scale, s2 = just past the code, s1 = its column). Keeps (x, col) like
; vwf_state: x resyncs to s1 * 12 when the parser moved s1 itself (new line, indent). Continues at 0x80064FC0.
vwf_measure:
    lhu     a0, -2(s2)
    jal     vwf_width            ; ra is not live here (the parser reloads it from its frame)
    move    t3, v0
    multu   v0, t3
    la      t4, vwf_mstate
    lw      t5, 0(t4)            ; x
    lw      t6, 4(t4)            ; the column that x belongs to
    mflo    v0                   ; advance in texels
    beq     t6, s1, @@go
    nop
    sll     t5, s1, 1
    addu    t5, t5, s1
    sll     t5, t5, 2            ; x = s1 * 12
@@go:
    addu    t5, t5, v0
    addiu   t6, t5, 11
    li      t7, 12
    divu    t6, t7
    mflo    s1                   ; s1 = ceil(x / 12)
    sw      t5, 0(t4)
    sw      s1, 4(t4)
    lh      t6, 0x832(gp)        ; the extent holds the glyph's first column; a wide code reaches column s1 - 1
    addiu   t7, s1, -1
    slt     t8, t6, t7
    beqz    t8, @@done
    nop
    sh      t7, 0x832(gp)
@@done:
    j       0x80064FC0
    nop

; vwf_width: a0 = glyph code; v0 = advance in font pixels as vwf_draw draws it (pairs and dictionary entries from
; en_widths, game glyphs 12). Uses t7-t9, v1 only.
vwf_width:
    beqz    a0, @@ret
    ori     v0, zero, 12
    move    v0, zero
    li      t7, DICT
    sltu    t8, a0, t7
    bnez    t8, @@one
    subu    t8, a0, t7
    sltiu   t9, t8, DICT_N
    beqz    t9, @@one
    sll     t8, t8, 1
    la      t9, DICT_TAB
    addu    t9, t9, t8
    lhu     t8, 0(t9)
    la      t9, DICT_BASE
    b       @@loop
    addu    t9, t9, t8           ; entry: pair codes, 0000 ends
@@one:
    la      t9, vwf_wtmp
    sh      a0, 0(t9)
    sh      zero, 2(t9)
@@loop:
    lhu     t8, 0(t9)
    nop
    beqz    t8, @@ret
    addiu   t9, t9, 2
    sltiu   t7, t8, PAIR
    bnez    t7, @@game
    sltiu   t7, t8, PAIR + 0x4000
    beqz    t7, @@game
    addiu   t8, t8, -PAIR
    srl     t7, t8, 7
    la      v1, en_widths
    addu    t7, v1, t7
    lbu     t7, 0(t7)
    andi    t8, t8, 0x7F
    addu    v0, v0, t7
    beqz    t8, @@loop           ; no second letter
    addu    t8, v1, t8
    lbu     t8, 0(t8)
    b       @@loop
    addu    v0, v0, t8
@@game:
    b       @@loop
    addiu   v0, v0, 12
@@ret:
    jr      ra
    nop

; popup_width: v0 = pixel width of the string at a1 (FFFF ends). Uses a0, v1, t3-t9.
popup_width:
    move    t5, a1
    move    t6, ra
    move    t4, zero
    ori     t3, zero, 0xFFFF
@@next:
    lhu     a0, 0(t5)
    nop
    beq     a0, t3, @@end
    addiu   t5, t5, 2
    jal     vwf_width
    nop
    b       @@next
    addu    t4, t4, v0
@@end:
    jr      t6
    move    v0, t4

.align 4
vwf_mstate:                      ; x, col
    .word 0, -1
vwf_wtmp:
    .halfword 0, 0

; msys_get: v0 = string pointer from a description getter (its frame: ra at 0x14(sp), s0 at 0x10(sp)). A pointer
; into the MSYS load buffer is unpacked into one of MSYS_NSLOT slots above the loaded subfile; the cache (key =
; pointer ^ loaded subfile gp+0x52E << 24, slot) returns the same slot while the string is in use. Other pointers
; (the EXE fallback string) pass through.
msys_get:
    lui     t0, 0x8014
    addiu   t0, t0, 0x1778       ; MSYS load buffer
    subu    t0, v0, t0
    sltiu   t0, t0, 0x5000
    beqz    t0, @@ret
    nop
    lbu     t1, 0x52E(gp)
    nop
    sll     t1, t1, 24
    xor     t1, t1, v0           ; key
    la      t2, msys_cache
    addiu   t3, t2, 8 * MSYS_NSLOT
@@look:
    lw      t4, 0(t2)
    nop
    beq     t4, t1, @@hit
    nop
    addiu   t2, t2, 8
    bne     t2, t3, @@look
    nop
    la      t2, msys_next        ; miss: take the next slot round-robin
    lw      t3, 0(t2)
    nop
    addiu   t4, t3, 1
    andi    t4, t4, MSYS_NSLOT - 1
    sw      t4, 0(t2)
    li      t4, MSYS_SLOT
    multu   t3, t4
    sll     t3, t3, 3
    la      t2, msys_cache
    addu    t2, t2, t3
    mflo    t4
    la      a1, MSYS_SCRATCH
    addu    a1, a1, t4           ; slot
    sw      t1, 0(t2)
    sw      a1, 4(t2)
    jal     msys_unpack          ; ra is reloaded from the getter's frame below
    move    a0, v0
    b       @@ret
    nop
@@hit:
    lw      v0, 4(t2)
@@ret:
    lw      ra, 0x14(sp)
    lw      s0, 0x10(sp)
    jr      ra
    addiu   sp, sp, 0x18

; msys_unpack: a0 = packed string, a1 = slot; v0 = slot. Mirrors msyspack.unpack(): canonical Huffman codes (MSB
; first), symbols expanded through the model's (L, R) table with a stack, letters paired like enfont.EnCodec.
; A full slot or a bad code ends the string with FFFF. Uses only a0-a3, t0-t9, v0, v1.
msys_unpack:
    move    t8, a1
    la      t9, MSYS_MODEL
    lhu     t7, 0(t9)            ; maxlen
    addiu   t9, t9, 2            ; counts[]
    sll     t7, t7, 1
    addu    t7, t7, t9           ; symbol table (right after counts[])
    move    a2, zero             ; pending letter
    move    a3, zero             ; bit mask (0: fetch a byte)
    addiu   v1, a1, MSYS_SLOT - 8 ; write limit
@@sym:
    move    t0, zero             ; code
    move    t1, zero             ; first
    move    t2, zero             ; index
    move    t3, t9               ; &counts[len - 1]
@@bit:
    bnez    a3, @@take
    nop
    lbu     t6, 0(a0)
    addiu   a0, a0, 1
    li      a3, 0x80
@@take:
    and     t5, t6, a3
    sltu    t5, zero, t5
    srl     a3, a3, 1
    or      t0, t0, t5           ; code |= bit
    lhu     t5, 0(t3)            ; count of this length
    addiu   t3, t3, 2
    subu    t4, t0, t1
    sltu    t4, t4, t5
    bnez    t4, @@found          ; code - first < count
    nop
    addu    t2, t2, t5           ; index += count
    addu    t1, t1, t5
    sll     t1, t1, 1            ; first = (first + count) << 1
    bne     t3, t7, @@bit
    sll     t0, t0, 1
    b       @@cut                ; no length matched: bad data
    nop
@@found:
    subu    t0, t0, t1
    addu    t0, t0, t2           ; symbol = index + code - first
    la      t1, msys_stack
    sh      t0, 0(t1)
    addiu   t2, t1, 2
@@pop:
    beq     t2, t1, @@sym
    nop
    addiu   t2, t2, -2
    lhu     t0, 0(t2)
    nop
    sll     t3, t0, 2
    addu    t3, t3, t7
    lhu     t4, 0(t3)            ; L
    lhu     t5, 2(t3)            ; R
    ori     v0, zero, 0xFFFF
    beq     t5, v0, @@leaf
    nop
    sh      t5, 0(t2)            ; push R, then L on top
    sh      t4, 2(t2)
    b       @@pop
    addiu   t2, t2, 4
@@leaf:
    beqz    t4, @@end            ; END
    sltiu   v0, t4, 0x80
    beqz    v0, @@raw
    nop
    bnez    a2, @@pair
    nop
    b       @@pop
    move    a2, t4               ; first letter of a pair
@@pair:
    sll     t5, a2, 7
    addu    t5, t5, t4
    addiu   t5, t5, PAIR
    move    a2, zero
@@put:
    sltu    v0, a1, v1
    beqz    v0, @@cut
    nop
    sh      t5, 0(a1)
    b       @@pop
    addiu   a1, a1, 2
@@raw:
    beqz    a2, @@put
    move    t5, t4
    sll     v0, a2, 7
    addiu   v0, v0, PAIR
    sh      v0, 0(a1)            ; the odd letter before a raw word
    addiu   a1, a1, 2
    b       @@put
    move    a2, zero
@@cut:
    b       @@fin
    ori     v0, zero, 1
@@end:
    move    v0, zero
@@fin:
    beqz    a2, @@fin2
    sll     t5, a2, 7
    addiu   t5, t5, PAIR
    sh      t5, 0(a1)
    addiu   a1, a1, 2
@@fin2:
    beqz    v0, @@done
    ori     t5, zero, 0xFFFF
    sh      t5, 0(a1)
@@done:
    jr      ra
    move    v0, t8

.align 4
msys_next:
    .word 0
msys_cache:                      ; MSYS_NSLOT x (key, slot)
    .fill 8 * MSYS_NSLOT, 0
msys_stack:                      ; msyspack.DEPTH + 1 entries at most
    .fill 64, 0

.align 4
en_widths:
    .incbin "en_widths.bin"
en_glyphs:
    .incbin "en_glyphs.bin"

.if org() > FREE_END
    .error "vwf.asm overruns the font"
.endif

.close
