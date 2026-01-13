// SPDX-License-Identifier: Apache-2.0 or CC0-1.0
#include "hal.h"
#include <sys/cdefs.h>

#define SERIAL_BAUD 38400

#include <libopencm3/cm3/dwt.h>
#include <libopencm3/cm3/nvic.h>
#include <libopencm3/cm3/systick.h>

#include <libopencm3/stm32/flash.h>
#include <libopencm3/stm32/gpio.h>
#include <libopencm3/stm32/pwr.h>
#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/rng.h>
#include <libopencm3/stm32/usart.h>

#define SERIAL_GPIO GPIOG
#define SERIAL_USART LPUART1
#define SERIAL_PINS (GPIO8 | GPIO7)
#define NUCLEO_L4R5_BOARD

/* Patched function for newer PLL not yet supported by opencm3 */
static void _rcc_set_main_pll(uint32_t source, uint32_t pllm, uint32_t plln, uint32_t pllp,
                              uint32_t pllq, uint32_t pllr) {
    RCC_PLLCFGR = (RCC_PLLCFGR_PLLM(pllm) << RCC_PLLCFGR_PLLM_SHIFT) |
                  (plln << RCC_PLLCFGR_PLLN_SHIFT) | ((pllp & 0x1Fu) << 27u) | /* NEWER PLLP */
                  (source << RCC_PLLCFGR_PLLSRC_SHIFT) | (pllq << RCC_PLLCFGR_PLLQ_SHIFT) |
                  (pllr << RCC_PLLCFGR_PLLR_SHIFT) | RCC_PLLCFGR_PLLREN;
}

#define _RCC_CAT(A, B) A##_##B
#define RCC_ID(NAME) _RCC_CAT(RCC, NAME)

__attribute__((unused)) static uint32_t _clock_freq;

#ifdef STM32F2
extern uint32_t rcc_apb1_frequency;
extern uint32_t rcc_apb2_frequency;
#endif

static void clock_setup(enum clock_mode clock) {
    rcc_periph_clock_enable(RCC_PWR);
    rcc_periph_clock_enable(RCC_SYSCFG);
    pwr_set_vos_scale(PWR_SCALE1);
    /* The L4R5ZI chip also needs the R1MODE bit in PWR_CR5 register set, but
       OpenCM3 doesn't support this yet. But luckily the default value for the bit
       is 1. */
    switch (clock) {
    case CLOCK_BENCHMARK:
        /* Benchmark straight from the HSI16 without prescaling */
        rcc_osc_on(RCC_HSI16);
        rcc_wait_for_osc_ready(RCC_HSI16);
        rcc_ahb_frequency = 20000000;
        rcc_apb1_frequency = 20000000;
        rcc_apb2_frequency = 20000000;
        _clock_freq = 20000000;
        rcc_set_hpre(RCC_CFGR_HPRE_NODIV);
        rcc_set_ppre1(RCC_CFGR_PPRE_NODIV);
        rcc_set_ppre2(RCC_CFGR_PPRE_NODIV);
        rcc_osc_off(RCC_PLL);
        while (rcc_is_osc_ready(RCC_PLL))
            ;
        /* Configure the PLL oscillator (use CUBEMX tool -> scale HSI16 to 20MHz). */
        _rcc_set_main_pll(RCC_PLLCFGR_PLLSRC_HSI16, 1, 10, 2, RCC_PLLCFGR_PLLQ_DIV2,
                          RCC_PLLCFGR_PLLR_DIV8);
        /* Enable PLL oscillator and wait for it to stabilize. */
        rcc_osc_on(RCC_PLL);
        flash_dcache_enable();
        flash_icache_enable();
        flash_set_ws(FLASH_ACR_LATENCY_0WS);
        flash_prefetch_enable();
        rcc_set_sysclk_source(RCC_CFGR_SW_PLL);
        rcc_wait_for_sysclk_status(RCC_PLL);
        break;
    case CLOCK_FAST:
    default:
        rcc_osc_on(RCC_HSI16);
        rcc_wait_for_osc_ready(RCC_HSI16);
        rcc_ahb_frequency = 120000000;
        rcc_apb1_frequency = 120000000;
        rcc_apb2_frequency = 120000000;
        _clock_freq = 120000000;
        rcc_set_hpre(RCC_CFGR_HPRE_NODIV);
        rcc_set_ppre1(RCC_CFGR_PPRE_NODIV);
        rcc_set_ppre2(RCC_CFGR_PPRE_NODIV);
        rcc_osc_off(RCC_PLL);
        while (rcc_is_osc_ready(RCC_PLL))
            ;
        /* Configure the PLL oscillator (use CUBEMX tool -> scale HSI16 to 120MHz). */
        _rcc_set_main_pll(RCC_PLLCFGR_PLLSRC_HSI16, 1, 15, 2, RCC_PLLCFGR_PLLQ_DIV2,
                          RCC_PLLCFGR_PLLR_DIV2);
        /* Enable PLL oscillator and wait for it to stabilize. */
        rcc_osc_on(RCC_PLL);
        rcc_wait_for_osc_ready(RCC_PLL);
        flash_dcache_enable();
        flash_icache_enable();
        flash_set_ws(0x05);
        flash_prefetch_enable();
        rcc_set_sysclk_source(RCC_CFGR_SW_PLL);
        rcc_wait_for_sysclk_status(RCC_PLL);
        break;
    }
    rcc_osc_on(RCC_HSI48); /* HSI48 must always be on for RNG */
    rcc_wait_for_osc_ready(RCC_HSI48);
    rcc_periph_clock_enable(RCC_RNG);
    rcc_set_clock48_source(RCC_CCIPR_CLK48SEL_HSI48);
    rng_enable();
}

