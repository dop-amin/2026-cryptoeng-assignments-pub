// SPDX-License-Identifier: Apache-2.0 or CC0-1.0
#include "hal.h"
#include <CMSDK_CM4.h>
#include <sys/cdefs.h>

#define BAUD 38400

/* Default clock on the MPS2 boards seems to be 25MHz */
#ifndef SYSTEM_CLOCK
#define SYSTEM_CLOCK 25000000UL
#endif

/* The startup file calls a SystemInit function. */
void SystemInit(void) {
    /* Enable the FPU */
    SCB->CPACR |= ((3UL << 10 * 2) | /* set CP10 Full Access */
                   (3UL << 11 * 2)); /* set CP11 Full Access */
    /* Enable UART */
    CMSDK_GPIO0->ALTFUNCSET |= 1u;
    CMSDK_GPIO0->ALTFUNCSET |= 2u;
    CMSDK_UART0->BAUDDIV = SYSTEM_CLOCK / BAUD;
    CMSDK_UART0->CTRL |= 1 << CMSDK_UART_CTRL_RXEN_Pos;
    CMSDK_UART0->CTRL |= 1 << CMSDK_UART_CTRL_TXEN_Pos;
    /* Enable SysTick Timer */
    SysTick->LOAD = 0xFFFFFFu;
    NVIC_SetPriority(SysTick_IRQn, (1UL << __NVIC_PRIO_BITS) - 1UL);
    NVIC_EnableIRQ(SysTick_IRQn);
    SysTick->VAL = 0UL;
    SysTick->CTRL = SysTick_CTRL_CLKSOURCE_Msk | SysTick_CTRL_TICKINT_Msk | SysTick_CTRL_ENABLE_Msk;
}

static volatile unsigned long long overflowcnt = 0;

/* SysTick Interrupt */
void SysTick_Handler(void) { ++overflowcnt; }

uint64_t hal_get_time() {
    while (1) {
        unsigned long long before = overflowcnt;
        unsigned long long result = (before + 1) * 16777216llu - SysTick->VAL;
        if (overflowcnt == before) {
            return result;
        }
    }
}

void hal_setup(const enum clock_mode clock) {
    (void)clock;
    // No additional setup needed for QEMU - SystemInit() is called by startup code

    // wait for the first systick overflow
    // improves reliability of the benchmarking scripts
    unsigned long long old = overflowcnt;
    while (old == overflowcnt)
        ;
}

static inline void uart_putc(int c) {
    while (CMSDK_UART0->STATE & CMSDK_UART_STATE_TXBF_Msk)
        ;
    CMSDK_UART0->DATA = c & 0xFFu;
}

void hal_send_str(const char *in) {
    const char *cur = in;
    while (*cur) {
        uart_putc(*cur);
        cur += 1;
    }
    uart_putc('\n');
}

/**
 * @brief Receive a string from the host via UART.
 *
 * Blocks until a newline ('\n' or '\r') or buffer full.
 *
 * @param[out] buf    Destination buffer
 * @param[in]  len    Buffer length (including space for '\0')
 */
uint32_t hal_recv_str(char *buf, uint32_t len) {
    uint32_t i = 0;

    if (len == 0)
        return 0;

    while (i < (len - 1)) {
        // Wait for data (wait while RX buffer is NOT full, i.e., empty)
        while (!(CMSDK_UART0->STATE & CMSDK_UART_STATE_RXBF_Msk))
            ;
        char c = CMSDK_UART0->DATA & 0xFFu;

        // Stop at newline or carriage return
        if (c == '\n' || c == '\r')
            break;

        buf[i++] = c;
    }

    buf[i] = '\0'; // Null-terminate
    return i;      // Return actual number of characters read
}

// Semihosting support for QEMU exit
static const uint32_t REPORT_EXCEPTION = 0x18;
static const uint32_t ApplicationExit = 0x20026;

// Do a system call towards QEMU or the debugger.
static uint32_t semihosting_syscall(uint32_t nr, const uint32_t arg) {
    __asm__ volatile("mov r0, %[nr]\n"
                     "mov r1, %[arg]\n"
                     "bkpt 0xAB\n"
                     "mov %[nr], r0\n"
                     : [nr] "+r"(nr)
                     : [arg] "r"(arg)
                     : "0", "1");
    return nr;
}

// Register a destructor that will call qemu telling them that the program
// has exited successfully.
static void __attribute__((destructor)) semihosting_exit(void) {
    semihosting_syscall(REPORT_EXCEPTION, ApplicationExit);
}

// Exception handlers that exit QEMU with error messages
void NMI_Handler(void) {
    hal_send_str("NMI_Handler");
    semihosting_syscall(REPORT_EXCEPTION, ApplicationExit);
}

