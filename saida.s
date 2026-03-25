.global _start
.section .data
.balign 8
last_result: .double 0.0
.balign 8
results:
  .double 0.0
  .double 0.0
  .double 0.0
  .double 0.0
const_0: .double 8.0
const_1: .double 3.0
const_2: .double 2.0
const_3: .double 1.0
const_4: .double 10.5
var_CONTADOR: .double 0.0

.section .text
.global _start
_start:
mov r7, sp
ldr r0, =const_0
vldr.f64 d0, [r0]
vpush.f64 {d0}
ldr r0, =const_1
vldr.f64 d0, [r0]
vpush.f64 {d0}
vpop.f64 {d1}
vpop.f64 {d0}
vdiv.f64 d2, d0, d1
vcvtr.s32.f64 s4, d2
vcvt.f64.s32 d2, s4
vmul.f64 d2, d2, d1
vsub.f64 d2, d0, d2
vpush.f64 {d2}
vpop.f64 {d0}
ldr r0, =last_result
vstr.f64 d0, [r0]
ldr r0, =results
vstr.f64 d0, [r0]
mov sp, r7
ldr r0, =const_2
vldr.f64 d0, [r0]
vpush.f64 {d0}
ldr r0, =const_1
vldr.f64 d0, [r0]
vpush.f64 {d0}
vpop.f64 {d1}
vpop.f64 {d0}
vcvtr.s32.f64 s4, d1
vmov r1, s4
ldr r0, =const_3
vldr.f64 d2, [r0]
cmp r1, #0
beq pow_done_1
pow_loop_0:
vmul.f64 d2, d2, d0
subs r1, r1, #1
bne pow_loop_0
pow_done_1:
vpush.f64 {d2}
vpop.f64 {d0}
ldr r0, =last_result
vstr.f64 d0, [r0]
ldr r0, =results
add r0, r0, #8
vstr.f64 d0, [r0]
mov sp, r7
ldr r0, =const_4
vldr.f64 d0, [r0]
vpush.f64 {d0}
vpop.f64 {d0}
ldr r0, =var_CONTADOR
vstr.f64 d0, [r0]
vpush.f64 {d0}
vpop.f64 {d0}
ldr r0, =last_result
vstr.f64 d0, [r0]
ldr r0, =results
add r0, r0, #16
vstr.f64 d0, [r0]
mov sp, r7
ldr r0, =var_CONTADOR
vldr.f64 d0, [r0]
vpush.f64 {d0}
ldr r0, =const_2
vldr.f64 d0, [r0]
vpush.f64 {d0}
vpop.f64 {d1}
vpop.f64 {d0}
vadd.f64 d2, d0, d1
vpush.f64 {d2}
vpop.f64 {d0}
ldr r0, =last_result
vstr.f64 d0, [r0]
ldr r0, =results
add r0, r0, #24
vstr.f64 d0, [r0]
mov sp, r7
bkpt
