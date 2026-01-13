#include <stdio.h>
#include <string.h>

#include "hal.h"
#include "sum_c.h"
#include "sum_wrapper.h"

/* Platform-specific includes */
#ifndef QEMU_PLATFORM
#include <libopencm3/cm3/nvic.h>
#include <libopencm3/cm3/systick.h>
#endif

/* Command buffer */
#define CMD_BUFFER_SIZE 512
static char cmd_buffer[CMD_BUFFER_SIZE];

#define BENCH_SEED 0x12345678
#define BENCH_NUM_INT 1000

/* Test data buffers */
#define MAX_INT 1024
static uint32_t integers[MAX_INT] __attribute__((aligned(4)));

/**
 * Simple xorshift32 PRNG - must match Python implementation
 */
static inline uint32_t xorshift32_next(uint32_t *state, uint32_t mod) {
    uint32_t x = *state;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    *state = x;
    if (mod != 0xFFFFFFFF) {
        return (x % mod);
    } else {
        return x;
    }
}

/**
 * Generate array of integers using PRNG
 */
static void generate_integers(uint32_t seed, uint32_t count, uint32_t mod) {
    uint32_t state = seed;
    for (uint32_t i = 0; i < count && i < MAX_INT; i++) {
        integers[i] = xorshift32_next(&state, mod);
    }
}

/* Byte swap for endianness conversion */
static inline uint32_t bswap32(uint32_t x) {
    return ((x & 0xFF000000) >> 24) | ((x & 0x00FF0000) >> 8) | ((x & 0x0000FF00) << 8) |
           ((x & 0x000000FF) << 24);
}

/**
 * Parse hex string to uint32 array (hex bytes interpreted as big-endian for transmission)
 * Each 8 hex chars represent 4 bytes sent in big-endian order by Python
 */
static size_t parse_hex_to_u32(const char *hex_str, uint32_t *output, size_t max_words) {
    size_t word_count = 0;
    size_t hex_len = strlen(hex_str);

    for (size_t i = 0; i < hex_len && word_count < max_words; i += 8) {
        uint8_t bytes[4] = {0};

        /* Parse 8 hex digits as 4 bytes */
        for (int j = 0; j < 4 && (i + j * 2 + 1) < hex_len; j++) {
            char hi = hex_str[i + j * 2];
            char lo = hex_str[i + j * 2 + 1];
            uint8_t hi_val, lo_val;

            /* Parse high nibble */
            if (hi >= '0' && hi <= '9')
                hi_val = hi - '0';
            else if (hi >= 'a' && hi <= 'f')
                hi_val = hi - 'a' + 10;
            else if (hi >= 'A' && hi <= 'F')
                hi_val = hi - 'A' + 10;
            else
                continue;

            /* Parse low nibble */
            if (lo >= '0' && lo <= '9')
                lo_val = lo - '0';
            else if (lo >= 'a' && lo <= 'f')
                lo_val = lo - 'a' + 10;
            else if (lo >= 'A' && lo <= 'F')
                lo_val = lo - 'A' + 10;
            else
                continue;

            bytes[j] = (hi_val << 4) | lo_val;
        }

        /* Construct big-endian uint32 from transmitted bytes */
        output[word_count++] = ((uint32_t)bytes[0] << 24) | ((uint32_t)bytes[1] << 16) |
                               ((uint32_t)bytes[2] << 8) | (uint32_t)bytes[3];
    }

    return word_count;
}

/**
 * Parse hex string to byte array
 * Returns number of bytes parsed
 */
static size_t parse_hex_to_bytes(const char *hex_str, uint8_t *output, size_t max_bytes) {
    size_t byte_count = 0;
    size_t hex_len = strlen(hex_str);

    for (size_t i = 0; i < hex_len && byte_count < max_bytes; i += 2) {
        if (i + 1 >= hex_len)
            break;

        char hi = hex_str[i];
        char lo = hex_str[i + 1];
        uint8_t hi_val, lo_val;

        /* Stop at space or newline */
        if (hi == ' ' || hi == '\n' || hi == '\r')
            break;
        if (lo == ' ' || lo == '\n' || lo == '\r')
            break;

        /* Parse high nibble */
        if (hi >= '0' && hi <= '9')
            hi_val = hi - '0';
        else if (hi >= 'a' && hi <= 'f')
            hi_val = hi - 'a' + 10;
        else if (hi >= 'A' && hi <= 'F')
            hi_val = hi - 'A' + 10;
        else
            break; /* Stop on invalid char instead of continue */

        /* Parse low nibble */
        if (lo >= '0' && lo <= '9')
            lo_val = lo - '0';
        else if (lo >= 'a' && lo <= 'f')
            lo_val = lo - 'a' + 10;
        else if (lo >= 'A' && lo <= 'F')
            lo_val = lo - 'A' + 10;
        else
            break; /* Stop on invalid char instead of continue */

        output[byte_count++] = (hi_val << 4) | lo_val;
    }

    return byte_count;
}

