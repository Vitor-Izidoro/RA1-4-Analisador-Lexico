.global _start
.section .data
.balign 8
last_result: .double 0.0
.balign 8
results: .space 56
.balign 4
display_lut: .word 0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07, 0x7F, 0x6F, 0x77, 0x7C, 0x39, 0x5E, 0x79, 0x71
.balign 8
.balign 8
const_0: .double 10.0
.balign 8
const_1: .double 3.0
.balign 8
const_2: .double 1.0
.balign 8
var_BASE: .double 0.0
.balign 8
const_3: .double 25.0
.balign 8
const_4: .double 4.0
.balign 8
const_5: .double 2.0
.balign 8
const_6: .double 400.0
.balign 8
var_PULO: .double 0.0
.balign 8
const_7: .double 5.0
.balign 8
const_8: .double 5000.0
.balign 8
const_9: .double 1966.0
.balign 8
var_BATATA: .double 0.0

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
    vcvtr.s32.f64 s4, d1
    vmov r9, s4
    ldr r0, =const_2
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
    ldr r6, =var_BASE
    vstr.f64 d0, [r6]
    vpush.f64 {d0}
    vpop.f64 {d0}
    vstr.f64 d0, [r10]
    vstr.f64 d0, [r11]
    dsb

    @ ---- linha 2 ----
    mov sp, r7
    ldr r0, =const_3
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    ldr r0, =const_4
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vdiv.f64 d2, d0, d1
    vcvtr.s32.f64 s4, d2
    vcvt.f64.s32 d2, s4
    vpush.f64 {d2}
    ldr r0, =const_3
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    ldr r0, =const_4
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
    vpop.f64 {d1}
    vpop.f64 {d0}
    vmul.f64 d2, d0, d1
    vpush.f64 {d2}
    vpop.f64 {d0}
    vstr.f64 d0, [r10]
    add r12, r11, #8
    vstr.f64 d0, [r12]
    dsb

    @ ---- linha 3 ----
    mov sp, r7
    ldr r6, =var_BASE
    vldr.f64 d0, [r6]
    vpush.f64 {d0}
    ldr r0, =const_5
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vdiv.f64 d2, d0, d1
    vpush.f64 {d2}
    ldr r0, =const_6
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vsub.f64 d2, d0, d1
    vpush.f64 {d2}
    vpop.f64 {d0}
    vstr.f64 d0, [r10]
    add r12, r11, #16
    vstr.f64 d0, [r12]
    dsb

    @ ---- linha 4 ----
    mov sp, r7
    ldr r0, =const_5
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    vpop.f64 {d0}
    ldr r6, =var_PULO
    vstr.f64 d0, [r6]
    vpush.f64 {d0}
    vpop.f64 {d0}
    vstr.f64 d0, [r10]
    add r12, r11, #24
    vstr.f64 d0, [r12]
    dsb

    @ ---- linha 5 ----
    mov sp, r7
    ldr r6, =var_PULO
    vldr.f64 d0, [r6]
    vpush.f64 {d0}
    @ --- COMANDO RES DINÂMICO ---
    vpop.f64 {d0}                @ Desempilha N (f64) para d0
    vcvtr.s32.f64 s0, d0         @ Converte N para inteiro (s32) em s0
    vmov r1, s0                  @ Move o N inteiro para r1
    mov r2, #4         @ r2 = índice da linha atual
    subs r3, r2, r1              @ r3 = linha_atual - N
    @ Limita a 0 caso r3 < 0 para evitar segmentation fault
    cmp r3, #0
    movlt r3, #0
    @ Calcula o endereço usando r11 (base de results)
    add r4, r11, r3, lsl #3      @ r4 = results + (r3 * 8 bytes)
    vldr.f64 d0, [r4]            @ Carrega o resultado antigo para d0
    vpush.f64 {d0}               @ Empilha o resultado recuperado
    vpop.f64 {d0}
    vstr.f64 d0, [r10]
    add r12, r11, #32
    vstr.f64 d0, [r12]
    dsb

    @ ---- linha 6 ----
    mov sp, r7
    ldr r0, =const_2
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    @ --- COMANDO RES DINÂMICO ---
    vpop.f64 {d0}                @ Desempilha N (f64) para d0
    vcvtr.s32.f64 s0, d0         @ Converte N para inteiro (s32) em s0
    vmov r1, s0                  @ Move o N inteiro para r1
    mov r2, #5         @ r2 = índice da linha atual
    subs r3, r2, r1              @ r3 = linha_atual - N
    @ Limita a 0 caso r3 < 0 para evitar segmentation fault
    cmp r3, #0
    movlt r3, #0
    @ Calcula o endereço usando r11 (base de results)
    add r4, r11, r3, lsl #3      @ r4 = results + (r3 * 8 bytes)
    vldr.f64 d0, [r4]            @ Carrega o resultado antigo para d0
    vpush.f64 {d0}               @ Empilha o resultado recuperado
    ldr r0, =const_7
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vadd.f64 d2, d0, d1
    vpush.f64 {d2}
    ldr r0, =const_0
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
    add r12, r11, #40
    vstr.f64 d0, [r12]
    dsb

    @ ---- linha 7 ----
    mov sp, r7
    ldr r0, =const_2
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    @ --- COMANDO RES DINÂMICO ---
    vpop.f64 {d0}                @ Desempilha N (f64) para d0
    vcvtr.s32.f64 s0, d0         @ Converte N para inteiro (s32) em s0
    vmov r1, s0                  @ Move o N inteiro para r1
    mov r2, #6         @ r2 = índice da linha atual
    subs r3, r2, r1              @ r3 = linha_atual - N
    @ Limita a 0 caso r3 < 0 para evitar segmentation fault
    cmp r3, #0
    movlt r3, #0
    @ Calcula o endereço usando r11 (base de results)
    add r4, r11, r3, lsl #3      @ r4 = results + (r3 * 8 bytes)
    vldr.f64 d0, [r4]            @ Carrega o resultado antigo para d0
    vpush.f64 {d0}               @ Empilha o resultado recuperado
    ldr r0, =const_8
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vmul.f64 d2, d0, d1
    vpush.f64 {d2}
    ldr r0, =const_9
    vldr.f64 d0, [r0]
    vpush.f64 {d0}
    vpop.f64 {d1}
    vpop.f64 {d0}
    vadd.f64 d2, d0, d1
    vpush.f64 {d2}
    vpop.f64 {d0}
    ldr r6, =var_BATATA
    vstr.f64 d0, [r6]
    vpush.f64 {d0}
    vpop.f64 {d0}
    vstr.f64 d0, [r10]
    add r12, r11, #48
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
