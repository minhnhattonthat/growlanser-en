; vwf.asm: proportional English text for Growlanser (armips, applied by tools/insert.py to SLPS_023.80).
;
; The text printer (0x8006E794) draws into a 4bpp RAM canvas (struct 0x801D2808: base1, stride1, split, -, base2,
; stride2; texels from split*12 on go to canvas 2, low nibble = left texel). Two glyph routines read the font:
;   0x800711E0 (col, row+1, code): normal text, 1 texel per font pixel, 1 canvas row per font row, y = row*16+2,
;                                  x = col*12 texels; the printer then adds 1 to its column s6. (jal 0x8006F3A8)
;   0x80071650 (col, row, code):   double size, 2x2 texels per font pixel, y = row*16+6, x = col*12 texels;
;                                  the printer adds 2. (jal 0x8006F49C)
; vwf_std / vwf_big replace those calls. They keep their own texel x, draw pair codes (tools/enfont.py) as two
; proportional glyphs and game glyphs 12 px wide, and return the column ceil(x / 12), which the printer stores in
; s6. The texel x resyncs to col*12 whenever the printer moves (new line, page, window, indent).
; Code and data live in the font's last kanji cells (0x6A0-0x7CA), unused once the script is English.
; Tested under unicorn: tests/test_vwf.py (tools/vwfemu.py).

.psx
.open "SLPS_023.80", 0x8000F800

WAIT       equ 0x80069D64        ; called by the printer after each glyph
PAIR       equ 0x0800
FREE_START equ 0x800FF508        ; font cell 0x6A0
FREE_END   equ 0x80100A0E        ; end of the font (cell 0x7CB)

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

.org FREE_START
vwf_state:                       ; 0 texel x, 4 last col returned, 8 last row, 12 canvas base1, 16 scale, 20 y0
    .word 0, -1, -1, 0, 1, 0

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
    sw      a3, 16(s3)
    sll     t1, a1, 4
    addu    t1, t1, t0
    sw      t1, 20(s3)           ; y0 = row * 16 + offset
    lui     t0, 0x801D
    lw      t9, 0x2808(t0)       ; canvas base1 now
    lw      t1, 4(s3)
    lw      t2, 8(s3)
    lw      t3, 12(s3)
    lw      s0, 0(s3)
    bne     t1, a0, @@resync
    nop
    bne     t2, a1, @@resync
    nop
    beq     t3, t9, @@go
    nop
@@resync:
    sll     s0, a0, 1
    addu    s0, s0, a0
    sll     s0, s0, 2            ; x = col * 12
@@go:
    sw      t9, 12(s3)
    move    s1, a1
    move    s2, a2
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
    sw      s0, 0(s3)
    sw      s2, 4(s3)
    sw      s1, 8(s3)
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
    lw      s4, 16(t0)           ; scale
    lw      t8, 20(t0)           ; y0
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

.align 4
en_widths:
    .incbin "en_widths.bin"
en_glyphs:
    .incbin "en_glyphs.bin"

.if org() > FREE_END
    .error "vwf.asm overruns the font"
.endif

.close