/**
 * Handle TEST_SUM* commands
 * Format: TEST_SUM_X <seed_hex> <count_hex> <mod_hex>
 * seed_hex: 8 hex chars (4 bytes, big-endian)
 * count_hex: 8 hex chars (4 bytes, big-endian)
 * mod_hex: 8 hex chars (4 bytes, big-endian)
 */
static void handle_test_sumc(const char *args) {
    /* Parse seed and count (2 uint32 values = 8 bytes) */
    uint32_t params[3];
    size_t parsed = parse_hex_to_u32(args, params, 3);

    if (parsed != 3) {
        hal_send_str("ERR Invalid parameters\n");
        return;
    }

    uint32_t seed = params[0];
    uint32_t count = params[1];
    uint32_t mod = params[2];

    if (count == 0 || count > MAX_INT) {
        hal_send_str("ERR Invalid count\n");
        return;
    }

    /* Generate integers using PRNG */
    generate_integers(seed, count, mod);

    /* Compute sum */
    uint32_t res = sumc(integers, count);

    /* Send result (convert uint32 to big-endian hex bytes) */
    char response[15]; /* "OK " + 8 hex digits + "\n" + null terminator */
    snprintf(response, sizeof(response), "OK %02x%02x%02x%02x\n", (unsigned)((res >> 24) & 0xFF),
             (unsigned)((res >> 16) & 0xFF), (unsigned)((res >> 8) & 0xFF), (unsigned)(res & 0xFF));
    hal_send_str(response);
    return;
}

static void handle_test_sumjasmin(const char *args) {
    /* Parse seed and count (3 uint32 values = 12 bytes) */
    uint32_t params[3];
    size_t parsed = parse_hex_to_u32(args, params, 3);

    if (parsed != 3) {
        hal_send_str("ERR Invalid parameters\n");
        return;
    }

    uint32_t seed = params[0];
    uint32_t count = params[1];
    uint32_t mod = params[2];

    if (count == 0 || count > MAX_INT) {
        hal_send_str("ERR Invalid count\n");
        return;
    }

    /* Generate integers using PRNG */
    generate_integers(seed, count, mod);

    /* Compute sum */
    uint32_t res = sum_jasmin(integers, count);

    /* Send result (convert uint32 to big-endian hex bytes) */
    char response[15]; /* "OK " + 8 hex digits + "\n" + null terminator */
    snprintf(response, sizeof(response), "OK %02x%02x%02x%02x\n", (unsigned)((res >> 24) & 0xFF),
             (unsigned)((res >> 16) & 0xFF), (unsigned)((res >> 8) & 0xFF), (unsigned)(res & 0xFF));
    hal_send_str(response);
    return;
}

static void handle_test_sumjasminfast(const char *args) {
    /* Parse seed and count (3 uint32 values = 12 bytes) */
    uint32_t params[3];
    size_t parsed = parse_hex_to_u32(args, params, 3);

    if (parsed != 3) {
        hal_send_str("ERR Invalid parameters\n");
        return;
    }

    uint32_t seed = params[0];
    uint32_t count = params[1];
    uint32_t mod = params[2];

    if (count == 0 || count > MAX_INT) {
        hal_send_str("ERR Invalid count\n");
        return;
    }

    /* Generate integers using PRNG */
    generate_integers(seed, count, mod);

    /* Compute sum */
    uint32_t res = sum_jasmin_fast(integers, count);

    /* Send result (convert uint32 to big-endian hex bytes) */
    char response[15]; /* "OK " + 8 hex digits + "\n" + null terminator */
    snprintf(response, sizeof(response), "OK %02x%02x%02x%02x\n", (unsigned)((res >> 24) & 0xFF),
             (unsigned)((res >> 16) & 0xFF), (unsigned)((res >> 8) & 0xFF), (unsigned)(res & 0xFF));
    hal_send_str(response);
    return;
}

/**
 * Handle BENCHMARK_SUM_C command
 */
static void handle_benchmark_sumc(const char *args) {
    int iterations;

    if (sscanf(args, "%d", &iterations) != 1 || iterations <= 0) {
        hal_send_str("ERR Invalid iteration count\n");
        return;
    }

    /* Initialize test data using PRNG (use fixed seed for benchmarking) */
    /* Use mod=0xFFFFFFFF for full 32-bit range in benchmarking */
    generate_integers(BENCH_SEED, BENCH_NUM_INT, 0xFFFFFFFF);

    /* Run benchmark */
    uint64_t start_cycles = hal_get_time();
    volatile uint32_t result;
    for (int i = 0; i < iterations; i++) {
        result = sumc(integers, BENCH_NUM_INT);
    }

    uint64_t end_cycles = hal_get_time();
    uint32_t total_cycles = (uint32_t)(end_cycles - start_cycles);

    /* Send result */
    char response[64];
    snprintf(response, sizeof(response), "OK cycles=%lu\n", (unsigned long)total_cycles);
    hal_send_str(response);
}

