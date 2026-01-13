#include "hal.h"
#include <stdio.h>

/* Platform-specific includes */
#ifndef QEMU_PLATFORM
#include <libopencm3/cm3/nvic.h>
#include <libopencm3/cm3/systick.h>
#endif

uint32_t placeholder_function(uint32_t input) {
    // A simple placeholder function that does minimal work
    // This is just for demonstrating how benchmarking works
    return input + 1;
}

int main(void) {
    /* Initialize platform */
    hal_setup(CLOCK_BENCHMARK);

    /* Wait a moment for UART capture to start (especially important for QEMU) */
    uint64_t start = hal_get_time();
    while (hal_get_time() - start < 25000000) {
        /* Wait ~1 second at 25MHz */
    }

    /* Welcome message */
    hal_send_str("\n");
    hal_send_str("====================================\n");
    hal_send_str("Playground 1: Bench Demo\n");
    hal_send_str("====================================\n\n");

    /* Run benchmark */
    uint32_t iterations = 1000;

    uint64_t start_cycles = hal_get_time();
    // volatile disallows compiler from optimizing result (and the corresponding
    // computation) away
    volatile uint32_t result;
    for (int i = 0; i < iterations; i++) {
        result = placeholder_function(result);
    }

    uint64_t end_cycles = hal_get_time();
    uint32_t total_cycles = (uint32_t)(end_cycles - start_cycles);
    uint32_t cycles_per_iter = total_cycles / iterations;

    char response[64];
    snprintf(response, sizeof(response), "Took %lu cycles (%lu per iteration)\n",
             (unsigned long)total_cycles, (unsigned long)cycles_per_iter);
    hal_send_str(response);

    /* Loop forever (prevents return from main which causes issues) */
    while (1) {
        /* Idle */
    }
}
