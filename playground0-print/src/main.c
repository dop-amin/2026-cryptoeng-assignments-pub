#include "hal.h"
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
    hal_send_str("Playground 0: Print Demo\n");
    hal_send_str("====================================\n\n");

    /* Send the fixed message */
    hal_send_str("Hello from the Nucleo board!\n");
    hal_send_str("This is a simple demo of UART communication.\n");

    /* Loop forever (prevents return from main which causes issues) */
    while (1) {
        /* Idle */
    }
}
