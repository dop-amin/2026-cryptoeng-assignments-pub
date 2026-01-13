#include "hal.h"
#include "myjasmin_wrapper.h"
#include <stdio.h>

/* Platform-specific includes */
#ifndef QEMU_PLATFORM
#include <libopencm3/cm3/nvic.h>
#include <libopencm3/cm3/systick.h>
#endif

int main(void) {
    /* Initialize platform */
    hal_setup(CLOCK_BENCHMARK);

    /* Wait a moment for UART capture to start */
    uint64_t start = hal_get_time();
    while (hal_get_time() - start < 25000000) {
        /* Wait for 25000000 cycles */
    }

    /* Welcome message */
    hal_send_str("\n");
    hal_send_str("====================================\n");
    hal_send_str("Playground 2: Jasmin Demo\n");
    hal_send_str("====================================\n\n");

    /* Run benchmark with Jasmin function */
    uint32_t iterations = 1000;

    uint64_t start_cycles = hal_get_time();
    // volatile disallows compiler from optimizing result away
    volatile uint32_t result = 0;
    for (uint32_t i = 0; i < iterations; i++) {
        result = increment_jasmin(result);
    }

    uint64_t end_cycles = hal_get_time();
    uint32_t total_cycles = (uint32_t)(end_cycles - start_cycles);
    uint32_t cycles_per_iter = total_cycles / iterations;

    char response[128];
    snprintf(response, sizeof(response),
             "Jasmin increment called %lu times\n"
             "Result: %lu\n"
             "Took %lu cycles (%lu per iteration)\n",
             (unsigned long)iterations, (unsigned long)result, (unsigned long)total_cycles,
             (unsigned long)cycles_per_iter);
    hal_send_str(response);

    /* Loop forever (prevents return from main which causes issues) */
    while (1) {
        /* Idle */
    }
}
