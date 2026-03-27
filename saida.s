.global _start
.section .data
.balign 8
last_result: .double 0.0
.balign 8
results: .space 112
.balign 4
display_lut: .word 0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07, 0x7F, 0x6F, 0x77, 0x7C, 0x39, 0x5E, 0x79, 0x71
.balign 8
.balign 8
const_0: .double -5.5
.balign 8
const_1: .double -2.0
.balign 8
const_2: .double 11.0
.balign 8
var_X: .double 0.0
.balign 8
const_3: .double -10.0
.balign 8
var_Y: .double 0.0
.balign 8
const_4: .double 2.0
.balign 8
const_5: .double 1.0
.balign 8
const_6: .double 3.0
.balign 8
const_7: .double 4.0
.balign 8
const_8: .double 10.0
.balign 8
const_9: .double 5.0
.balign 8
var_Z: .double 0.0
.balign 8
const_10: .double 123.456
.balign 8
var_ULTIMO: .double 0.0

.section .text
.global _start
_start:
    @ --- Habilitar FPU (FPEXC.EN = 1) ---
    mrc p15, 0, r0, c1, c0, 2
    orr r0, r0, #0xF00000
    mcr p15, 0, r0, c1, c0, 2
    isb
    mov r0, #0x40000000
    vmsr fpexc, r0
    @ -----------------------------------------
    @ Salva SP base para restaurar entre linhas
    mov r7, sp
    @ Carrega endereços fixos uma única vez (evita literal pool overflow)
    ldr r10, =last_result   @ r10 = &last_result (fixo durante toda execução)
    ldr r11, =results       @ r11 = &results[0]  (fixo durante toda execução)

    @ ---- linha 1 ----
    mov sp, r7
    ldr r0, =const_0
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    ldr r0, =const_1
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vmul.f64 d2, d0, d1
    vpush.f64 {d2}
    vpop.f64 {d0}
    vstr.f64 d0, [r10]
    vstr.f64 d0, [r11]
    dsb

    @ ---- linha 2 ----
    mov sp, r7
    ldr r0, =const_2
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    vpop.f64 {d0}
    ldr r6, =var_X
    vstr.f64 d0, [r6]
    vpush.f64 {d0}
    vpop.f64 {d0}
    vstr.f64 d0, [r10]
    add r12, r11, #8
    vstr.f64 d0, [r12]
    dsb

    @ ---- linha 3 ----
    mov sp, r7
    ldr r0, =const_3
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    vpop.f64 {d0}
    ldr r6, =var_Y
    vstr.f64 d0, [r6]
    vpush.f64 {d0}
    vpop.f64 {d0}
    vstr.f64 d0, [r10]
    add r12, r11, #16
    vstr.f64 d0, [r12]
    dsb

    @ ---- linha 4 ----
    mov sp, r7
    ldr r6, =var_X
    vldr.f64 d0, [r6]
    vpush.f64 {d0}
    ldr r6, =var_Y
    vldr.f64 d0, [r6]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vsub.f64 d2, d0, d1
    vpush.f64 {d2}
    ldr r0, =const_4
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vcvtr.s32.f64 s4, d1
    vmov r9, s4
    ldr r0, =const_5
    vldr.f64 d2, [r0]
    cmp r9, #0
    beq pow_done_1
pow_loop_0:
    vmul.f64 d2, d2, d0
    subs r9, r9, #1
    bne pow_loop_0
pow_done_1:
    vpush.f64 {d2}
    vpop.f64 {d0}
    vstr.f64 d0, [r10]
    add r12, r11, #24
    vstr.f64 d0, [r12]
    dsb

    @ ---- linha 5 ----
    mov sp, r7
    ldr r0, =const_4
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    ldr r0, =const_6
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vcvtr.s32.f64 s4, d1
    vmov r9, s4
    ldr r0, =const_5
    vldr.f64 d2, [r0]
    cmp r9, #0
    beq pow_done_3
pow_loop_2:
    vmul.f64 d2, d2, d0
    subs r9, r9, #1
    bne pow_loop_2
