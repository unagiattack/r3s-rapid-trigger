; Eight-key Raw-count RT implementation for the supported stock integration.
; Raw movement thresholds have no confirmed millimeter calibration.
; Config: reserved0@0, release/press/db/restGate/restSamples/faultAfter/adcMax/restNoise@2..16.
; mode0 raw /1 original @18, baseline policy0 freeze @19, maxGap@20,generation@24.
; Sample raw/base/reserved0/epoch/tick/ready(u32==1),24B. Context14=last baseline.
; Public: init(R0=context36); adapter(R0=context,R1=sample24,R2=config28,R3=state<<8|vote).
; Adapter returns R0=vote, R1=RT-path0/1, R2=valid0/1. Caller owns stable, disjoint buffers.
.org 0x0801e400
raw_init:
2|push {r4,lr}
2|mov r4,r0
2|movs r1,#0
2|movs r2,#9
init_loop:
2|str r1,[r0,#0]
2|adds r0,#4
2|subs r2,#1
2|bne <init_loop>
2|ldr r1,[<init_magic>]
2|str r1,[r4,#28]
2|pop {r4,pc}
.align4
init_magic:
.word 0x52545231

.org 0x0801e500
raw_adapter:
2|push {r4,r5,r6,r7,lr}
2|sub sp,#4
2|mov r4,r0
2|mov r5,r1
2|mov r6,r2
2|mov r7,r3
2|lsrs r0,r7,#8
2|cmp r0,#3
2|bhi <adapter_early>
2|ldr r0,[r4,#28]
2|ldr r1,[<adapter_magic>]
2|cmp r0,r1
2|bne <adapter_early>
2|ldrb r0,[r4,#0]
2|cmp r0,#3
2|bhi <adapter_early>
2|ldrb r0,[r4,#1]
2|cmp r0,#1
2|bhi <adapter_early>
2|mov r0,r4
2|adds r0,#32
2|ldrb r0,[r0,#1]
2|cmp r0,#0
2|bne <adapter_early>
2|mov r0,r6
4|bl <raw_config_valid>
2|cmp r0,#0
2|beq <adapter_early>
2|mov r0,r4
2|adds r0,#32
2|movs r1,#1
2|strb r1,[r0,#1]
2|ldr r0,[r6,#24]
2|ldr r1,[r4,#24]
2|cmp r0,r1
2|beq <generation_ok>
2|mov r0,r4
4|bl <raw_reset>
2|movs r0,#0
2|strh r0,[r4,#4]
2|ldr r0,[r6,#24]
2|str r0,[r4,#24]
generation_ok:
2|mov r0,r4
2|mov r1,r5
2|mov r2,r6
2|uxtb r3,r7
4|bl <raw_step>
2|str r1,[sp,#0]
2|cmp r1,#0
2|beq <adapter_disarm>
2|ldrb r0,[r4,#0]
2|cmp r0,#0
2|beq <adapter_disarm>
2|ldrb r0,[r6,#18]
2|cmp r0,#1
2|beq <adapter_disarm>
2|ldrb r0,[r4,#0]
2|cmp r0,#1
2|bne <adapter_choose>
2|lsrs r0,r7,#8
2|cmp r0,#0
2|bne <adapter_choose>
2|uxtb r0,r7
2|cmp r0,#0
2|bne <adapter_choose>
2|ldrh r0,[r6,#8]
2|cmp r2,r0
2|bhi <adapter_choose>
2|mov r0,r4
2|adds r0,#32
2|movs r1,#1
2|strb r1,[r0,#0]
2|b <adapter_choose>
adapter_disarm:
2|mov r0,r4
2|adds r0,#32
2|movs r1,#0
2|strb r1,[r0,#0]
adapter_choose:
2|mov r3,r4
2|adds r3,#32
2|movs r1,#0
2|strb r1,[r3,#1]
2|ldrb r0,[r3,#0]
2|cmp r0,#1
2|bne <adapter_fallback>
2|ldrb r0,[r4,#1]
2|movs r1,#1
2|b <adapter_done>
adapter_fallback:
2|uxtb r0,r7
2|movs r1,#0
adapter_done:
2|ldr r2,[sp,#0]
2|add sp,#4
2|pop {r4,r5,r6,r7,pc}
adapter_early:
2|uxtb r0,r7
2|movs r1,#0
2|movs r2,#0
2|add sp,#4
2|pop {r4,r5,r6,r7,pc}
.align4
adapter_magic:
.word 0x52545231

.org 0x0801e700
raw_config_valid:
2|push {r4,lr}
2|mov r4,r0
2|ldrb r0,[r4,#18]
2|cmp r0,#1
2|bhi <config_bad>
2|ldrb r0,[r4,#19]
2|cmp r0,#0
2|bhi <config_bad>
2|ldr r0,[r4,#20]
2|cmp r0,#0
2|beq <config_bad>
2|lsrs r0,r0,#31
2|cmp r0,#0
2|bne <config_bad>
2|ldrh r0,[r4,#14]
2|cmp r0,#0
2|beq <config_bad>
2|ldrh r1,[r4,#16]
2|cmp r1,r0
2|bhi <config_bad>
2|ldrh r0,[r4,#10]
2|cmp r0,#0
2|beq <config_bad>
2|ldrh r0,[r4,#12]
2|cmp r0,#0
2|beq <config_bad>
2|ldrh r0,[r4,#0]
2|cmp r0,#0
2|bne <config_bad>
2|ldrh r0,[r4,#8]
2|ldrh r1,[r4,#14]
2|cmp r0,r1
2|bcs <config_bad>
2|ldrh r1,[r4,#6]
2|ldrh r0,[r4,#2]
2|cmp r0,#0
2|beq <config_bad>
2|adds r0,r0,r1
2|ldrh r2,[r4,#14]
2|cmp r0,r2
2|bhi <config_bad>
2|ldrh r0,[r4,#4]
2|cmp r0,#0
2|beq <config_bad>
2|adds r0,r0,r1
2|ldrh r2,[r4,#14]
2|cmp r0,r2
2|bhi <config_bad>
2|movs r0,#1
2|pop {r4,pc}
config_bad:
2|movs r0,#0
2|pop {r4,pc}
.align4
config_full:
.word 0x0000ffff

.org 0x0801e900
raw_step:
2|push {r4,r5,r6,r7,lr}
2|sub sp,#4
2|mov r4,r0
2|mov r5,r1
2|mov r6,r2
2|str r3,[sp,#0]
2|ldrh r0,[r4,#6]
2|movs r1,#1
2|ands r0,r1
2|beq <time_ok>
2|ldr r0,[r5,#16]
2|ldr r1,[r4,#20]
2|subs r7,r0,r1
2|lsrs r0,r7,#31
2|cmp r0,#0
2|beq <time_forward>
2|b <sample_fault>
time_forward:
2|ldr r0,[r6,#20]
2|cmp r7,r0
2|bls <time_ok>
2|mov r0,r4
4|bl <raw_reset>
time_ok:
2|ldr r0,[r5,#16]
2|str r0,[r4,#20]
2|ldrh r0,[r4,#6]
2|movs r1,#1
2|orrs r0,r1
2|strh r0,[r4,#6]
2|ldr r0,[r5,#20]
2|cmp r0,#1
2|beq <sensor_ready>
2|b <sample_fault>
sensor_ready:
2|ldrh r1,[r6,#14]
2|ldr r0,[r5,#0]
2|cmp r0,r1
2|bls <raw_ok>
2|b <sample_fault>
raw_ok:
2|ldr r0,[r5,#4]
2|cmp r0,r1
2|bls <baseline_ok>
2|b <sample_fault>
baseline_ok:
2|ldr r0,[r5,#8]
2|cmp r0,#0
2|beq <sensor_valid>
2|b <sample_fault>
sensor_valid:
2|movs r0,#0
2|strh r0,[r4,#4]
2|ldrh r0,[r4,#6]
2|movs r1,#2
2|ands r0,r1
2|beq <new_calibration>
2|ldr r0,[r5,#12]
2|ldr r1,[r4,#16]
2|cmp r0,r1
2|bne <new_calibration>
2|ldrb r0,[r4,#0]
2|cmp r0,#2
2|bcs <baseline_store>
2|ldr r0,[r5,#4]
2|ldrh r1,[r4,#14]
2|cmp r0,r1
2|beq <baseline_store>
new_calibration:
2|mov r0,r4
4|bl <raw_reset>
2|ldr r0,[r5,#12]
2|str r0,[r4,#16]
2|ldrh r0,[r4,#6]
2|movs r1,#2
2|orrs r0,r1
2|strh r0,[r4,#6]
baseline_store:
2|ldr r1,[r5,#4]
2|strh r1,[r4,#14]
2|ldrb r0,[r4,#0]
2|cmp r0,#2
2|bcc <effective_baseline>
2|ldrh r1,[r4,#12]
effective_baseline:
2|ldr r0,[r5,#0]
2|cmp r0,r1
2|bls <raw_zero>
2|subs r7,r0,r1
2|b <normalized_ok>
raw_zero:
2|movs r7,#0
normalized_ok:
2|ldrb r0,[r6,#18]
2|cmp r0,#1
2|bne <mode_enabled>
2|mov r0,r4
4|bl <raw_reset>
2|b <sample_valid_return>
mode_enabled:
2|ldrb r0,[r4,#0]
2|cmp r0,#0
2|bne <phase_active>
2|ldrh r0,[r6,#8]
2|cmp r7,r0
2|bhi <rest_count_zero>
2|ldr r3,[r5,#0]
2|ldrh r0,[r4,#2]
2|cmp r0,#0
2|beq <rest_seed>
2|ldrh r1,[r4,#8]
2|cmp r3,r1
2|bls <rest_peak_done>
2|mov r1,r3
2|strh r1,[r4,#8]
rest_peak_done:
2|ldrh r2,[r4,#10]
2|cmp r3,r2
2|bcs <rest_valley_done>
2|mov r2,r3
2|strh r2,[r4,#10]
rest_valley_done:
2|subs r1,r1,r2
2|ldrh r2,[r6,#16]
2|cmp r1,r2
2|bhi <rest_seed>
2|ldr r1,[<sample_full>]
2|cmp r0,r1
2|bcs <rest_count_store>
2|adds r0,#1
2|b <rest_count_store>
rest_seed:
2|strh r3,[r4,#8]
2|strh r3,[r4,#10]
2|movs r0,#1
2|b <rest_count_store>
rest_count_zero:
2|movs r0,#0
2|strh r0,[r4,#8]
2|strh r0,[r4,#10]
rest_count_store:
2|strh r0,[r4,#2]
2|ldrh r1,[r6,#10]
2|cmp r0,r1
2|bcc <sample_valid_return>
2|movs r0,#1
2|strb r0,[r4,#0]
2|movs r0,#0
2|strh r0,[r4,#8]
2|strh r0,[r4,#10]
2|b <sample_valid_return>
phase_active:
2|ldr r3,[sp,#0]
2|str r0,[sp,#0]
2|mov r0,r7
2|mov r1,r4
2|mov r2,r6
4|bl <raw_core>
2|ldr r0,[sp,#0]
2|cmp r0,#2
2|bcc <check_initial_press>
2|ldrb r1,[r4,#0]
2|cmp r1,#1
2|bne <check_initial_press>
2|mov r0,r4
4|bl <raw_reset>
2|b <sample_valid_return>
check_initial_press:
2|cmp r0,#1
2|bne <check_rest_phase>
2|ldrb r0,[r4,#0]
2|cmp r0,#2
2|bne <check_rest_phase>
2|ldr r0,[r5,#4]
2|strh r0,[r4,#12]
2|ldrh r0,[r4,#6]
2|movs r1,#4
2|orrs r0,r1
2|strh r0,[r4,#6]
check_rest_phase:
2|ldrb r0,[r4,#0]
2|cmp r0,#1
2|bne <sample_valid_return>
2|ldrh r0,[r4,#6]
2|movs r1,#4
2|mvns r1,r1
2|ands r0,r1
2|strh r0,[r4,#6]
2|movs r0,#0
2|strh r0,[r4,#12]
sample_valid_return:
2|ldrb r0,[r4,#1]
2|movs r1,#1
2|mov r2,r7
2|add sp,#4
2|pop {r4,r5,r6,r7,pc}
sample_fault:
2|mov r0,r4
2|mov r1,r6
4|bl <raw_fault>
2|movs r1,#0
2|movs r2,#0
2|add sp,#4
2|pop {r4,r5,r6,r7,pc}
.align4
sample_full:
.word 0x0000ffff

.org 0x0801eb00
raw_fault:
2|push {r4,lr}
2|mov r4,r0
2|ldrh r0,[r4,#4]
2|ldr r2,[<fault_full>]
2|cmp r0,r2
2|bcs <fault_count_store>
2|adds r0,#1
fault_count_store:
2|strh r0,[r4,#4]
2|ldrh r1,[r1,#12]
2|cmp r0,r1
2|bcc <fault_return>
2|mov r0,r4
4|bl <raw_reset>
fault_return:
2|ldrb r0,[r4,#1]
2|pop {r4,pc}
.align4
fault_full:
.word 0x0000ffff

.org 0x0801eb80
raw_reset:
2|movs r1,#0
2|strh r1,[r0,#0]
2|strh r1,[r0,#2]
2|strh r1,[r0,#8]
2|strh r1,[r0,#10]
2|strh r1,[r0,#12]
2|ldrh r2,[r0,#6]
2|movs r3,#4
2|mvns r3,r3
2|ands r2,r3
2|strh r2,[r0,#6]
2|adds r0,#32
2|strb r1,[r0,#0]
2|bx lr

.org 0x0801ec00
raw_core:
2|push {r4,r5,r6,r7,lr}
2|sub sp,#4
2|mov r4,r0
2|mov r5,r1
2|mov r6,r2
2|ldrb r7,[r5,#0]
2|cmp r7,#1
2|beq <core_first>
2|cmp r7,#2
2|beq <core_down>
2|b <core_ready>
core_first:
2|mov r0,r5
2|adds r0,#32
2|ldrb r0,[r0,#0]
2|cmp r0,#1
2|bne <core_off>
2|cmp r3,#0
2|beq <core_off>
2|movs r0,#2
2|strb r0,[r5,#0]
2|strh r4,[r5,#8]
2|b <core_on>
core_down:
2|ldrh r0,[r5,#8]
2|cmp r4,r0
2|bls <core_peak_done>
2|strh r4,[r5,#8]
2|mov r0,r4
core_peak_done:
2|subs r0,r0,r4
2|ldrh r1,[r6,#2]
2|ldrh r2,[r6,#6]
2|adds r1,r1,r2
2|cmp r0,r1
2|bhi <core_release>
2|b <core_rest_test>
core_rest_test:
2|ldrh r0,[r6,#8]
2|cmp r4,r0
2|bls <core_release>
2|b <core_on>
core_release:
2|strh r4,[r5,#10]
2|ldrh r0,[r6,#8]
2|cmp r4,r0
2|bls <core_rest>
2|movs r0,#3
2|strb r0,[r5,#0]
2|b <core_off>
core_rest:
2|movs r0,#1
2|strb r0,[r5,#0]
2|b <core_off>
core_ready:
2|ldrh r0,[r5,#10]
2|cmp r4,r0
2|bcs <core_valley_done>
2|strh r4,[r5,#10]
2|mov r0,r4
core_valley_done:
2|ldrh r1,[r6,#8]
2|cmp r4,r1
2|bls <core_rest>
2|subs r0,r4,r0
2|ldrh r1,[r6,#4]
2|ldrh r2,[r6,#6]
2|adds r1,r1,r2
2|cmp r0,r1
2|bls <core_off>
2|movs r0,#2
2|strb r0,[r5,#0]
2|strh r4,[r5,#8]
core_on:
2|movs r0,#1
2|b <core_store>
core_off:
2|movs r0,#0
core_store:
2|strb r0,[r5,#1]
2|add sp,#4
2|pop {r4,r5,r6,r7,pc}

.org 0x0801ee00
raw_watchdog:
2|push {r4,r5,r6,lr}
2|mov r4,r0
2|mov r5,r1
2|mov r6,r2
2|ldr r0,[r4,#28]
2|ldr r1,[<watchdog_magic>]
2|cmp r0,r1
2|bne <watchdog_no>
2|ldrb r0,[r4,#0]
2|cmp r0,#3
2|bhi <watchdog_no>
2|ldrb r0,[r4,#1]
2|cmp r0,#1
2|bhi <watchdog_no>
2|mov r0,r4
2|adds r0,#32
2|ldrb r0,[r0,#1]
2|cmp r0,#0
2|bne <watchdog_no>
2|mov r0,r6
4|bl <raw_config_valid>
2|cmp r0,#0
2|beq <watchdog_no>
2|ldr r0,[r4,#24]
2|ldr r1,[r6,#24]
2|cmp r0,r1
2|bne <watchdog_no>
2|ldrb r0,[r4,#0]
2|cmp r0,#0
2|beq <watchdog_no>
2|ldrh r0,[r4,#6]
2|movs r1,#1
2|ands r0,r1
2|beq <watchdog_no>
2|ldr r1,[r4,#20]
2|subs r0,r5,r1
2|lsrs r1,r0,#31
2|cmp r1,#0
2|bne <watchdog_no>
2|ldr r1,[r6,#20]
2|cmp r0,r1
2|bls <watchdog_no>
2|mov r0,r4
4|bl <raw_reset>
2|movs r0,#1
2|pop {r4,r5,r6,pc}
watchdog_no:
2|movs r0,#0
2|pop {r4,r5,r6,pc}
.align4
watchdog_magic:
.word 0x52545231

; Each key owns a 36-byte committed context. One shared 44-byte transaction holds
; pending[36], staged, and owner. The masked scanner path serializes stage/finish.
.org 0x0801f000
tx_init:
2|push {r4,lr}
4|bl <raw_init>
2|pop {r4,pc}

.org 0x0801f010
tx_stage:
2|push {r4,r5,r6,r7,lr}
2|sub sp,#4
2|mov r4,r0
2|mov r5,r1
2|mov r6,r2
2|mov r7,r3
2|ldr r0,[<tx_stage_shared>]
2|ldr r1,[r0,#36]
2|cmp r1,#0
2|bne <tx_nested>
2|mov r1,r0
2|mov r0,r4
4|bl <tx_copy>
2|ldr r0,[<tx_stage_shared>]
2|mov r1,r5
2|mov r2,r6
2|mov r3,r7
4|bl <raw_adapter>
2|push {r0,r1,r2,r3}
2|cmp r2,#0
2|beq <tx_invalid>
2|ldr r0,[<tx_stage_shared>]
2|movs r1,#1
2|str r1,[r0,#36]
2|str r4,[r0,#40]
2|b <tx_stage_end>
tx_invalid:
2|ldr r0,[<tx_stage_shared>]
4|bl <raw_reset>
2|ldr r0,[<tx_stage_shared>]
2|mov r1,r4
4|bl <tx_copy>
tx_stage_end:
2|pop {r0,r1,r2,r3}
2|add sp,#4
2|pop {r4,r5,r6,r7,pc}
tx_nested:
2|uxtb r0,r7
2|movs r1,#0
2|movs r2,#0
2|add sp,#4
2|pop {r4,r5,r6,r7,pc}
.align4
tx_stage_shared:
.word 0x20004dd4

.org 0x0801f080
tx_finish:
2|push {r4,r5,r6,lr}
2|mov r4,r0
2|mov r6,r1
2|ldr r5,[<tx_finish_shared>]
2|ldr r0,[r5,#40]
2|cmp r0,r4
2|bne <tx_finish_skip>
2|ldr r0,[r5,#36]
2|cmp r0,#1
2|bne <tx_finish_skip>
2|movs r0,#0
2|str r0,[r5,#36]
2|str r0,[r5,#40]
2|cmp r6,#3
2|beq <tx_finish_skip>
2|cmp r6,#4
2|beq <tx_finish_skip>
2|mov r0,r5
2|mov r1,r4
4|bl <tx_copy>
2|movs r0,#1
2|pop {r4,r5,r6,pc}
tx_finish_skip:
2|movs r0,#0
2|pop {r4,r5,r6,pc}
.align4
tx_finish_shared:
.word 0x20004dd4

.org 0x0801f0c0
tx_invalidate:
2|push {r4,r5,r6,lr}
2|mov r4,r0
4|bl <raw_reset>
2|ldr r5,[<tx_invalidate_shared>]
2|ldr r0,[r5,#40]
2|cmp r0,r4
2|bne <tx_invalidate_end>
2|movs r0,#0
2|str r0,[r5,#36]
2|str r0,[r5,#40]
tx_invalidate_end:
2|pop {r4,r5,r6,pc}
.align4
tx_invalidate_shared:
.word 0x20004dd4
.org 0x0801f0f0
tx_copy:
2|movs r2,#9
tx_copy_loop:
2|ldr r3,[r0,#0]
2|str r3,[r1,#0]
2|adds r0,#4
2|adds r1,#4
2|subs r2,#1
2|bne <tx_copy_loop>
2|bx lr

.org 0x0801f110
tx_watchdog:
2|push {r4,r5,r6,lr}
2|mov r4,r0
2|ldr r5,[<tx_watchdog_shared>]
2|ldr r0,[r5,#40]
2|cmp r0,r4
2|bne <tx_watchdog_run>
2|movs r0,#0
2|str r0,[r5,#36]
2|str r0,[r5,#40]
tx_watchdog_run:
2|mov r0,r4
4|bl <raw_watchdog>
2|pop {r4,r5,r6,pc}
.align4
tx_watchdog_shared:
.word 0x20004dd4

.org 0x0801f200
w_prepare:
2|push {r4,r5,r6,r7,lr}
2|sub sp,#4
2|mov r4,r0
2|mov r5,r1
2|mov r6,r2
2|ldr r0,[r5,#0]
2|uxth r1,r0
2|str r1,[r4,#0]
2|ldr r1,[r5,#4]
2|str r1,[r4,#4]
2|movs r1,#0
2|str r1,[r4,#8]
2|str r1,[r4,#20]
2|ldr r1,[r5,#8]
2|str r1,[r4,#12]
2|ldr r1,[r5,#12]
2|str r1,[r4,#16]
2|lsrs r0,r0,#16
2|cmp r0,#1
2|bne <w_prepare_no>
2|ldr r0,[r5,#16]
2|ldr r1,[r5,#20]
2|cmp r0,r1
2|bne <w_prepare_no>
2|movs r1,#1
2|ands r0,r1
2|bne <w_prepare_no>
2|ldr r0,[r5,#24]
2|ldr r1,[r5,#28]
2|cmp r0,r1
2|bne <w_prepare_no>
2|ldr r1,[r6,#24]
2|cmp r0,r1
2|bne <w_prepare_no>
2|ldr r0,[r5,#32]
4|bl <per_key_enabled>
2|cmp r0,#1
2|bne <w_prepare_no>
w_prepare_target:
2|ldr r0,[r5,#36]
2|cmp r0,#7
2|bne <w_prepare_no>
2|ldr r0,[r5,#40]
2|cmp r0,#1
2|bne <w_prepare_no>
2|ldr r0,[r5,#44]
2|cmp r0,#3
2|bhi <w_prepare_no>
2|ldr r0,[r5,#48]
2|cmp r0,#2
2|bhi <w_prepare_no>
2|ldr r0,[r5,#52]
2|cmp r0,#10
2|bcc <w_prepare_no>
2|ldr r1,[<w_u16_max>]
2|cmp r0,r1
2|bhi <w_prepare_no>
2|ldr r0,[r5,#56]
2|cmp r0,#3
2|bhi <w_prepare_no>
2|ldr r0,[r5,#60]
2|cmp r0,#255
2|bhi <w_prepare_no>
2|ldrh r1,[r6,#14]
2|ldr r0,[r4,#0]
2|cmp r0,r1
2|bhi <w_prepare_no>
2|ldr r0,[r4,#4]
2|cmp r0,r1
2|bhi <w_prepare_no>
2|ldrb r0,[r6,#18]
2|cmp r0,#0
2|bne <w_prepare_no>
2|mov r0,r6
4|bl <raw_config_valid>
2|cmp r0,#1
2|bne <w_prepare_no>
2|str r0,[r4,#20]
2|b <w_prepare_end>
w_prepare_no:
2|movs r0,#0
w_prepare_end:
2|add sp,#4
2|pop {r4,r5,r6,r7,pc}
.align4
w_u16_max:
.word 0x0000ffff

.org 0x0801f0c0
rt_invalidate:
.org 0x0801f200
rt_prepare:
.org 0x0801f010
rt_stage:
.org 0x0801f080
rt_finish:

; RT-owned 16-byte sidecar: sequence/epoch/generation/depth.
; Callers serialize updates under PRIMASK. Corruption leaves an odd sequence.
.org 0x0801f400
writer_init:
2|movs r1,#0
2|str r1,[r0,#0]
2|str r1,[r0,#4]
2|str r1,[r0,#8]
2|str r1,[r0,#12]
2|bx lr
writer_begin:
2|ldr r1,[r0,#0]
2|ldr r2,[r0,#12]
2|cmp r2,#0
2|beq <writer_outer>
2|cmp r2,#254
2|bhi <writer_broken>
2|movs r3,#1
2|ands r3,r1
2|beq <writer_broken>
2|adds r2,#1
2|str r2,[r0,#12]
2|movs r0,#1
2|bx lr
writer_outer:
2|movs r3,#1
2|ands r3,r1
2|bne <writer_broken>
2|movs r2,#0
2|mvns r2,r2
2|ldr r3,[r0,#4]
2|cmp r3,r2
2|beq <writer_broken>
2|ldr r3,[r0,#8]
2|cmp r3,r2
2|beq <writer_broken>
2|adds r1,#1
2|str r1,[r0,#0]
2|ldr r1,[r0,#4]
2|adds r1,#1
2|str r1,[r0,#4]
2|ldr r1,[r0,#8]
2|adds r1,#1
2|str r1,[r0,#8]
2|movs r1,#1
2|str r1,[r0,#12]
2|movs r0,#1
2|bx lr
writer_end:
2|ldr r1,[r0,#0]
2|ldr r2,[r0,#12]
2|cmp r2,#0
2|beq <writer_broken>
2|cmp r2,#255
2|bhi <writer_broken>
2|movs r3,#1
2|ands r3,r1
2|beq <writer_broken>
2|subs r2,#1
2|str r2,[r0,#12]
2|bne <writer_end_done>
2|adds r1,#1
2|str r1,[r0,#0]
writer_end_done:
2|movs r0,#1
2|bx lr
writer_broken:
2|movs r3,#1
2|orrs r1,r3
2|str r1,[r0,#0]
2|movs r1,#0
2|mvns r1,r1
2|str r1,[r0,#12]
2|movs r0,#0
2|bx lr
; R0 sidecar16, R1 committed context36, R2 id0..5, R3 stable args[2].
; ID0 mode166D4, ID1 selector166E0, ID2 globals166EC, ID3 gain169B0.
; ID4 sensor clear1666C, ID5 sensor initialize16680; wrapped stock mutation paths.
; Mutation always runs for valid ID, even metadata failure; stock R0 return preserved.
.org 0x0801f500
writer_apply:
2|push {r4,r5,r6,r7,lr}
2|sub sp,#12
2|mov r4,r0
2|mov r5,r1
2|mov r6,r2
2|mov r7,r3
2|cmp r6,#5
2|bhi <writer_id_bad>
2|mov r0,r4
4|bl <writer_begin>
2|str r0,[sp,#4]
2|mov r0,r5
4|bl <wasd_invalidate_all>
2|ldr r0,[r7,#0]
2|ldr r1,[r7,#4]
2|cmp r6,#0
2|beq <writer_mode>
2|cmp r6,#1
2|beq <writer_selector>
2|cmp r6,#2
2|beq <writer_globals>
2|cmp r6,#3
2|beq <writer_gain>
2|cmp r6,#4
2|beq <writer_clear>
4|bl 0x08016680
2|b <writer_original_done>
writer_clear:
4|bl 0x0801666c
2|b <writer_original_done>
writer_gain:
4|bl 0x080169b0
2|b <writer_original_done>
writer_mode:
4|bl 0x080166d4
2|b <writer_original_done>
writer_selector:
4|bl 0x080166e0
2|b <writer_original_done>
writer_globals:
4|bl 0x080166ec
writer_original_done:
2|str r0,[sp,#0]
2|mov r0,r5
4|bl <wasd_invalidate_all>
2|ldr r0,[sp,#4]
2|cmp r0,#1
2|bne <writer_keep_denied>
2|mov r0,r4
4|bl <writer_end>
2|mov r1,r0
2|b <writer_result>
writer_keep_denied:
2|movs r1,#0
writer_result:
2|ldr r0,[sp,#0]
2|b <writer_apply_end>
writer_id_bad:
2|movs r0,#0
2|mvns r0,r0
2|movs r1,#0
writer_apply_end:
2|add sp,#12
2|pop {r4,r5,r6,r7,pc}

; Privileged Cortex-M mutation guard. NMI/HardFault/DMA remain outside this protocol.
.org 0x0801f600
irq_save:
4|mrs r0,primask
2|cpsid i
2|bx lr
irq_restore:
4|dmb #0x1f
4|msr primask,r0
2|bx lr
.org 0x0801f700
critical_apply:
2|push {r4,r5,r6,r7,lr}
2|sub sp,#12
2|mov r4,r0
2|mov r5,r1
2|mov r6,r2
2|mov r7,r3
2|cmp r6,#5
2|bhi <critical_id_bad>
4|mrs r0,primask
2|str r0,[sp,#8]
2|cpsid i
2|mov r0,r4
4|bl <writer_begin>
2|str r0,[sp,#4]
2|mov r0,r5
4|bl <wasd_invalidate_all>
2|ldr r0,[sp,#8]
4|dmb #0x1f
4|msr primask,r0
2|ldr r0,[r7,#0]
2|ldr r1,[r7,#4]
2|cmp r6,#0
2|beq <critical_mode>
2|cmp r6,#1
2|beq <critical_selector>
2|cmp r6,#2
2|beq <critical_globals>
2|cmp r6,#3
2|beq <critical_gain>
2|cmp r6,#4
2|beq <critical_clear>
4|bl 0x08016680
2|b <critical_original_done>
critical_clear:
4|bl 0x0801666c
2|b <critical_original_done>
critical_gain:
4|bl 0x080169b0
2|b <critical_original_done>
critical_mode:
4|bl 0x080166d4
2|b <critical_original_done>
critical_selector:
4|bl 0x080166e0
2|b <critical_original_done>
critical_globals:
4|bl 0x080166ec
critical_original_done:
2|str r0,[sp,#0]
2|cpsid i
2|mov r0,r5
4|bl <wasd_invalidate_all>
2|ldr r0,[sp,#4]
2|cmp r0,#1
2|bne <critical_keep_denied>
2|mov r0,r4
4|bl <writer_end>
2|mov r1,r0
2|b <critical_result>
critical_keep_denied:
2|movs r1,#0
critical_result:
2|ldr r2,[sp,#8]
4|dmb #0x1f
4|msr primask,r2
2|ldr r0,[sp,#0]
2|b <critical_apply_end>
critical_id_bad:
2|movs r0,#0
2|mvns r0,r0
2|movs r1,#0
critical_apply_end:
2|add sp,#12
2|pop {r4,r5,r6,r7,pc}

; R0 bundle20: context/sample/config/mutable-frame/metadata pointers; R1 stock vote byte.
; Decision for the selected enabled key. Frame proofs describe acquisition provenance.
; Restores entry PRIMASK. No ADC polling or HID dispatch within this short section.
.org 0x0801f900
critical_decide:
2|push {r4,r5,r6,r7,lr}
2|sub sp,#20
2|mov r4,r0
2|uxtb r1,r1
2|str r1,[sp,#4]
4|mrs r0,primask
2|str r0,[sp,#0]
2|cpsid i
2|ldr r5,[r4,#0]
2|ldr r7,[r4,#4]
2|ldr r6,[r4,#12]
2|ldr r0,[sp,#4]
2|str r0,[r6,#60]
2|ldr r0,[<decision_key>]
2|ldr r0,[r0,#0]
2|ldrb r0,[r0,#0]
2|str r0,[r6,#56]
2|mov r0,r7
2|mov r1,r6
2|ldr r2,[r4,#8]
4|bl <rt_prepare>
2|movs r1,#0
2|str r1,[r6,#36]
2|cmp r0,#1
2|bne <decision_stage>
2|ldr r0,[r4,#16]
2|ldr r1,[r0,#12]
2|cmp r1,#0
2|bne <decision_invalid>
2|ldr r1,[r0,#0]
2|ldr r2,[r6,#16]
2|cmp r1,r2
2|bne <decision_invalid>
2|ldr r1,[r0,#4]
2|ldr r2,[r6,#8]
2|cmp r1,r2
2|bne <decision_invalid>
2|ldr r1,[r0,#8]
2|ldr r2,[r6,#24]
2|cmp r1,r2
2|bne <decision_invalid>
2|ldr r0,[<decision_globals>]
2|ldrb r1,[r0,#0]
2|ldr r2,[r6,#40]
2|cmp r1,r2
2|bne <decision_invalid>
2|ldrb r1,[r0,#1]
2|ldr r2,[r6,#44]
2|cmp r1,r2
2|bne <decision_invalid>
2|ldr r0,[<decision_sensor>]
2|ldr r0,[r0,#0]
2|ldrh r1,[r0,#4]
2|ldr r2,[r6,#0]
2|uxth r2,r2
2|cmp r1,r2
2|bne <decision_invalid>
2|ldrh r1,[r0,#6]
2|ldr r2,[r6,#4]
2|cmp r1,r2
2|bne <decision_invalid>
2|ldrh r1,[r0,#8]
2|ldr r2,[r6,#52]
2|cmp r1,r2
2|bne <decision_invalid>
2|ldrb r1,[r0,#26]
2|ldr r2,[r6,#48]
2|cmp r1,r2
2|beq <decision_stage>
decision_invalid:
2|movs r0,#0
2|str r0,[r7,#20]
decision_stage:
2|mov r0,r5
2|mov r1,r7
2|ldr r2,[r4,#8]
2|ldr r3,[r6,#56]
2|lsls r3,r3,#8
2|ldr r7,[r6,#60]
2|adds r3,r3,r7
4|bl <rt_stage>
2|str r0,[sp,#4]
2|str r1,[sp,#8]
2|str r2,[sp,#12]
2|mov r1,r0
2|ldr r0,[r6,#32]
4|bl 0x080187c4
2|str r0,[sp,#16]
2|mov r1,r0
2|mov r0,r5
4|bl <rt_finish>
2|ldr r0,[sp,#0]
4|dmb #0x1f
4|msr primask,r0
2|ldr r0,[sp,#16]
2|ldr r1,[sp,#4]
2|ldr r2,[sp,#12]
2|ldr r3,[sp,#8]
2|add sp,#20
2|pop {r4,r5,r6,r7,pc}
.align4
decision_key:
.word 0x20004fe0
decision_globals:
.word 0x20002b10
decision_sensor:
.word 0x20004fdc

; Acquisition token24: seq/epoch/generation/sensor/startTick/valid.
; R0 token24, R1 metadata16, R2 caller sensor. Short privileged snapshot only.
.org 0x0801fa00
capture_begin:
2|push {r4,r5,r6,lr}
2|sub sp,#8
2|mov r4,r0
2|mov r5,r1
2|mov r6,r2
4|mrs r0,primask
2|str r0,[sp,#0]
2|cpsid i
2|movs r0,#0
2|str r0,[r4,#20]
2|ldr r1,[r5,#0]
2|str r1,[r4,#0]
2|ldr r1,[r5,#4]
2|str r1,[r4,#4]
2|ldr r1,[r5,#8]
2|str r1,[r4,#8]
2|str r6,[r4,#12]
4|bl 0x08010c94
2|str r0,[r4,#16]
2|mov r0,r6
4|bl <per_key_enabled>
2|cmp r0,#1
2|bne <capture_begin_end>
capture_begin_target:
2|ldr r0,[r5,#0]
2|movs r1,#1
2|ands r0,r1
2|bne <capture_begin_end>
2|ldr r0,[r5,#12]
2|cmp r0,#0
2|bne <capture_begin_end>
2|str r1,[r4,#20]
capture_begin_end:
2|ldr r0,[sp,#0]
4|dmb #0x1f
4|msr primask,r0
2|ldr r0,[r4,#20]
2|add sp,#8
2|pop {r4,r5,r6,pc}

; Finish bundle24: frame64/token24/metadata16/taggedRaw/profileProof/config28.
; profileProof bits0/1 authorize the integration assumptions; they are not measurements.
; Return R0 acquisition-valid, R1 capabilities; creates no hardware quality proof.
.org 0x0801fb00
capture_finish:
2|push {r4,r5,r6,r7,lr}
2|sub sp,#12
2|mov r4,r0
4|mrs r0,primask
2|str r0,[sp,#0]
2|cpsid i
2|ldr r5,[r4,#0]
2|ldr r6,[r4,#4]
2|ldr r7,[r4,#8]
2|ldr r0,[r6,#20]
2|str r0,[sp,#8]
2|movs r0,#0
2|str r0,[r6,#20]
2|mov r0,r5
2|movs r1,#0
2|movs r2,#16
capture_clear:
2|str r1,[r0,#0]
2|adds r0,#4
2|subs r2,#1
2|bne <capture_clear>
2|ldr r0,[r4,#12]
2|str r0,[r5,#0]
2|ldr r0,[<capture_sensor>]
2|ldr r0,[r0,#0]
2|ldrh r1,[r0,#6]
2|str r1,[r5,#4]
2|ldrh r1,[r0,#8]
2|str r1,[r5,#52]
2|ldrb r1,[r0,#26]
2|str r1,[r5,#48]
2|ldr r0,[r6,#4]
2|str r0,[r5,#8]
4|bl 0x08010c94
2|str r0,[r5,#12]
2|ldr r0,[r6,#0]
2|str r0,[r5,#16]
2|ldr r0,[r7,#0]
2|str r0,[r5,#20]
2|ldr r0,[r6,#8]
2|str r0,[r5,#24]
2|ldr r0,[r7,#8]
2|str r0,[r5,#28]
2|ldr r0,[r6,#12]
2|str r0,[r5,#32]
2|ldr r0,[<capture_globals>]
2|ldrb r1,[r0,#0]
2|str r1,[r5,#40]
2|ldrb r1,[r0,#1]
2|str r1,[r5,#44]
2|ldr r0,[<capture_key>]
2|ldr r0,[r0,#0]
2|ldrb r0,[r0,#0]
2|str r0,[r5,#56]
2|ldr r0,[r6,#12]
4|bl 0x0801651c
2|str r0,[r5,#60]
2|movs r0,#0
2|str r0,[sp,#4]
2|ldr r0,[sp,#8]
2|cmp r0,#1
2|bne <capture_finish_end>
2|ldr r0,[r6,#12]
4|bl <per_key_enabled>
2|cmp r0,#1
2|bne <capture_finish_end>
capture_finish_target:
2|ldr r0,[r7,#12]
2|cmp r0,#0
2|bne <capture_finish_end>
2|ldr r0,[r7,#0]
2|movs r1,#1
2|ands r1,r0
2|bne <capture_finish_end>
2|ldr r1,[r6,#0]
2|cmp r0,r1
2|bne <capture_finish_end>
2|ldr r0,[r7,#4]
2|ldr r1,[r6,#4]
2|cmp r0,r1
2|bne <capture_finish_end>
2|ldr r0,[r7,#8]
2|ldr r1,[r6,#8]
2|cmp r0,r1
2|bne <capture_finish_end>
2|ldr r0,[r4,#12]
2|lsrs r1,r0,#16
2|cmp r1,#1
2|bne <capture_finish_end>
2|uxth r0,r0
2|ldr r1,[<capture_sensor>]
2|ldr r1,[r1,#0]
2|ldrh r1,[r1,#4]
2|cmp r0,r1
2|bne <capture_finish_end>
2|ldr r0,[r5,#12]
2|ldr r1,[r6,#16]
2|subs r0,r0,r1
2|ldr r1,[r4,#20]
2|ldr r1,[r1,#20]
2|cmp r1,#0
2|beq <capture_finish_end>
2|lsrs r2,r1,#31
2|cmp r2,#0
2|bne <capture_finish_end>
2|cmp r0,r1
2|bhi <capture_finish_end>
2|ldr r0,[r4,#16]
2|cmp r0,#3
2|bhi <capture_finish_end>
2|movs r1,#4
2|orrs r0,r1
2|str r0,[r5,#36]
2|movs r0,#1
2|str r0,[sp,#4]
capture_finish_end:
2|ldr r0,[sp,#0]
4|dmb #0x1f
4|msr primask,r0
2|ldr r0,[sp,#4]
2|ldr r1,[r5,#36]
2|add sp,#12
2|pop {r4,r5,r6,r7,pc}
.align4
capture_sensor:
.word 0x20004fdc
capture_globals:
.word 0x20002b10
capture_key:
.word 0x20004fe0

; Stock scanner hooks. The 40-byte RT descriptor is allocated at 0x20004eb4.
; Descriptor: decision pointers0..16/token20/finishBundle24/profileProof28/tag32/sensor36.
; acquire hook is specific to original157C8, whose live R7 is the sensor index.
.org 0x0801fc80
scanner_acquire_hook:
2|push {r4,r5,lr}
2|sub sp,#4
2|mov r4,r0
2|ldr r5,[<acquire_descriptor>]
2|mov r2,r7
2|str r2,[r5,#36]
2|mov r0,r2
4|bl <wasd_select>
2|cmp r0,#0
2|beq <acquire_original>
2|mov r2,r7
2|ldr r0,[r5,#20]
2|ldr r1,[r5,#16]
4|bl <integration_maybe_enable>
4|bl <capture_begin>
acquire_original:
2|mov r0,r4
4|bl 0x08018898
2|str r0,[r5,#32]
2|add sp,#4
2|pop {r4,r5,pc}
.align4
acquire_descriptor:
.word 0x20004eb4

.org 0x0801fd00
scanner_sensor_hook:
2|push {r4,r5,r6,lr}
2|sub sp,#8
2|mov r4,r0
2|mov r5,r1
2|ldr r6,[<sensor_descriptor>]
2|uxth r1,r1
4|bl 0x08016700
2|str r0,[sp,#0]
sensor_hook_target:
2|mov r0,r4
4|bl <per_key_enabled>
2|cmp r0,#1
2|bne <sensor_hook_end>
2|ldr r0,[r6,#36]
2|cmp r0,r4
2|bne <sensor_unbound>
2|ldr r0,[r6,#32]
2|cmp r0,r5
2|beq <sensor_finish>
sensor_unbound:
2|ldr r0,[r6,#20]
2|ldr r1,[r6,#16]
2|movs r2,#255
4|bl <integration_maybe_enable>
4|bl <capture_begin>
sensor_finish:
2|ldr r0,[r6,#24]
2|ldr r1,[r6,#12]
2|str r1,[r0,#0]
2|ldr r1,[r6,#20]
2|str r1,[r0,#4]
2|ldr r1,[r6,#16]
2|str r1,[r0,#8]
2|str r5,[r0,#12]
2|ldr r1,[r6,#28]
2|str r1,[r0,#16]
2|ldr r1,[r6,#8]
2|str r1,[r0,#20]
4|bl <capture_finish>
sensor_hook_end:
2|ldr r0,[sp,#0]
2|add sp,#8
2|pop {r4,r5,r6,pc}
.align4
sensor_descriptor:
.word 0x20004eb4

.org 0x0801fdc0
scanner_fsm_hook:
2|push {r4,r5,lr}
2|sub sp,#4
2|mov r4,r0
2|mov r5,r1
fsm_target:
2|mov r0,r4
4|bl <per_key_enabled>
2|cmp r0,#1
2|bne <fsm_original>
2|ldr r0,[<fsm_descriptor>]
4|bl <critical_decide>
2|b <fsm_hook_end>
fsm_original:
2|mov r0,r4
2|mov r1,r5
4|bl 0x080187c4
fsm_hook_end:
2|add sp,#4
2|pop {r4,r5,pc}
.align4
fsm_descriptor:
.word 0x20004eb4


; Bounded ADC compatibility wrapper: R0 peripheral base, R1 polling budget.
; .stock16 words are read locally from user stock, with register fields adjusted.
; The success tag and explicit timeout path are project-authored additions.
.org 0x0801fe00
adc_read:
2|push {r4,r5,r6,r7,lr}
2|sub sp,#4
2|mov r4,r0
2|mov r5,r1
2|mov r6,r1
2|cmp r5,#0
2|beq <timeout>
2|lsrs r0,r5,#16
2|cmp r0,#0
2|bne <timeout>
.stock16 0x08016350 0x0700 0x0700
cr_check:
.stock16 0x0801634e 0x0038 0x0020
.stock16 0x08016352 0x0038 0x0038
.stock16 0x08016358 0x0038 0x0020
.stock16 0x0801635a 0x0000 0x0000
2|bne <conversion_start>
2|subs r6,r6,#1
2|bne <cr_check>
2|b <timeout>
conversion_start:
2|mov r6,r5
.stock16 0x08016366 0x0038 0x0020
.stock16 0x0801636a 0x0038 0x0038
.stock16 0x08016370 0x0038 0x0020
poll:
.stock16 0x08016390 0x0038 0x0020
.stock16 0x08016394 0x0038 0x0038
.stock16 0x0801639a 0x0038 0x0020
.stock16 0x0801639c 0x0000 0x0000
2|bne <success>
2|subs r6,r6,#1
2|beq <timeout>
.stock16 0x0801637e 0x0000 0x0000
.stock16 0x08016380 0x0000 0x0000
.stock16 0x08016382 0x0000 0x0000
delay:
.stock16 0x08016384 0x0000 0x0000
.stock16 0x08016386 0x0000 0x0000
.stock16 0x08016388 0x0000 0x0000
.stock16 0x0801638a 0x0000 0x0000
2|b <poll>
timeout:
2|movs r0,#0
2|b <adc_return>
success:
.stock16 0x080163a4 0x0038 0x0020
.stock16 0x080163a6 0x0000 0x0000
2|movs r1,#1
2|lsls r1,r1,#16
2|orrs r0,r1
adc_return:
2|add sp,#4
2|pop {r4,r5,r6,r7,pc}

; A011 matrix call ABI shim: original channel argument is unused by custom reader.
; Peripheral base is a verified MMIO address, not allocated RAM.
.org 0x0801fe80
matrix_adc_shim:
2|push {r4,lr}
2|ldr r0,[<adc_base>]
2|movs r1,#125
2|lsls r1,r1,#3
4|bl <adc_read>
2|pop {r4,pc}
.align4
adc_base:
.word 0x40012400

; The boot bridge calls this after the stock scatter initialization.
; Clear the 564-byte RT allocation and start with unproven acquisition metadata.
.org 0x0801e840
integration_init:
2|push {r4,r5,r6,lr}
2|ldr r0,[<integration_ram>]
2|movs r1,#0
2|movs r2,#141
integration_zero:
2|str r1,[r0,#0]
2|adds r0,#4
2|subs r2,#1
2|bne <integration_zero>
2|ldr r4,[<integration_contexts>]
2|movs r5,#8
integration_context_init:
2|ldr r0,[r4,#0]
4|bl <tx_init>
2|adds r4,#4
2|subs r5,#1
2|bne <integration_context_init>
2|ldr r0,[<integration_control>]
2|movs r1,#255
2|str r1,[r0,#0]
2|ldr r1,[<integration_sensor_w>]
2|str r1,[r0,#4]
2|ldr r1,[<integration_key_w>]
2|str r1,[r0,#8]
2|ldr r0,[<integration_descriptor>]
2|ldr r1,[<integration_table_pointer>]
2|movs r2,#10
integration_copy:
2|ldr r3,[r1,#0]
2|str r3,[r0,#0]
2|adds r1,#4
2|adds r0,#4
2|subs r2,#1
2|bne <integration_copy>
2|pop {r4,r5,r6,pc}
.align4
integration_ram:
.word 0x20004db0
integration_descriptor:
.word 0x20004eb4
integration_table_pointer:
.word 0x0801ff00
integration_contexts:
.word 0x0801f5c0
integration_context_a:
.word 0x20004edc
integration_context_s:
.word 0x20004f00
integration_context_d:
.word 0x20004f24
integration_control:
.word 0x20004fd8
integration_sensor_w:
.word 0x20002d1e
integration_key_w:
.word 0x200012bc
.org 0x0801ff00
integration_table:
.word 0x20004db0
.word 0x20004e00
.word 0x20004e18
.word 0x20004e34
.word 0x20004e74
.word 0x20004e84
.word 0x20004e9c
.word 0x00000000
.word 0x00000000
.word 0x000000ff

.org 0x0801e780
integration_writer_0:
2|movs r2,#0
2|b <integration_writer_common>
integration_writer_1:
2|movs r2,#1
2|b <integration_writer_common>
integration_writer_2:
2|movs r2,#2
2|b <integration_writer_common>
integration_writer_3:
2|movs r2,#3
2|b <integration_writer_common>
integration_writer_4:
2|movs r2,#4
2|b <integration_writer_common>
integration_writer_5:
2|movs r2,#5
2|b <integration_writer_common>
integration_writer_common:
2|push {r0,r1,r4,lr}
2|mov r3,sp
2|ldr r0,[<integration_writer_meta>]
2|ldr r1,[<integration_writer_context>]
4|bl <critical_apply>
2|add sp,#8
2|pop {r4,pc}
.align4
integration_writer_meta:
.word 0x20004e74
integration_writer_context:
.word 0x20004db0

; Original scatter loop reaches 080100C8, whose literal at 080100CC selects main.
; Redirect that literal, not the pre-scatter BL; otherwise init would be overwritten.
.org 0x0801ff40
integration_boot_bridge:
2|push {r4,lr}
4|bl <integration_init>
2|ldr r0,[<integration_original_main>]
4|bl 0x08019d54
2|pop {r4,pc}
.align4
integration_original_main:
.word 0x08019d55

; Revoke stale RT authorization around broader settings/clock calls.
; Short masked notification only; original callees run with their own mask behavior.
.org 0x0801e800
integration_revoke:
2|push {r0,r1,r2,r3,r4,r5,r6,lr}
4|mrs r4,primask
2|cpsid i
2|ldr r0,[<integration_revoke_meta>]
4|bl <writer_begin>
2|mov r5,r0
2|ldr r0,[<integration_revoke_context>]
4|bl <wasd_invalidate_all>
2|ldr r0,[<integration_revoke_descriptor>]
2|movs r1,#0
2|str r1,[r0,#28]
2|cmp r5,#1
2|bne <integration_revoke_end>
2|ldr r0,[<integration_revoke_meta>]
4|bl <writer_end>
integration_revoke_end:
4|dmb #0x1f
4|msr primask,r4
2|pop {r0,r1,r2,r3,r4,r5,r6,pc}
.align4
integration_revoke_meta:
.word 0x20004e74
integration_revoke_context:
.word 0x20004db0
integration_revoke_descriptor:
.word 0x20004eb4

.org 0x0801ee80
integration_guard_selection:
2|push {r4,lr}
4|bl <integration_revoke>
4|bl 0x080192fc
2|push {r0,r1}
4|bl <integration_revoke>
2|pop {r0,r1}
2|pop {r4,pc}

.org 0x0801eea0
integration_guard_keymap:
2|push {r4,lr}
4|bl <integration_revoke>
4|bl 0x08018794
2|push {r0,r1}
4|bl <integration_revoke>
2|pop {r0,r1}
2|pop {r4,pc}

.org 0x0801eec0
integration_guard_record:
2|push {r4,lr}
4|bl <integration_revoke>
4|bl 0x0801a4c8
2|push {r0,r1}
4|bl <integration_revoke>
2|pop {r0,r1}
2|pop {r4,pc}

.org 0x0801eee0
integration_guard_apply:
2|push {r4,lr}
4|bl <integration_revoke>
4|bl 0x08019dc0
2|push {r0,r1}
4|bl <integration_revoke>
2|pop {r0,r1}
2|pop {r4,pc}

.org 0x0801ef00
integration_guard_reload:
2|push {r4,lr}
4|bl <integration_revoke>
4|bl 0x0801a004
2|push {r0,r1}
4|bl <integration_revoke>
2|pop {r0,r1}
2|pop {r4,pc}

.org 0x0801ef20
integration_guard_clock_setup:
2|push {r4,lr}
4|bl <integration_revoke>
4|bl 0x08012b30
2|push {r0,r1}
4|bl <integration_revoke>
2|pop {r0,r1}
2|pop {r4,pc}

.org 0x0801ef40
integration_guard_clock_alternate:
2|push {r4,lr}
4|bl <integration_revoke>
4|bl 0x08012a44
2|push {r0,r1}
4|bl <integration_revoke>
2|pop {r0,r1}
2|pop {r4,pc}

.org 0x0801ef60
integration_guard_clock_transition:
2|push {r4,lr}
4|bl <integration_revoke>
4|bl 0x08012be8
2|push {r0,r1}
4|bl <integration_revoke>
2|pop {r0,r1}
2|pop {r4,pc}

.org 0x0801ef80
integration_guard_systick_setup:
2|push {r4,lr}
4|bl <integration_revoke>
4|bl 0x08010cb0
2|push {r0,r1}
4|bl <integration_revoke>
2|pop {r0,r1}
2|pop {r4,pc}

.org 0x0801efa0
; This wake wrapper is present but not hooked; all wake paths are not verified.
integration_guard_wake_candidate:
2|push {r4,lr}
4|bl <integration_revoke>
4|bl 0x0801b584
2|push {r0,r1}
4|bl <integration_revoke>
2|pop {r0,r1}
2|pop {r4,pc}

; Activation header is enabled by the packaged exporter for this implementation.
; Profile authorization means explicit experiment assumptions, not physical proof.
.org 0x0801f300
integration_maybe_enable:
2|push {r0,r1,r2,r3,r4,r5,r6,lr}
4|mrs r4,primask
2|cpsid i
2|ldr r5,[<activation_descriptor>]
2|ldr r6,[<activation_header_pointer>]
2|ldr r0,[r6,#0]
2|cmp r0,#1
2|bne <activation_return>
2|ldr r0,[<activation_globals>]
2|ldrb r1,[r0,#0]
2|ldrb r2,[r6,#4]
2|cmp r1,r2
2|bne <activation_reject>
2|ldrb r1,[r0,#1]
2|movs r2,#3
2|cmp r1,r2
2|bhi <activation_reject>
2|ldr r0,[<activation_sensor>]
2|ldr r0,[r0,#0]
2|ldrb r1,[r0,#26]
2|ldrb r2,[r6,#6]
2|cmp r1,r2
2|bne <activation_reject>
2|ldr r6,[r5,#16]
2|ldr r0,[r6,#0]
2|movs r1,#1
2|ands r0,r1
2|bne <activation_reject>
2|ldr r0,[r6,#12]
2|cmp r0,#0
2|bne <activation_reject>
2|movs r1,#0
2|mvns r1,r1
2|ldr r0,[r6,#4]
2|cmp r0,r1
2|beq <activation_reject>
2|ldr r0,[r6,#8]
2|cmp r0,r1
2|beq <activation_reject>
2|ldr r0,[r5,#28]
2|cmp r0,#3
2|bne <activation_refresh>
2|ldr r0,[r5,#8]
2|ldr r0,[r0,#24]
2|ldr r1,[r6,#8]
2|cmp r0,r1
2|beq <activation_return>
activation_refresh:
2|ldr r0,[r5,#0]
4|bl <rt_invalidate>
2|ldr r0,[r5,#8]
2|ldr r1,[<activation_configuration_pointer>]
2|movs r2,#7
activation_copy:
2|ldr r3,[r1,#0]
2|str r3,[r0,#0]
2|adds r1,#4
2|adds r0,#4
2|subs r2,#1
2|bne <activation_copy>
2|ldr r0,[r5,#8]
2|ldr r1,[r6,#8]
2|str r1,[r0,#24]
2|movs r0,#3
2|str r0,[r5,#28]
2|b <activation_return>
activation_reject:
2|ldr r0,[r5,#28]
2|cmp r0,#0
2|beq <activation_return>
4|bl <integration_revoke>
activation_return:
4|bl <per_key_config>
4|dmb #0x1f
4|msr primask,r4
2|pop {r0,r1,r2,r3,r4,r5,r6,pc}
.align4
activation_descriptor:
.word 0x20004eb4
activation_header_pointer:
.word 0x0801f660
activation_globals:
.word 0x20002b10
activation_sensor:
.word 0x20004fdc
activation_configuration_pointer:
.word 0x0801f640
.org 0x0801f640
activation_configuration:
.word 0x00780000
.word 0x00100078
.word 0x00200020
.word 0x0fff0001
.word 0x00000010
.word 0x00000028
.word 0x00000000
.org 0x0801f660
activation_header:
.word 0x00000000
.word 0x11000301
.word 0x52544558
.word 0x00000001

; C5 diagnostic copy wrapper, status extension for W sensor17 only.
; Retains state/raw/baseline/scale. Replaces eight APC table entries with status.
.org 0x0801ff60
diagnostic_c5_copy:
2|push {r4,r5,r6,lr}
2|mov r4,r0
2|mov r5,r1
4|bl 0x080165d8
2|push {r0,r1}
2|cmp r5,#17
2|bne <diagnostic_return>
2|ldr r0,[<diagnostic_magic>]
2|strh r0,[r4,#10]
2|movs r0,#1
2|strh r0,[r4,#12]
2|ldr r5,[<diagnostic_globals>]
2|ldrb r0,[r5,#0]
2|ldrb r1,[r5,#1]
2|lsls r1,r1,#8
2|orrs r0,r1
2|strh r0,[r4,#14]
2|ldr r5,[<diagnostic_sensor>]
2|ldrb r0,[r5,#26]
2|ldr r5,[<diagnostic_descriptor>]
2|ldr r1,[r5,#28]
2|lsls r1,r1,#8
2|orrs r0,r1
2|strh r0,[r4,#16]
2|ldr r5,[<diagnostic_context>]
2|ldrb r0,[r5,#0]
2|mov r1,r5
2|adds r1,#32
2|ldrb r1,[r1,#0]
2|lsls r1,r1,#8
2|orrs r0,r1
2|strh r0,[r4,#18]
2|ldrh r0,[r5,#2]
2|strh r0,[r4,#20]
2|ldr r5,[<diagnostic_meta>]
2|ldrh r0,[r5,#8]
2|strh r0,[r4,#22]
2|ldr r5,[<diagnostic_config>]
2|ldrh r0,[r5,#24]
2|strh r0,[r4,#24]
diagnostic_return:
2|pop {r0,r1}
2|pop {r4,r5,r6,pc}
.align4
diagnostic_magic:
.word 0x00005254
diagnostic_globals:
.word 0x20002b10
diagnostic_sensor:
.word 0x20002d1e
diagnostic_descriptor:
.word 0x20004eb4
diagnostic_context:
.word 0x20004db0
diagnostic_meta:
.word 0x20004e74
diagnostic_config:
.word 0x20004e18

; Eight independent contexts; shared capture/metadata/config, single scanner owner.
; R0 sensor -> R0 supported0/1. Updates selected context and validated sensor pointers.
.org 0x0801f680
wasd_select:
2|push {r4,r5,r6,lr}
2|mov r4,r0
2|ldr r5,[<wasd_descriptor>]
2|ldr r6,[<wasd_control>]
4|bl <per_key_enabled>
2|cmp r0,#1
2|bne <wasd_select_no>
2|mov r0,r4
4|bl <per_key_index>
2|cmp r0,#8
2|bcs <wasd_select_no>
2|lsls r0,r0,#2
2|ldr r1,[<wasd_route_contexts>]
2|ldr r0,[r1,r0]
wasd_select_store:
2|str r0,[r5,#0]
2|str r4,[r6,#0]
2|mov r0,r4
2|movs r1,#30
2|muls r0,r1
2|ldr r1,[<wasd_sensor_base>]
2|adds r0,r0,r1
2|str r0,[r6,#4]
2|mov r0,r4
2|lsls r0,r0,#4
2|ldr r1,[<wasd_key_base>]
2|adds r0,r0,r1
2|str r0,[r6,#8]
2|movs r0,#1
2|pop {r4,r5,r6,pc}
wasd_select_no:
2|movs r0,#255
2|str r0,[r6,#0]
2|movs r0,#0
2|pop {r4,r5,r6,pc}
.align4
wasd_descriptor:
.word 0x20004eb4
wasd_control:
.word 0x20004fd8
wasd_route_contexts:
.word 0x0801f5c0
wasd_extra_context:
.word 0x20004edc
wasd_w_context:
.word 0x20004db0
wasd_sensor_base:
.word 0x20002b20
wasd_key_base:
.word 0x200011ac

; Caller already protects mutation notification or owns the scanner.
.org 0x0801f580
wasd_invalidate_all:
2|push {r4,r5,r6,lr}
2|ldr r4,[<wasd_contexts_pointer>]
2|movs r5,#8
wasd_invalidate_loop:
2|ldr r0,[r4,#0]
4|bl <rt_invalidate>
2|adds r4,#4
2|subs r5,#1
2|bne <wasd_invalidate_loop>
2|movs r0,#0
2|pop {r4,r5,r6,pc}
.align4
wasd_contexts_pointer:
.word 0x0801f5c0
.org 0x0801f5c0
wasd_contexts:
.word 0x20004db0
.word 0x20004edc
.word 0x20004f00
.word 0x20004f24
.word 0x20004f48
.word 0x20004f6c
.word 0x20004f90
.word 0x20004fb4

; Eight immutable rows: sensor, release/press, exact enable flag.
.org 0x0801f800
per_key_index:
2|push {r1,r2,r3,lr}
2|mov r3,r0
2|ldr r1,[<eight_table_index>]
2|movs r0,#0
eight_find:
2|ldr r2,[r1,#0]
2|cmp r2,r3
2|beq <eight_index_end>
2|adds r1,#12
2|adds r0,#1
2|cmp r0,#8
2|bcc <eight_find>
2|movs r0,#255
eight_index_end:
2|pop {r1,r2,r3,pc}
.align4
eight_table_index:
.word 0x0801fc10
.org 0x0801f840
per_key_enabled:
2|push {r1,r2,r3,lr}
4|bl <per_key_index>
2|cmp r0,#8
2|bcs <eight_disabled>
2|movs r1,#12
2|muls r0,r1
2|ldr r1,[<eight_table_enable>]
2|adds r0,r0,r1
2|ldr r0,[r0,#8]
2|cmp r0,#1
2|beq <eight_enabled_end>
eight_disabled:
2|movs r0,#0
eight_enabled_end:
2|pop {r1,r2,r3,pc}
.align4
eight_table_enable:
.word 0x0801fc10
.org 0x0801f880
per_key_config:
2|push {r0,r1,r2,r3,r4,lr}
2|ldr r0,[<per_key_descriptor>]
2|ldr r0,[r0,#28]
2|cmp r0,#3
2|bne <per_key_end>
2|ldr r0,[<per_key_control>]
2|ldr r0,[r0,#0]
4|bl <per_key_index>
2|cmp r0,#8
2|bcs <per_key_end>
2|movs r1,#12
2|muls r0,r1
2|ldr r1,[<per_key_table_pointer>]
2|adds r0,r0,r1
2|ldr r2,[<per_key_cfg>]
2|ldrh r1,[r0,#4]
2|strh r1,[r2,#2]
2|ldrh r1,[r0,#6]
2|strh r1,[r2,#4]
per_key_end:
2|pop {r0,r1,r2,r3,r4,pc}
.align4
per_key_descriptor:
.word 0x20004eb4
per_key_control:
.word 0x20004fd8
per_key_table_pointer:
.word 0x0801fc10
per_key_cfg:
.word 0x20004e18
.org 0x0801fc10
per_key_table:
.word 0x00000011
.word 0x00300030
.word 0x00000001
.word 0x0000001e
.word 0x00300030
.word 0x00000001
.word 0x0000001f
.word 0x00300030
.word 0x00000001
.word 0x00000020
.word 0x00300030
.word 0x00000001
.word 0x00000010
.word 0x00300030
.word 0x00000001
.word 0x00000012
.word 0x00300030
.word 0x00000001
.word 0x0000002b
.word 0x00300030
.word 0x00000001
.word 0x0000003c
.word 0x00300030
.word 0x00000001
