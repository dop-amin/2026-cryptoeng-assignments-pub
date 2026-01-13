#include <stdio.h>
#include <string.h>

#include "chacha20_wrapper.h"
#include "hal.h"

/* Platform-specific includes */
#ifndef QEMU_PLATFORM
#include <libopencm3/cm3/nvic.h>
#include <libopencm3/cm3/systick.h>
#endif

/* Command buffer */
#define CMD_BUFFER_SIZE 512
static char cmd_buffer[CMD_BUFFER_SIZE];

/* Test data buffers */
static uint32_t test_input[16] __attribute__((aligned(4)));
static uint32_t test_output[16] __attribute__((aligned(4)));

/* Byte swap for endianness conversion */
static inline uint32_t bswap32(uint32_t x) {
    return ((x & 0xFF000000) >> 24) | ((x & 0x00FF0000) >> 8) | ((x & 0x0000FF00) << 8) |
           ((x & 0x000000FF) << 24);
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
 * Handle TEST_KEYSTREAM command
 * Format: TEST_KEYSTREAM <key_hex> <nonce_hex> <length>
 */
static void handle_test_keystream(const char *args) {
    uint8_t key[32];
    uint8_t nonce[12];
    uint32_t length;
    static uint8_t keystream[256] __attribute__((aligned(4)));

    /* Find first space (after key) */
    const char *nonce_start = strchr(args, ' ');
    if (!nonce_start) {
        hal_send_str("ERR Missing nonce\n");
        return;
    }
    nonce_start++; /* Skip space */

    /* Find second space (after nonce) */
    const char *length_start = strchr(nonce_start, ' ');
    if (!length_start) {
        hal_send_str("ERR Missing length\n");
        return;
    }
    length_start++; /* Skip space */

    /* Parse length */
    if (sscanf(length_start, "%lu", &length) != 1 || length == 0 || length > 256) {
        hal_send_str("ERR Invalid length (max 256)\n");
        return;
    }

    /* Parse key (32 bytes = 64 hex chars) */
    size_t key_len = parse_hex_to_bytes(args, key, 32);
    if (key_len != 32) {
        hal_send_str("ERR Invalid key length (need 32 bytes)\n");
        return;
    }

    /* Parse nonce (12 bytes = 24 hex chars) */
    size_t nonce_len = parse_hex_to_bytes(nonce_start, nonce, 12);
    if (nonce_len != 12) {
        hal_send_str("ERR Invalid nonce length (need 12 bytes)\n");
        return;
    }

    /* Generate keystream */
    memset(keystream, 0, sizeof(keystream));
    crypto_stream_chacha20_ietf(keystream, nonce, key, length);

    /* Send result - all hex on one line */
    static char result[600]; /* "OK " + 256*2 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < length; i++) {
        pos += sprintf(result + pos, "%02x", keystream[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/**
 * Handle TEST_KEYSETUP command
 * Format: TEST_KEYSETUP <32-byte-key-hex>
 * Returns: state[0..15] in hex (64 bytes = 128 hex chars)
 */
static void handle_test_keysetup(const char *args) {
    uint8_t key[32];
    static uint32_t state[16] __attribute__((aligned(4)));

    /* Parse key (32 bytes = 64 hex chars) */
    size_t key_len = parse_hex_to_bytes(args, key, 32);
    if (key_len != 32) {
        hal_send_str("ERR Invalid key length (need 32 bytes)\n");
        return;
    }

    /* Initialize state to zero */
    memset(state, 0, sizeof(state));

    /* Call keysetup */
    test_chacha20_keysetup(state, key);

    /* Send result - state as 16 words in little-endian byte order */
    static char result[300]; /* "OK " + 64*2 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (int i = 0; i < 16; i++) {
        /* Output each word as 4 bytes in little-endian order */
        pos += sprintf(result + pos, "%02x%02x%02x%02x", (unsigned)(state[i] & 0xFF),
                       (unsigned)((state[i] >> 8) & 0xFF), (unsigned)((state[i] >> 16) & 0xFF),
                       (unsigned)((state[i] >> 24) & 0xFF));
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/**
 * Handle TEST_IVSETUP command
 * Format: TEST_IVSETUP <16-word-state-hex> <12-byte-nonce-hex>
 * Returns: state[0..15] in hex (64 bytes = 128 hex chars)
 */
static void handle_test_ivsetup(const char *args) {
    static uint32_t state[16] __attribute__((aligned(4)));
    uint8_t nonce[12];

    /* Find space between state and nonce */
    const char *nonce_start = strchr(args, ' ');
    if (!nonce_start) {
        hal_send_str("ERR Missing nonce\n");
        return;
    }
    nonce_start++; /* Skip space */

    /* Parse state (16 words = 64 bytes = 128 hex chars) */
    size_t state_len = parse_hex_to_bytes(args, (uint8_t *)state, 64);
    if (state_len != 64) {
        hal_send_str("ERR Invalid state length (need 64 bytes)\n");
        return;
    }

    /* Parse nonce (12 bytes = 24 hex chars) */
    size_t nonce_len = parse_hex_to_bytes(nonce_start, nonce, 12);
    if (nonce_len != 12) {
        hal_send_str("ERR Invalid nonce length (need 12 bytes)\n");
        return;
    }

    /* Call ivsetup */
    test_chacha20_ietf_ivsetup(state, nonce);

    /* Send result - state as 16 words in little-endian byte order */
    static char result[300]; /* "OK " + 64*2 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (int i = 0; i < 16; i++) {
        /* Output each word as 4 bytes in little-endian order */
        pos += sprintf(result + pos, "%02x%02x%02x%02x", (unsigned)(state[i] & 0xFF),
                       (unsigned)((state[i] >> 8) & 0xFF), (unsigned)((state[i] >> 16) & 0xFF),
                       (unsigned)((state[i] >> 24) & 0xFF));
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/**
 * Handle TEST_ENCRYPT command
 * Format: TEST_ENCRYPT <16-word-state-hex> <length>
 * Returns: keystream output in hex (up to 256 bytes)
 */
static void handle_test_encrypt(const char *args) {
    static uint32_t state[16] __attribute__((aligned(4)));
    uint32_t length;
    static uint8_t keystream[256] __attribute__((aligned(4)));

    /* Find space between state and length */
    const char *length_start = strchr(args, ' ');
    if (!length_start) {
        hal_send_str("ERR Missing length\n");
        return;
    }
    length_start++; /* Skip space */

    /* Parse length */
    if (sscanf(length_start, "%lu", &length) != 1 || length == 0 || length > 256) {
        hal_send_str("ERR Invalid length (max 256)\n");
        return;
    }

    /* Parse state (16 words = 64 bytes = 128 hex chars) */
    size_t state_len = parse_hex_to_bytes(args, (uint8_t *)state, 64);
    if (state_len != 64) {
        hal_send_str("ERR Invalid state length (need 64 bytes)\n");
        return;
    }

    /* Clear keystream buffer */
    memset(keystream, 0, sizeof(keystream));

    /* Call encrypt_bytes (generates keystream) */
    test_chacha20_encrypt_bytes(state, NULL, keystream, length);

    /* Send result - keystream in hex */
    static char result[600]; /* "OK " + 256*2 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < length; i++) {
        pos += sprintf(result + pos, "%02x", keystream[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/**
 * Handle TEST_PRIMITIVE command
 */
static void handle_test_primitive(const char *args) {
    int op_id;

    /* Parse operation ID */
    if (sscanf(args, "%d", &op_id) != 1) {
        hal_send_str("ERR Invalid operation ID\n");
        return;
    }

    /* Skip to hex data */
    const char *hex_data = strchr(args, ' ');
    if (!hex_data) {
        hal_send_str("ERR Missing data\n");
        return;
    }
    hex_data++; /* Skip space */

    /* Parse input data as little-endian bytes */
    static uint32_t inputs[4] __attribute__((aligned(4)));
    size_t byte_count = parse_hex_to_bytes(hex_data, (uint8_t *)inputs, 16);

    if (byte_count < 8) {
        hal_send_str("ERR Insufficient data\n");
        return;
    }

    /* Execute operation */
    switch (op_id) {
    case 1: /* add32 */
        break;

    case 2: /* rotl32 */
        break;

    case 3: /* quarterround */
        if (byte_count < 16) {
            hal_send_str("ERR Quarterround needs 16 bytes\n");
            return;
        }

        test_quarterround(inputs);

        /* Send result as little-endian hex bytes (direct memory dump) */
        static char result[40];
        int pos = sprintf(result, "OK ");
        for (int i = 0; i < 16; i++) {
            pos += sprintf(result + pos, "%02x", ((uint8_t *)inputs)[i]);
        }
        sprintf(result + pos, "\n");
        hal_send_str(result);
        return;

    default:
        hal_send_str("ERR Unknown operation\n");
        return;
    }
}

/**
 * Handle TEST_FULL command
 */
static void handle_test_full(const char *args) {
    /* Parse input state (16 words = 64 bytes) as little-endian */
    size_t byte_count = parse_hex_to_bytes(args, (uint8_t *)test_input, 64);

    if (byte_count != 64) {
        hal_send_str("ERR Need 64 bytes for full block\n");
        return;
    }

    /* Output buffer as bytes */
    static uint8_t output_bytes[64] __attribute__((aligned(4)));

    /* Run ChaCha20 block */
    uint64_t start_cycles = hal_get_time();
    test_chacha20_block(output_bytes, test_input);
    uint64_t end_cycles = hal_get_time();
    uint64_t cycles = end_cycles - start_cycles;

    /* Send result - all hex on one line (already in little-endian bytes) */
    char result[256];
    int pos = sprintf(result, "OK ");
    for (int i = 0; i < 64; i++) {
        pos += sprintf(result + pos, "%02x", output_bytes[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);

    /* Optionally print cycle count for benchmarking */
    (void)cycles; /* Suppress unused warning */
}

/**
 * Handle TEST_COLUMN_ROUND command
 * Format: TEST_COLUMN_ROUND <16-word-state-hex>
 * Returns: state[0..15] after column round in hex (64 bytes = 128 hex chars)
 */
static void handle_test_column_round(const char *args) {
    static uint32_t state[16] __attribute__((aligned(4)));

    /* Parse state (16 words = 64 bytes = 128 hex chars) */
    size_t state_len = parse_hex_to_bytes(args, (uint8_t *)state, 64);
    if (state_len != 64) {
        hal_send_str("ERR Invalid state length (need 64 bytes)\n");
        return;
    }

    /* Call column_round */
    test_column_round(state);

    /* Send result - state as 16 words in little-endian byte order */
    static char result[300]; /* "OK " + 64*2 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (int i = 0; i < 16; i++) {
        /* Output each word as 4 bytes in little-endian order */
        pos += sprintf(result + pos, "%02x%02x%02x%02x", (unsigned)(state[i] & 0xFF),
                       (unsigned)((state[i] >> 8) & 0xFF), (unsigned)((state[i] >> 16) & 0xFF),
                       (unsigned)((state[i] >> 24) & 0xFF));
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/**
 * Handle TEST_DIAGONAL_ROUND command
 * Format: TEST_DIAGONAL_ROUND <16-word-state-hex>
 * Returns: state[0..15] after diagonal round in hex (64 bytes = 128 hex chars)
 */
static void handle_test_diagonal_round(const char *args) {
    static uint32_t state[16] __attribute__((aligned(4)));

    /* Parse state (16 words = 64 bytes = 128 hex chars) */
    size_t state_len = parse_hex_to_bytes(args, (uint8_t *)state, 64);
    if (state_len != 64) {
        hal_send_str("ERR Invalid state length (need 64 bytes)\n");
        return;
    }

    /* Call diagonal_round */
    test_diagonal_round(state);

    /* Send result - state as 16 words in little-endian byte order */
    static char result[300]; /* "OK " + 64*2 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (int i = 0; i < 16; i++) {
        /* Output each word as 4 bytes in little-endian order */
        pos += sprintf(result + pos, "%02x%02x%02x%02x", (unsigned)(state[i] & 0xFF),
                       (unsigned)((state[i] >> 8) & 0xFF), (unsigned)((state[i] >> 16) & 0xFF),
                       (unsigned)((state[i] >> 24) & 0xFF));
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/**
 * Handle BENCHMARK command
 * Format: BENCHMARK <iterations>
 */
static void handle_benchmark(const char *args) {
    int iterations;

    if (sscanf(args, "%d", &iterations) != 1 || iterations <= 0) {
        hal_send_str("ERR Invalid iteration count\n");
        return;
    }

    /* Initialize test data */
    for (int i = 0; i < 16; i++) {
        test_input[i] = i;
    }

    static uint8_t output_bytes[64] __attribute__((aligned(4)));

    /* Run benchmark */
    uint64_t start_cycles = hal_get_time();

    for (int i = 0; i < iterations; i++) {
        test_chacha20_block(output_bytes, test_input);
    }

    uint64_t end_cycles = hal_get_time();
    uint32_t total_cycles = (uint32_t)(end_cycles - start_cycles);

    /* Send result */
    char result[64];
    snprintf(result, sizeof(result), "OK cycles=%lu\n", (unsigned long)total_cycles);
    hal_send_str(result);
}

/**
 * Handle BENCHMARK_KEYSTREAM command
 * Format: BENCHMARK_KEYSTREAM <iterations> <length>
 */
static void handle_benchmark_keystream(const char *args) {
    int iterations;
    uint32_t length;

    if (sscanf(args, "%d %lu", &iterations, &length) != 2) {
        hal_send_str("ERR Invalid arguments\n");
        return;
    }

    if (iterations <= 0) {
        hal_send_str("ERR Invalid iteration count\n");
        return;
    }

    if (length == 0 || length > 256) {
        hal_send_str("ERR Invalid length (max 256)\n");
        return;
    }

    /* Fixed test key and nonce */
    static uint8_t key[32] = {0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a,
                              0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15,
                              0x16, 0x17, 0x18, 0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f};
    static uint8_t nonce[12] = {0x00, 0x00, 0x00, 0x09, 0x00, 0x00,
                                0x00, 0x4a, 0x00, 0x00, 0x00, 0x00};
    static uint8_t keystream[256] __attribute__((aligned(4)));

    /* Run benchmark */
    uint64_t start_cycles = hal_get_time();

    for (int i = 0; i < iterations; i++) {
        crypto_stream_chacha20_ietf(keystream, nonce, key, length);
    }

    uint64_t end_cycles = hal_get_time();
    uint32_t total_cycles = (uint32_t)(end_cycles - start_cycles);

    /* Send result */
    char result[64];
    snprintf(result, sizeof(result), "OK cycles=%lu\n", (unsigned long)total_cycles);
    hal_send_str(result);
}

/**
 * Handle RESET command
 */
static void handle_reset(void) {
    memset(test_input, 0, sizeof(test_input));
    memset(test_output, 0, sizeof(test_output));
    hal_send_str("OK\n");
}

/**
 * Process a command
 */
static void process_command(const char *cmd) {
    if (strncmp(cmd, "TEST_PRIMITIVE ", 15) == 0) {
        handle_test_primitive(cmd + 15);
    } else if (strncmp(cmd, "TEST_FULL ", 10) == 0) {
        handle_test_full(cmd + 10);
    } else if (strncmp(cmd, "TEST_KEYSTREAM ", 15) == 0) {
        handle_test_keystream(cmd + 15);
    } else if (strncmp(cmd, "TEST_KEYSETUP ", 14) == 0) {
        handle_test_keysetup(cmd + 14);
    } else if (strncmp(cmd, "TEST_IVSETUP ", 13) == 0) {
        handle_test_ivsetup(cmd + 13);
    } else if (strncmp(cmd, "TEST_ENCRYPT ", 13) == 0) {
        handle_test_encrypt(cmd + 13);
    } else if (strncmp(cmd, "TEST_COLUMN_ROUND ", 18) == 0) {
        handle_test_column_round(cmd + 18);
    } else if (strncmp(cmd, "TEST_DIAGONAL_ROUND ", 20) == 0) {
        handle_test_diagonal_round(cmd + 20);
    } else if (strncmp(cmd, "BENCHMARK_KEYSTREAM ", 20) == 0) {
        handle_benchmark_keystream(cmd + 20);
    } else if (strncmp(cmd, "BENCHMARK ", 10) == 0) {
        handle_benchmark(cmd + 10);
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
    hal_send_str("ChaCha20 Assignment - Nucleo-L4R5ZI\n");
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