pow_done_3:
    vpush.f64 {d2}
    ldr r0, =const_7
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    ldr r0, =const_4
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vmul.f64 d2, d0, d1
    vpush.f64 {d2}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vadd.f64 d2, d0, d1
    vpush.f64 {d2}
    ldr r0, =const_8
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    ldr r0, =const_6
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vdiv.f64 d2, d0, d1
    vcvtr.s32.f64 s4, d2
    vcvt.f64.s32 d2, s4
    vpush.f64 {d2}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vmul.f64 d2, d0, d1
    vpush.f64 {d2}
    ldr r0, =const_9
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vdiv.f64 d2, d0, d1
    vcvtr.s32.f64 s4, d2
    vcvt.f64.s32 d2, s4
    vmul.f64 d3, d2, d1
    vsub.f64 d2, d0, d3
    vpush.f64 {d2}
    vpop.f64 {d0}
    vstr.f64 d0, [r10]
    add r12, r11, #32
    vstr.f64 d0, [r12]
    dsb

    @ ---- linha 6 ----
    mov sp, r7
    ldr r0, =const_6
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    vpop.f64 {d0}
    ldr r6, =var_Z
    vstr.f64 d0, [r6]
    vpush.f64 {d0}
    vpop.f64 {d0}
    vstr.f64 d0, [r10]
    add r12, r11, #40
    vstr.f64 d0, [r12]
    dsb

    @ ---- linha 7 ----
    mov sp, r7
    ldr r0, =const_5
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    @ --- COMANDO RES DINÂMICO ---
    vpop.f64 {d0}
    vcvtr.s32.f64 s0, d0
    vmov r1, s0
    mov r2, #6
    subs r3, r2, r1
    cmp r3, #0
    movlt r3, #0
    add r4, r11, r3, lsl #3
    vldr.f64 d0, [r4]
    vpush.f64 {d0}
    ldr r6, =var_Z
    vldr.f64 d0, [r6]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vadd.f64 d2, d0, d1
    vpush.f64 {d2}
    vpop.f64 {d0}
    vstr.f64 d0, [r10]
    add r12, r11, #48
    vstr.f64 d0, [r12]
    dsb

    @ ---- linha 8 ----
    mov sp, r7
    ldr r0, =const_4
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    @ --- COMANDO RES DINÂMICO ---
    vpop.f64 {d0}
    vcvtr.s32.f64 s0, d0
    vmov r1, s0
    mov r2, #7
    subs r3, r2, r1
    cmp r3, #0
    movlt r3, #0
    add r4, r11, r3, lsl #3
    vldr.f64 d0, [r4]
    vpush.f64 {d0}
    ldr r6, =var_X
    vldr.f64 d0, [r6]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vdiv.f64 d2, d0, d1
    vpush.f64 {d2}
    vpop.f64 {d0}
    vstr.f64 d0, [r10]
    add r12, r11, #56
    vstr.f64 d0, [r12]
    dsb

    @ ---- linha 9 ----
    mov sp, r7
    ldr r0, =const_8
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    ldr r0, =const_4
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vmul.f64 d2, d0, d1
    vpush.f64 {d2}
    ldr r0, =const_9
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    ldr r0, =const_5
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vadd.f64 d2, d0, d1
    vpush.f64 {d2}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vsub.f64 d2, d0, d1
    vpush.f64 {d2}
    ldr r0, =const_4
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vcvtr.s32.f64 s4, d1
    vmov r9, s4
    ldr r0, =const_5
    vldr.f64 d2, [r0]
    cmp r9, #0
    beq pow_done_5
pow_loop_4:
    vmul.f64 d2, d2, d0
    subs r9, r9, #1
    bne pow_loop_4