/**
 * Handle BENCHMARK_SUM_JASMIN command
 */
static void handle_benchmark_sumjasmin(const char *args) {
    int iterations;

    if (sscanf(args, "%d", &iterations) != 1 || iterations <= 0) {
        hal_send_str("ERR Invalid iteration count\n");
        return;
    }

    /* Initialize test data using PRNG (use fixed seed for benchmarking) */
    /* Use mod=0xFFFFFFFF for full 32-bit range in benchmarking */
    generate_integers(BENCH_SEED, BENCH_NUM_INT, 0xFFFFFFFF);

    /* Run benchmark */
    uint64_t start_cycles = hal_get_time();
    volatile uint32_t result;
    for (int i = 0; i < iterations; i++) {
        result = sum_jasmin(integers, BENCH_NUM_INT);
    }

    uint64_t end_cycles = hal_get_time();
    uint32_t total_cycles = (uint32_t)(end_cycles - start_cycles);

    /* Send result */
    char response[64];
    snprintf(response, sizeof(response), "OK cycles=%lu\n", (unsigned long)total_cycles);
    hal_send_str(response);
}

/**
 * Handle BENCHMARK_SUM_JASMIN_FAST command
 */
static void handle_benchmark_sumjasminfast(const char *args) {
    int iterations;

    if (sscanf(args, "%d", &iterations) != 1 || iterations <= 0) {
        hal_send_str("ERR Invalid iteration count\n");
        return;
    }

    /* Initialize test data using PRNG (use fixed seed for benchmarking) */
    /* Use mod=0xFFFFFFFF for full 32-bit range in benchmarking */
    generate_integers(BENCH_SEED, BENCH_NUM_INT, 0xFFFFFFFF);

    /* Run benchmark */
    uint64_t start_cycles = hal_get_time();
    volatile uint32_t result;
    for (int i = 0; i < iterations; i++) {
        result = sum_jasmin_fast(integers, BENCH_NUM_INT);
    }

    uint64_t end_cycles = hal_get_time();
    uint32_t total_cycles = (uint32_t)(end_cycles - start_cycles);

    /* Send result */
    char response[64];
    snprintf(response, sizeof(response), "OK cycles=%lu\n", (unsigned long)total_cycles);
    hal_send_str(response);
}

/**
 * Handle TEST_HELLO command
 */
static void handle_hello_world(const char *args) { hal_send_str("Hello host!\n"); }

/**
 * Handle RESET command
 */
static void handle_reset(void) {
    memset(integers, 0, sizeof(integers));
    hal_send_str("OK\n");
}

/**
 * Process a command
 */
static void process_command(const char *cmd) {
    if (strncmp(cmd, "TEST_HELLO ", 11) == 0) {
        handle_hello_world(cmd + 11);
    } else if (strncmp(cmd, "TEST_SUM_C ", 11) == 0) {
        handle_test_sumc(cmd + 11);
    } else if (strncmp(cmd, "TEST_SUM_JASMIN ", 16) == 0) {
        handle_test_sumjasmin(cmd + 16);
    } else if (strncmp(cmd, "TEST_SUM_JASMIN_FAST ", 21) == 0) {
        handle_test_sumjasminfast(cmd + 21);
    } else if (strncmp(cmd, "BENCHMARK_SUM_C ", 16) == 0) {
        handle_benchmark_sumc(cmd + 16);
    } else if (strncmp(cmd, "BENCHMARK_SUM_JASMIN ", 21) == 0) {
        handle_benchmark_sumjasmin(cmd + 21);
    } else if (strncmp(cmd, "BENCHMARK_SUM_JASMIN_FAST ", 26) == 0) {
        handle_benchmark_sumjasminfast(cmd + 26);
    } else if (strcmp(cmd, "RESET") == 0) {
        handle_reset();
    } else {
        hal_send_str("ERR Unknown command\n");
    }
}

int main(void) {
    /* Initialize platform */
    hal_setup(CLOCK_BENCHMARK);

    /* Welcome message */
    hal_send_str("\n");
    hal_send_str("====================================\n");
    hal_send_str("Sum Assignment - Nucleo-L4R5ZI\n");
    hal_send_str("====================================\n");
    hal_send_str("Ready for commands.\n\n");

    /* Main command loop */
    while (1) {
        /* Read command */
        size_t len = hal_recv_str(cmd_buffer, CMD_BUFFER_SIZE);
        if (len > 0) {
            /* Process command */
            process_command(cmd_buffer);
        }
    }

    return 0;
}