static void usart_setup(void) {
    rcc_periph_clock_enable(RCC_GPIOG);
    rcc_periph_clock_enable(RCC_LPUART1);

    PWR_CR2 |= PWR_CR2_IOSV;
    gpio_set_output_options(SERIAL_GPIO, GPIO_OTYPE_PP, GPIO_OSPEED_100MHZ, SERIAL_PINS);
    gpio_set_af(SERIAL_GPIO, GPIO_AF8, SERIAL_PINS);
    gpio_mode_setup(SERIAL_GPIO, GPIO_MODE_AF, GPIO_PUPD_NONE, SERIAL_PINS);
    usart_set_baudrate(SERIAL_USART, SERIAL_BAUD);
    usart_set_databits(SERIAL_USART, 8);
    usart_set_stopbits(SERIAL_USART, USART_STOPBITS_1);
    usart_set_mode(SERIAL_USART, USART_MODE_TX_RX);
    usart_set_parity(SERIAL_USART, USART_PARITY_NONE);
    usart_set_flow_control(SERIAL_USART, USART_FLOWCONTROL_NONE);
    usart_disable_rx_interrupt(SERIAL_USART);
    usart_disable_tx_interrupt(SERIAL_USART);
    usart_enable(SERIAL_USART);
}

static void systick_setup(void) {
    /* Systick is always the same on libopencm3 */
    systick_set_clocksource(STK_CSR_CLKSOURCE_AHB);
    systick_set_reload(0xFFFFFFu);
    systick_interrupt_enable();
    systick_counter_enable();
}
static volatile unsigned long long overflowcnt = 0;
void hal_setup(const enum clock_mode clock) {
    clock_setup(clock);
    usart_setup();
    systick_setup();

    // wait for the first systick overflow
    // improves reliability of the benchmarking scripts since it makes it much
    // less likely that the host will miss the start of the output
    unsigned long long old = overflowcnt;
    while (old == overflowcnt)
        ;
}

void hal_send_str(const char *in) {
    const char *cur = in;
    while (*cur) {
        usart_send_blocking(SERIAL_USART, *cur);
        cur += 1;
    }
    usart_send_blocking(SERIAL_USART, '\n');
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
        char c = usart_recv_blocking(SERIAL_USART);
        // Stop at newline or carriage return
        if (c == '\n' || c == '\r')
            break;

        buf[i++] = c;
    }

    buf[i] = '\0'; // Null-terminate
    return len;
}

void sys_tick_handler(void) { ++overflowcnt; }

uint64_t hal_get_time() {
    while (true) {
        unsigned long long before = overflowcnt;
        unsigned long long result = (before + 1) * 16777216llu - systick_get_value();
        if (overflowcnt == before) {
            return result;
        }
    }
}

/* End of BSS is where the heap starts (defined in the linker script) */
extern char end;
static char *heap_end = &end;

size_t hal_get_stack_size(void) {
    register char *cur_stack;
    asm volatile("mov %0, sp" : "=r"(cur_stack));
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