pow_done_5:
    vpush.f64 {d2}
    ldr r0, =const_6
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vdiv.f64 d2, d0, d1
    vcvtr.s32.f64 s4, d2
    vcvt.f64.s32 d2, s4
    vpush.f64 {d2}
    vpop.f64 {d0}
    vstr.f64 d0, [r10]
    add r12, r11, #64
    vstr.f64 d0, [r12]
    dsb

    @ ---- linha 10 ----
    mov sp, r7
    ldr r6, =var_X
    vldr.f64 d0, [r6]
    vpush.f64 {d0}
    ldr r6, =var_Y
    vldr.f64 d0, [r6]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vmul.f64 d2, d0, d1
    vpush.f64 {d2}
    ldr r6, =var_Z
    vldr.f64 d0, [r6]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vdiv.f64 d2, d0, d1
    vcvtr.s32.f64 s4, d2
    vcvt.f64.s32 d2, s4
    vpush.f64 {d2}
    vpop.f64 {d0}
    vstr.f64 d0, [r10]
    add r12, r11, #72
    vstr.f64 d0, [r12]
    dsb

    @ ---- linha 11 ----
    mov sp, r7
    ldr r0, =const_10
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    vpop.f64 {d0}
    ldr r6, =var_ULTIMO
    vstr.f64 d0, [r6]
    vpush.f64 {d0}
    vpop.f64 {d0}
    vstr.f64 d0, [r10]
    add r12, r11, #80
    vstr.f64 d0, [r12]
    dsb

    @ ---- linha 12 ----
    mov sp, r7
    ldr r0, =const_7
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    @ --- COMANDO RES DINÂMICO ---
    vpop.f64 {d0}
    vcvtr.s32.f64 s0, d0
    vmov r1, s0
    mov r2, #11
    subs r3, r2, r1
    cmp r3, #0
    movlt r3, #0
    add r4, r11, r3, lsl #3
    vldr.f64 d0, [r4]
    vpush.f64 {d0}
    ldr r6, =var_ULTIMO
    vldr.f64 d0, [r6]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vadd.f64 d2, d0, d1
    vpush.f64 {d2}
    ldr r0, =const_5
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    @ --- COMANDO RES DINÂMICO ---
    vpop.f64 {d0}
    vcvtr.s32.f64 s0, d0
    vmov r1, s0
    mov r2, #11
    subs r3, r2, r1
    cmp r3, #0
    movlt r3, #0
    add r4, r11, r3, lsl #3
    vldr.f64 d0, [r4]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vsub.f64 d2, d0, d1
    vpush.f64 {d2}
    vpop.f64 {d0}
    vstr.f64 d0, [r10]
    add r12, r11, #88
    vstr.f64 d0, [r12]
    dsb

    @ ---- linha 13 ----
    mov sp, r7
    ldr r0, =const_8
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    @ --- COMANDO RES DINÂMICO ---
    vpop.f64 {d0}
    vcvtr.s32.f64 s0, d0
    vmov r1, s0
    mov r2, #12
    subs r3, r2, r1
    cmp r3, #0
    movlt r3, #0
    add r4, r11, r3, lsl #3
    vldr.f64 d0, [r4]
    vpush.f64 {d0}
    vpop.f64 {d0}
    vstr.f64 d0, [r10]
    add r12, r11, #96
    vstr.f64 d0, [r12]
    dsb

    @ ---- linha 14 ----
    mov sp, r7
    ldr r6, =var_ULTIMO
    vldr.f64 d0, [r6]
    vpush.f64 {d0}
    ldr r0, =const_4
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vdiv.f64 d2, d0, d1
    vpush.f64 {d2}
    ldr r0, =const_9
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vdiv.f64 d2, d0, d1
    vcvtr.s32.f64 s4, d2
    vcvt.f64.s32 d2, s4
    vmul.f64 d3, d2, d1
    vsub.f64 d2, d0, d3
    vpush.f64 {d2}
    ldr r0, =const_4
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vcvtr.s32.f64 s4, d1
    vmov r9, s4
    ldr r0, =const_5
    vldr.f64 d2, [r0]
    cmp r9, #0
    beq pow_done_7
pow_loop_6:
    vmul.f64 d2, d2, d0
    subs r9, r9, #1
    bne pow_loop_6
pow_done_7:
    vpush.f64 {d2}
    vpop.f64 {d0}
    vstr.f64 d0, [r10]
    add r12, r11, #104
    vstr.f64 d0, [r12]
    dsb

    @ --- DECODIFICADOR PARA 4 DISPLAYS ---
    vldr.f64 d0, [r10]
    vcvt.s32.f64 s0, d0
    vmov r1, s0
    ldr r2, =0xFF200020
    ldr r3, =display_lut
    mov r4, #0

    @ HEX0 (unidades)
    and r6, r1, #0xF
    ldr r5, [r3, r6, lsl #2]
    orr r4, r4, r5

    @ HEX1 (dezenas)
    lsr r1, r1, #4
    and r6, r1, #0xF
    ldr r5, [r3, r6, lsl #2]
    lsl r5, r5, #8
    orr r4, r4, r5

    @ HEX2 (centenas)
    lsr r1, r1, #4
    and r6, r1, #0xF
    ldr r5, [r3, r6, lsl #2]
    lsl r5, r5, #16
    orr r4, r4, r5

    @ HEX3 (milhares)
    lsr r1, r1, #4
    and r6, r1, #0xF
    ldr r5, [r3, r6, lsl #2]
    lsl r5, r5, #24
    orr r4, r4, r5

    str r4, [r2]

fim:
    bkpt