void HardFault_Handler(void) {
    hal_send_str("HardFault_Handler");
    semihosting_syscall(REPORT_EXCEPTION, ApplicationExit);
}

void MemManage_Handler(void) {
    hal_send_str("MemManage_Handler");
    semihosting_syscall(REPORT_EXCEPTION, ApplicationExit);
}

void BusFault_Handler(void) {
    hal_send_str("BusFault_Handler");
    semihosting_syscall(REPORT_EXCEPTION, ApplicationExit);
}

void UsageFault_Handler(void) {
    hal_send_str("UsageFault_Handler");
    semihosting_syscall(REPORT_EXCEPTION, ApplicationExit);
}

void SVC_Handler(void) {
    hal_send_str("SVC_Handler");
    semihosting_syscall(REPORT_EXCEPTION, ApplicationExit);
}

void DebugMon_Handler(void) {
    hal_send_str("DebugMon_Handler");
    semihosting_syscall(REPORT_EXCEPTION, ApplicationExit);
}

void PendSV_Handler(void) {
    hal_send_str("PendSV_Handler");
    semihosting_syscall(REPORT_EXCEPTION, ApplicationExit);
}

void Default_Handler(void) { semihosting_syscall(REPORT_EXCEPTION, ApplicationExit); }

/* End of BSS is where the heap starts (defined in the linker script) */
extern char end;
static char *heap_end = &end;

size_t hal_get_stack_size(void) {
    register char *cur_stack;
    __asm__ volatile("mov %0, sp" : "=r"(cur_stack));
    return cur_stack - heap_end;
}

const uint32_t stackpattern = 0xDEADBEEFlu;

static void *last_sp = NULL;

void hal_spraystack(void) {

    char *_heap_end = heap_end;
    asm volatile("mov %0, sp\n"
                 ".L%=:\n\t"
                 "str %2, [%1], #4\n\t"
                 "cmp %1, %0\n\t"
                 "blt .L%=\n\t"
                 : "+r"(last_sp), "+r"(_heap_end)
                 : "r"(stackpattern)
                 : "cc", "memory");
}

size_t hal_checkstack(void) {
    size_t result = 0;
    asm volatile("sub %0, %1, %2\n"
                 ".L%=:\n\t"
                 "ldr ip, [%2], #4\n\t"
                 "cmp ip, %3\n\t"
                 "ite eq\n\t"
                 "subeq %0, #4\n\t"
                 "bne .LE%=\n\t"
                 "cmp %2, %1\n\t"
                 "blt .L%=\n\t"
                 ".LE%=:\n"
                 : "+r"(result)
                 : "r"(last_sp), "r"(heap_end), "r"(stackpattern)
                 : "ip", "cc");
    return result;
}

/* Implement some system calls to shut up the linker warnings */

#include <errno.h>
#include <sys/stat.h>

#undef errno
extern int errno;

/* Syscall wrapper prototypes */
void *__wrap__sbrk(int incr);
int __wrap__open(char *file, int flags, int mode);
int __wrap__close(int fd);
int __wrap__fstat(int fd, struct stat *buf);
int __wrap__getpid(void);
int __wrap__isatty(int file);
int __wrap__kill(int pid, int sig);
int __wrap__lseek(int fd, int ptr, int dir);
int __wrap__read(int fd, char *ptr, int len);
int __wrap__write(int fd, const char *ptr, int len);

int __wrap__open(char *file, int flags, int mode) {
    (void)file;
    (void)flags;
    (void)mode;
    errno = ENOSYS;
    return -1;
}

int __wrap__close(int fd) {
    errno = ENOSYS;
    (void)fd;
    return -1;
}

int __wrap__fstat(int fd, struct stat *buf) {
    (void)fd;
    (void)buf;
    errno = ENOSYS;
    return -1;
}

int __wrap__getpid(void) {
    errno = ENOSYS;
    return -1;
}

int __wrap__isatty(int file) {
    (void)file;
    errno = ENOSYS;
    return 0;
}

int __wrap__kill(int pid, int sig) {
    (void)pid;
    (void)sig;
    errno = ENOSYS;
    return -1;
}

int __wrap__lseek(int fd, int ptr, int dir) {
    (void)fd;
    (void)ptr;
    (void)dir;
    errno = ENOSYS;
    return -1;
}

int __wrap__read(int fd, char *ptr, int len) {
    (void)fd;
    (void)ptr;
    (void)len;
    errno = ENOSYS;
    return -1;
}

int __wrap__write(int fd, const char *ptr, int len) {
    (void)fd;
    (void)ptr;
    (void)len;
    errno = ENOSYS;
    return -1;
}

void *__wrap__sbrk(int incr) {
    char *prev_heap_end;

    prev_heap_end = heap_end;
    heap_end += incr;

    return (void *)prev_heap_end;
}
