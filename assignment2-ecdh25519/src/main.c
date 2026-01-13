#include <stdio.h>
#include <string.h>

#include "hal.h"
#include "smult_wrapper.h"

/* Platform-specific includes */
#ifndef QEMU_PLATFORM
#include <libopencm3/cm3/nvic.h>
#include <libopencm3/cm3/systick.h>
#endif

/* Command buffer */
#define CMD_BUFFER_SIZE 1024
static char cmd_buffer[CMD_BUFFER_SIZE];

/* Test data buffers */
static uint32_t test_input[16] __attribute__((aligned(4)));
static uint32_t test_output[16] __attribute__((aligned(4)));

/* Parse hex string to byte array
 * Returns number of bytes parsed */
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

/* Copy uint8_t array to uint32_t array */
static void copy_u8_to_u32(uint32_t *r, const uint8_t *x, unsigned int len) {
    unsigned int i;
    for (i = 0; i < len; i++) {
        r[i] = x[i];
    }
}

/* Generate 32B random */
static void random_bytes(uint8_t *r, unsigned int len) {
    unsigned int i;
    for (i = 0; i < len; i++) {
        r[i] = rand() & 0xFF;
    }
}

/* Pack 4 uint8_t elements to one uint32_t */
static void copy_4u8_to_u32(uint32_t *r, const uint8_t *x, unsigned int len) {
    len >>= 2;
    for (uint32_t i = 0; i < len; i++) {
        r[i] = ((uint32_t)x[4 * i]) | ((uint32_t)x[4 * i + 1] << 8) |
               ((uint32_t)x[4 * i + 2] << 16) | ((uint32_t)x[4 * i + 3] << 24);
    }
}

/* Handle TEST_FE25519_CMOV command
 * Format: TEST_FE25519_CMOV <x> <y> <cond> */
static void handle_test_fe25519_cmov(const char *args) {
    uint8_t x8[N], y8[N];
    uint8_t b[4];
    fe25519 x, y;

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Check if the second argument is missing
    const char *y_start = strchr(args, ' ');
    if (!y_start) {
        hal_send_str("ERR Missing y\n");
        return;
    }
    y_start++; // Skip space

    // Check if the third argument is missing
    const char *cond_start = strchr(y_start, ' ');
    if (!cond_start) {
        hal_send_str("ERR Missing cond\n");
        return;
    }
    cond_start++; // Skip space

    // Parse inputs
    size_t x_len = parse_hex_to_bytes(x_start, x8, N);
    size_t y_len = parse_hex_to_bytes(y_start, y8, N);
    size_t cond_len = parse_hex_to_bytes(cond_start, b, 4);
    if ((x_len != N) || (y_len != N)) {
        hal_send_str("ERR Invalid field element length (need 32 bytes)\n");
        return;
    }

    copy_u8_to_u32(&x, x8, N);
    copy_u8_to_u32(&y, y8, N);
    uint32_t cond = (uint32_t)b[0];

    // Main computation
    fe25519_cmov_wrapper(&x, &y, cond);

    // Send result - all hex on one line
    static char result[3 + 2 * N + 2]; /* "OK " + 64 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", x.v[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/* Handle TEST_FE25519_FREEZE command
 * Format: TEST_FE25519_FREEZE <x> */
static void handle_test_fe25519_freeze(const char *args) {
    uint8_t r8[N];
    fe25519 r;

    // Check if the first argument is missing
    const char *r_start = args;
    if (*r_start == '\0') {
        hal_send_str("ERR Missing r\n");
        return;
    }

    // Parse inputs
    size_t r_len = parse_hex_to_bytes(r_start, r8, N);
    if (r_len != N) {
        hal_send_str("ERR Invalid field element length (need 32 bytes)\n");
        return;
    }

    copy_u8_to_u32(&r, r8, N);

    // Main computation
    fe25519_freeze_wrapper(&r);

    // Send result - all hex on one line
    static char result[3 + 2 * N + 2]; /* "OK " + 64 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", r.v[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/* Handle TEST_FE25519_ISEQ command
 * Format: TEST_FE25519_ISEQ <x> <y> */
static void handle_test_fe25519_iseq(const char *args) {
    uint8_t x8[N], y8[N];
    fe25519 x, y;
    int b;

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Check if the second argument is missing
    const char *y_start = strchr(args, ' ');
    if (!y_start) {
        hal_send_str("ERR Missing y\n");
        return;
    }
    y_start++; // Skip space

    // Parse inputs
    size_t x_len = parse_hex_to_bytes(x_start, x8, N);
    size_t y_len = parse_hex_to_bytes(y_start, y8, N);
    if ((x_len != N) || (y_len != N)) {
        hal_send_str("ERR Invalid field element length (need 32 bytes)\n");
        return;
    }

    copy_u8_to_u32(&x, x8, N);
    copy_u8_to_u32(&y, y8, N);

    // Main computation
    b = fe25519_iseq_wrapper(&x, &y);

    // Send result - all hex on one line
    static char result[3 + 2 * 4 + 2]; /* "OK " + 2*4 hex chars + "\n" + null */
    int pos = sprintf(result, "OK %08x\n", b);
    hal_send_str(result);
}

/* Handle TEST_FE25519_ISNEGATIVE command
 * Format: TEST_FE25519_ISNEGATIVE <x> */
static void handle_test_fe25519_isnegative(const char *args) {
    uint8_t x8[N];
    fe25519 x;
    int b;

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Parse x (32 bytes = 64 hex chars)
    size_t x_len = parse_hex_to_bytes(x_start, x8, N);
    if (x_len != N) {
        hal_send_str("ERR Invalid field element length (need 32 bytes)\n");
        return;
    }

    copy_u8_to_u32(&x, x8, N);

    // Main computation
    b = fe25519_isnegative_wrapper(&x);

    // Send result - all hex on one line
    static char result[3 + 2 * 4 + 2]; /* "OK " + 2*4 hex chars + "\n" + null */
    int pos = sprintf(result, "OK %08x\n", b);
    hal_send_str(result);
}

/* Handle TEST_FE25519_ADD command
 * Format: TEST_FE25519_ADD <x> <y> */
static void handle_test_fe25519_add(const char *args) {
    uint8_t x8[N], y8[N];
    fe25519 x, y;
    fe25519 r;

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Check if the second argument is missing
    const char *y_start = strchr(args, ' ');
    if (!y_start) {
        hal_send_str("ERR Missing y\n");
        return;
    }
    y_start++; // Skip space

    // Parse inputs
    size_t x_len = parse_hex_to_bytes(x_start, x8, N);
    size_t y_len = parse_hex_to_bytes(y_start, y8, N);
    if ((x_len != N) || (y_len != N)) {
        hal_send_str("ERR Invalid field element length (need 32 bytes)\n");
        return;
    }

    copy_u8_to_u32(&x, x8, N);
    copy_u8_to_u32(&y, y8, N);

    // Main computation
    fe25519_add_wrapper(&r, &x, &y);

    // Send result - all hex on one line
    static char result[3 + 2 * N + 2]; /* "OK " + 64 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", r.v[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/* Handle TEST_FE25519_ADD_RX command
 * Format: TEST_FE25519_ADD_RX <x> <y> */
static void handle_test_fe25519_add_rx(const char *args) {
    uint8_t x8[N], y8[N];
    fe25519 x, y;

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Check if the second argument is missing
    const char *y_start = strchr(args, ' ');
    if (!y_start) {
        hal_send_str("ERR Missing y\n");
        return;
    }
    y_start++; // Skip space

    // Parse inputs
    size_t x_len = parse_hex_to_bytes(x_start, x8, N);
    size_t y_len = parse_hex_to_bytes(y_start, y8, N);
    if ((x_len != N) || (y_len != N)) {
        hal_send_str("ERR Invalid field element length (need 32 bytes)\n");
        return;
    }

    copy_u8_to_u32(&x, x8, N);
    copy_u8_to_u32(&y, y8, N);

    // Main computation
    fe25519_add_rx_wrapper(&x, &y);

    // Send result - all hex on one line
    static char result[3 + 2 * N + 2]; /* "OK " + 64 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", x.v[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/* Handle TEST_FE25519_DOUBLE command
 * Format: TEST_FE25519_DOUBLE <x> */
static void handle_test_fe25519_double(const char *args) {
    uint8_t x8[N];
    fe25519 x, r;

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Parse inputs
    size_t x_len = parse_hex_to_bytes(x_start, x8, N);
    if (x_len != N) {
        hal_send_str("ERR Invalid field element length (need 32 bytes)\n");
        return;
    }

    copy_u8_to_u32(&x, x8, N);

    // Main computation
    fe25519_double_wrapper(&r, &x);

    // Send result - all hex on one line
    static char result[3 + 2 * N + 2]; /* "OK " + 64 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", r.v[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/* Handle TEST_FE25519_DOUBLE_INPLACE command
 * Format: TEST_FE25519_DOUBLE_INPLACE <x> */
static void handle_test_fe25519_double_inplace(const char *args) {
    uint8_t x8[N];
    fe25519 x;

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Parse inputs
    size_t x_len = parse_hex_to_bytes(x_start, x8, N);
    if (x_len != N) {
        hal_send_str("ERR Invalid field element length (need 32 bytes)\n");
        return;
    }

    copy_u8_to_u32(&x, x8, N);

    // Main computation
    fe25519_double_inplace_wrapper(&x);

    // Send result - all hex on one line
    static char result[3 + 2 * N + 2]; /* "OK " + 64 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", x.v[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/* Handle TEST_FE25519_SUB command
 * Format: TEST_FE25519_SUB <x> <y> */
static void handle_test_fe25519_sub(const char *args) {
    uint8_t x8[N], y8[N];
    fe25519 x, y, r;

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Check if the second argument is missing
    const char *y_start = strchr(args, ' ');
    if (!y_start) {
        hal_send_str("ERR Missing y\n");
        return;
    }
    y_start++; // Skip space

    // Parse inputs
    size_t x_len = parse_hex_to_bytes(x_start, x8, N);
    size_t y_len = parse_hex_to_bytes(y_start, y8, N);
    if ((x_len != N) || (y_len != N)) {
        hal_send_str("ERR Invalid field element length (need 32 bytes)\n");
        return;
    }

    copy_u8_to_u32(&x, x8, N);
    copy_u8_to_u32(&y, y8, N);

    // Main computation
    fe25519_sub_wrapper(&r, &x, &y);

    // Send result - all hex on one line
    static char result[3 + 2 * N + 2]; /* "OK " + 64 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", r.v[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/* Handle TEST_FE25519_SUB_RX command
 * Format: TEST_FE25519_SUB_RX <x> <y> */
static void handle_test_fe25519_sub_rx(const char *args) {
    uint8_t x8[N], y8[N];
    fe25519 x, y;

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Check if the second argument is missing
    const char *y_start = strchr(args, ' ');
    if (!y_start) {
        hal_send_str("ERR Missing y\n");
        return;
    }
    y_start++; // Skip space

    // Parse inputs
    size_t x_len = parse_hex_to_bytes(x_start, x8, N);
    size_t y_len = parse_hex_to_bytes(y_start, y8, N);
    if ((x_len != N) || (y_len != N)) {
        hal_send_str("ERR Invalid field element length (need 32 bytes)\n");
        return;
    }

    copy_u8_to_u32(&x, x8, N);
    copy_u8_to_u32(&y, y8, N);

    // Main computation
    fe25519_sub_rx_wrapper(&x, &y);

    // Send result - all hex on one line
    static char result[3 + 2 * N + 2]; /* "OK " + 64 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", x.v[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/* Handle TEST_FE25519_NEG command
 * Format: TEST_FE25519_NEG <x> */
static void handle_test_fe25519_neg(const char *args) {
    uint8_t x8[N];
    fe25519 x, r;

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Parse inputs
    size_t x_len = parse_hex_to_bytes(x_start, x8, N);
    if (x_len != N) {
        hal_send_str("ERR Invalid field element length (need 32 bytes)\n");
        return;
    }

    copy_u8_to_u32(&x, x8, N);

    // Main computation
    fe25519_neg_wrapper(&r, &x);

    // Send result - all hex on one line
    static char result[3 + 2 * N + 2]; /* "OK " + 64 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", r.v[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/* Handle TEST_FE25519_NEG_INPLACE command
 * Format: TEST_FE25519_NEG_INPLACE <x> */
static void handle_test_fe25519_neg_inplace(const char *args) {
    uint8_t x8[N];
    fe25519 x;

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Parse inputs
    size_t x_len = parse_hex_to_bytes(x_start, x8, N);
    if (x_len != N) {
        hal_send_str("ERR Invalid field element length (need 32 bytes)\n");
        return;
    }

    copy_u8_to_u32(&x, x8, N);

    // Main computation
    fe25519_neg_inplace_wrapper(&x);

    // Send result - all hex on one line
    static char result[3 + 2 * N + 2]; /* "OK " + 64 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", x.v[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/* Handle TEST_FE25519_MUL command
 * Format: TEST_FE25519_MUL <x> <y> */
static void handle_test_fe25519_mul(const char *args) {
    uint8_t x8[N], y8[N];
    fe25519 x, y, r;

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Check if the second argument is missing
    const char *y_start = strchr(args, ' ');
    if (!y_start) {
        hal_send_str("ERR Missing y\n");
        return;
    }
    y_start++; // Skip space

    // Parse inputs
    size_t x_len = parse_hex_to_bytes(x_start, x8, N);
    size_t y_len = parse_hex_to_bytes(y_start, y8, N);
    if ((x_len != N) || (y_len != N)) {
        hal_send_str("ERR Invalid field element length (need 32 bytes)\n");
        return;
    }

    copy_u8_to_u32(&x, x8, N);
    copy_u8_to_u32(&y, y8, N);

    // Main computation
    fe25519_mul_wrapper(&r, &x, &y);

    // Send result - all hex on one line
    static char result[3 + 2 * N + 2]; /* "OK " + 64 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", r.v[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/* Handle TEST_FE25519_MUL_RX command
 * Format: TEST_FE25519_MUL_RX <x> <y> */
static void handle_test_fe25519_mul_rx(const char *args) {
    uint8_t x8[N], y8[N];
    fe25519 x, y;

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Check if the second argument is missing
    const char *y_start = strchr(args, ' ');
    if (!y_start) {
        hal_send_str("ERR Missing y\n");
        return;
    }
    y_start++; // Skip space

    // Parse inputs
    size_t x_len = parse_hex_to_bytes(x_start, x8, N);
    size_t y_len = parse_hex_to_bytes(y_start, y8, N);
    if ((x_len != N) || (y_len != N)) {
        hal_send_str("ERR Invalid field element length (need 32 bytes)\n");
        return;
    }

    copy_u8_to_u32(&x, x8, N);
    copy_u8_to_u32(&y, y8, N);

    // Main computation
    fe25519_mul_rx_wrapper(&x, &y);

    // Send result - all hex on one line
    static char result[3 + 2 * N + 2]; /* "OK " + 64 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", x.v[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/* Handle TEST_FE25519_SQUARE command
 * Format: TEST_FE25519_SQUARE <x> */
static void handle_test_fe25519_square(const char *args) {
    uint8_t x8[N];
    fe25519 x, r;

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Parse inputs
    size_t x_len = parse_hex_to_bytes(x_start, x8, N);
    if (x_len != N) {
        hal_send_str("ERR Invalid field element length (need 32 bytes)\n");
        return;
    }

    // Convert to uin32_t array
    copy_u8_to_u32(&x, x8, N);

    // Main computation
    fe25519_square_wrapper(&r, &x);

    // Send result - all hex on one line
    static char result[3 + 2 * N + 2]; /* "OK " + 64 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", r.v[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/* Handle TEST_FE25519_SQUARE_INPLACE command
 * Format: TEST_FE25519_SQUARE_INPLACE <x> */
static void handle_test_fe25519_square_inplace(const char *args) {
    uint8_t x8[N];
    fe25519 x;

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Parse inputs
    size_t x_len = parse_hex_to_bytes(x_start, x8, N);
    if (x_len != N) {
        hal_send_str("ERR Invalid field element length (need 32 bytes)\n");
        return;
    }

    copy_u8_to_u32(&x, x8, N);

    // Main computation
    fe25519_square_inplace_wrapper(&x);

    // Send result - all hex on one line
    static char result[3 + 2 * N + 2]; /* "OK " + 64 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", x.v[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/* Handle TEST_FE25519_POW2523 command
 * Format: TEST_FE25519_POW2523 <x> */
static void handle_test_fe25519_pow2523(const char *args) {
    uint8_t x8[N];
    fe25519 x, r;

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Parse inputs
    size_t x_len = parse_hex_to_bytes(x_start, x8, N);
    if (x_len != N) {
        hal_send_str("ERR Invalid field element length (need 32 bytes)\n");
        return;
    }

    copy_u8_to_u32(&x, x8, N);

    // Main computation
    fe25519_pow2523_wrapper(&r, &x);

    // Send result - all hex on one line
    static char result[3 + 2 * N + 2]; /* "OK " + 64 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", r.v[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/* Handle TEST_FE25519_INVSQRT command
 * Format: TEST_FE25519_INVSQRT <x> */
static void handle_test_fe25519_invsqrt(const char *args) {
    uint8_t x8[N];
    fe25519 x, r;

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Parse inputs
    size_t x_len = parse_hex_to_bytes(x_start, x8, N);
    if (x_len != N) {
        hal_send_str("ERR Invalid field element length (need 32 bytes)\n");
        return;
    }

    copy_u8_to_u32(&x, x8, N);

    // Main computation
    fe25519_invsqrt_wrapper(&r, &x);

    // Send result - all hex on one line
    static char result[3 + 2 * N + 2]; /* "OK " + 64 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", r.v[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/* Handle TEST_GE25519_UNPACK command
 * Format: TEST_GE25519_UNPACK <x> */
static void handle_test_ge25519_unpack(const char *args) {
    uint8_t x[N];
    ge25519 r;

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Parse inputs
    size_t x_len = parse_hex_to_bytes(x_start, x, N);
    if (x_len != N) {
        hal_send_str("ERR Invalid encoded point length (need 32 bytes)\n");
        return;
    }

    // Main computation
    ge25519_unpack_wrapper(&r, &x);

    // Send result - all hex on one line
    static char result[3 + 4 * 2 * N + 2]; /* "OK " + 4*64 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", r.x.v[i]);
    }
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", r.y.v[i]);
    }
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", r.z.v[i]);
    }
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", r.t.v[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/* Handle TEST_GE25519_PACK command
 * Format: TEST_GE25519_PACK <x> */
static void handle_test_ge25519_pack(const char *args) {
    uint8_t x8[N_P3];
    ge25519 x;
    uint8_t r[N];

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Parse inputs
    size_t x_len = parse_hex_to_bytes(x_start, x8, N_P3);
    if (x_len != N_P3) {
        hal_send_str("ERR Invalid point length (need 128 bytes)\n");
        return;
    }

    copy_u8_to_u32(&x, x8, N_P3);

    // Main computation
    ge25519_pack_wrapper(r, &x);

    // Send result - all hex on one line
    static char result[3 + 2 * N + 2]; /* "OK " + 64 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", r[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/* Handle TEST_GE25519_ADD command
 * Format: TEST_GE25519_ADD <x> <y> */
static void handle_test_ge25519_add(const char *args) {
    uint8_t x8[N_P3], y8[N_P3];
    ge25519 x, y, r;

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Check if the second argument is missing
    const char *y_start = strchr(args, ' ');
    if (!y_start) {
        hal_send_str("ERR Missing y\n");
        return;
    }
    y_start++; // Skip space

    // Parse inputs
    size_t x_len = parse_hex_to_bytes(x_start, x8, N_P3);
    size_t y_len = parse_hex_to_bytes(y_start, y8, N_P3);
    if ((x_len != N_P3) || (y_len != N_P3)) {
        hal_send_str("ERR Invalid point length (need 128 bytes)\n");
        return;
    }

    copy_u8_to_u32(&x, x8, N_P3);
    copy_u8_to_u32(&y, y8, N_P3);

    // Main computation
    ge25519_add_wrapper(&r, &x, &y);

    // Send result - all hex on one line
    static char result[3 + 4 * 2 * N + 2]; /* "OK " + 4*64 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", r.x.v[i]);
    }
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", r.y.v[i]);
    }
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", r.z.v[i]);
    }
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", r.t.v[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/* Handle TEST_GE25519_ADD_RP command
 * Format: TEST_GE25519_ADD_RP <x> <y> */
static void handle_test_ge25519_add_rp(const char *args) {
    uint8_t x8[N_P3], y8[N_P3];
    ge25519 x, y;

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Check if the second argument is missing
    const char *y_start = strchr(args, ' ');
    if (!y_start) {
        hal_send_str("ERR Missing y\n");
        return;
    }
    y_start++; // Skip space

    // Parse inputs
    size_t x_len = parse_hex_to_bytes(x_start, x8, N_P3);
    size_t y_len = parse_hex_to_bytes(y_start, y8, N_P3);
    if ((x_len != N_P3) || (y_len != N_P3)) {
        hal_send_str("ERR Invalid point length (need 128 bytes)\n");
        return;
    }

    copy_u8_to_u32(&x, x8, N_P3);
    copy_u8_to_u32(&y, y8, N_P3);

    // Main computation
    ge25519_add_rp_wrapper(&x, &y);

    // Send result - all hex on one line
    static char result[3 + 4 * 2 * N + 2]; /* "OK " + 4*64 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", x.x.v[i]);
    }
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", x.y.v[i]);
    }
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", x.z.v[i]);
    }
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", x.t.v[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/* Handle TEST_GE25519_DOUBLE_INPLACE command
 * Format: TEST_GE25519_DOUBLE_INPLACE <x> */
static void handle_test_ge25519_double_inplace(const char *args) {
    uint8_t x8[N_P3];
    ge25519 x;

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Parse inputs
    size_t x_len = parse_hex_to_bytes(x_start, x8, N_P3);
    if (x_len != N_P3) {
        hal_send_str("ERR Invalid point length (need 128 bytes)\n");
        return;
    }

    copy_u8_to_u32(&x, x8, N_P3);

    // Main computation
    ge25519_double_inplace_wrapper(&x);

    // Send result - all hex on one line
    static char result[3 + 4 * 2 * N + 2]; /* "OK " + 4*64 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", x.x.v[i]);
    }
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", x.y.v[i]);
    }
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", x.z.v[i]);
    }
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", x.t.v[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/* Handle TEST_CRYPTO_SCALARMULT_BASE command
 * Format: TEST_CRYPTO_SCALARMULT_BASE <x> */
static void handle_test_crypto_scalarmult_base(const char *args) {
    uint8_t x[N], r[N];

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Parse inputs
    size_t x_len = parse_hex_to_bytes(x_start, x, N);
    if (x_len != N) {
        hal_send_str("ERR Invalid encoded point length (need 32 bytes)\n");
        return;
    }

    // Main computation
    crypto_scalarmult_base(&r, &x);

    // Send result - all hex on one line
    static char result[3 + 2 * N + 2]; /* "OK " + 64 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", r[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/* Handle TEST_CRYPTO_SCALARMULT command
 * Format: TEST_CRYPTO_SCALARMULT <x> <y> */
static void handle_test_crypto_scalarmult(const char *args) {
    uint8_t x[N], y[N], r[N];

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Check if the second argument is missing
    const char *y_start = strchr(args, ' ');
    if (!y_start) {
        hal_send_str("ERR Missing y\n");
        return;
    }
    y_start++; // Skip space

    // Parse inputs
    size_t x_len = parse_hex_to_bytes(x_start, x, N);
    size_t y_len = parse_hex_to_bytes(y_start, y, N);
    if ((x_len != N) || (y_len != N)) {
        hal_send_str("ERR Invalid encoded point length (need 32 bytes)\n");
        return;
    }

    // Main computation
    crypto_scalarmult_wrapper(&r, &x, &y);

    // Send result - all hex on one line
    static char result[3 + 2 * N + 2]; /* "OK " + 64 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < N; i++) {
        pos += sprintf(result + pos, "%02x", r[i]);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/* Handle BENCHMARK_CRYPTO_SCALARMULT_BASE command
 * Format: BENCHMARK_CRYPTO_SCALARMULT_BASE <iterations> */
static void handle_benchmark_crypto_scalarmult_base(const char *args) {
    int iterations;

    if (sscanf(args, "%d", &iterations) != 1 || iterations <= 0) {
        hal_send_str("ERR Invalid iteration count\n");
        return;
    }

    /* Initialize test data */
    uint8_t r[N];
    uint8_t scalar[N];

    /* Run benchmark */
    uint64_t total_cycles = 0;
    for (int i = 0; i < iterations; i++) {
        random_bytes(scalar, N);
        uint64_t start_cycles = hal_get_time();
        crypto_scalarmult_base(r, scalar);
        uint64_t end_cycles = hal_get_time();
        total_cycles += (end_cycles - start_cycles);
    }

    /* Send result */
    char result[64];
    snprintf(result, sizeof(result), "OK cycles=0x%08x%08x\n", (unsigned long)(total_cycles >> 32),
             (unsigned long)(total_cycles));
    hal_send_str(result);
}

/* Handle TEST_FE25519_ADD_RD32 command
 * Format: TEST_FE25519_ADD_RD32 <x> <y> */
static void handle_test_fe25519_add_rd32(const char *args) {
    uint8_t x8[N], y8[N];
    fe25519_rd32 x, y, r;

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Check if the second argument is missing
    const char *y_start = strchr(args, ' ');
    if (!y_start) {
        hal_send_str("ERR Missing y\n");
        return;
    }
    y_start++; // Skip space

    // Parse inputs
    size_t x_len = parse_hex_to_bytes(x_start, x8, N);
    size_t y_len = parse_hex_to_bytes(y_start, y8, N);
    if ((x_len != N) || (y_len != N)) {
        hal_send_str("ERR Invalid field element length (need 32 bytes)\n");
        return;
    }

    copy_4u8_to_u32(&x, x8, N);
    copy_4u8_to_u32(&y, y8, N);

    // Main computation
    fe25519_add_rd32_wrapper(&r, &x, &y);

    // Send result - all hex on one line
    static char result[3 + 2 * N + 2]; /* "OK " + 64 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < 8; i++) {
        pos += sprintf(result + pos, "%02x", r.v[i] & 0xFF);
        pos += sprintf(result + pos, "%02x", (r.v[i] >> 8) & 0xFF);
        pos += sprintf(result + pos, "%02x", (r.v[i] >> 16) & 0xFF);
        pos += sprintf(result + pos, "%02x", (r.v[i] >> 24) & 0xFF);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/* Handle TEST_FE25519_MUL_RD32 command
 * Format: TEST_FE25519_MUL_RD32 <x> <y> */
static void handle_test_fe25519_mul_rd32(const char *args) {
    uint8_t x8[N], y8[N];
    fe25519_rd32 x, y, r;

    // Check if the first argument is missing
    const char *x_start = args;
    if (*x_start == '\0') {
        hal_send_str("ERR Missing x\n");
        return;
    }

    // Check if the second argument is missing
    const char *y_start = strchr(args, ' ');
    if (!y_start) {
        hal_send_str("ERR Missing y\n");
        return;
    }
    y_start++; // Skip space

    // Parse inputs
    size_t x_len = parse_hex_to_bytes(x_start, x8, N);
    size_t y_len = parse_hex_to_bytes(y_start, y8, N);
    if ((x_len != N) || (y_len != N)) {
        hal_send_str("ERR Invalid field element length (need 32 bytes)\n");
        return;
    }

    copy_4u8_to_u32(&x, x8, N);
    copy_4u8_to_u32(&y, y8, N);

    // Main computation
    fe25519_mul_rd32_wrapper(&r, &x, &y);

    // Send result - all hex on one line
    static char result[3 + 2 * N + 2]; /* "OK " + 64 hex chars + "\n" + null */
    int pos = sprintf(result, "OK ");
    for (uint32_t i = 0; i < 8; i++) {
        pos += sprintf(result + pos, "%02x", r.v[i] & 0xFF);
        pos += sprintf(result + pos, "%02x", (r.v[i] >> 8) & 0xFF);
        pos += sprintf(result + pos, "%02x", (r.v[i] >> 16) & 0xFF);
        pos += sprintf(result + pos, "%02x", (r.v[i] >> 24) & 0xFF);
    }
    sprintf(result + pos, "\n");
    hal_send_str(result);
}

/* Handle RESET command */
static void handle_reset(void) {
    memset(test_input, 0, sizeof(test_input));
    memset(test_output, 0, sizeof(test_output));
    hal_send_str("OK\n");
}

/* Handle BENCHMARK_FE25519_ADD_RD32 command
 * Format: BENCHMARK_FE25519_ADD_RD32 <iterations> */
static void handle_benchmark_fe25519_add_rd32(const char *args) {
    int iterations;

    if (sscanf(args, "%d", &iterations) != 1 || iterations <= 0) {
        hal_send_str("ERR Invalid iteration count\n");
        return;
    }

    /* Initialize test data */
    uint32_t r[N_RD32];
    uint32_t x[N_RD32] = {3064516468, 4091053792, 1493400025, 2439143041,
                          181055578,  886030920,  3402770136, 26471200};
    uint32_t y[N_RD32] = {2616213762, 1587981061, 3199174000, 4241896399,
                          2810318829, 450362962,  1265205284, 1263945364};

    /* Run benchmark */
    uint64_t total_cycles = 0;
    for (int i = 0; i < iterations; i++) {
        uint64_t start_cycles = hal_get_time();
        fe25519_add_rd32_wrapper(r, x, y);
        uint64_t end_cycles = hal_get_time();
        total_cycles += (end_cycles - start_cycles);
    }

    /* Send result */
    char result[64];
    snprintf(result, sizeof(result), "OK cycles=0x%08x%08x\n", (unsigned long)(total_cycles >> 32),
             (unsigned long)(total_cycles));
    hal_send_str(result);
}

/* Handle BENCHMARK_FE25519_MUL_RD32 command
 * Format: BENCHMARK_FE25519_MUL_RD32 <iterations> */
static void handle_benchmark_fe25519_mul_rd32(const char *args) {
    int iterations;

    if (sscanf(args, "%d", &iterations) != 1 || iterations <= 0) {
        hal_send_str("ERR Invalid iteration count\n");
        return;
    }

    /* Initialize test data */
    uint32_t r[N_RD32];
    uint32_t x[N_RD32] = {3064516468, 4091053792, 1493400025, 2439143041,
                          181055578,  886030920,  3402770136, 26471200};
    uint32_t y[N_RD32] = {2616213762, 1587981061, 3199174000, 4241896399,
                          2810318829, 450362962,  1265205284, 1263945364};

    /* Run benchmark */
    uint64_t total_cycles = 0;
    for (int i = 0; i < iterations; i++) {
        uint64_t start_cycles = hal_get_time();
        fe25519_mul_rd32_wrapper(r, x, y);
        uint64_t end_cycles = hal_get_time();
        total_cycles += (end_cycles - start_cycles);
    }

    /* Send result */
    char result[64];
    snprintf(result, sizeof(result), "OK cycles=0x%08x%08x\n", (unsigned long)(total_cycles >> 32),
             (unsigned long)(total_cycles));
    hal_send_str(result);
}

/* Handle BENCHMARK_FE25519_ADD_WRAPPER command
 * Format: BENCHMARK_FE25519_ADD_WRAPPER <iterations> */
static void handle_benchmark_fe25519_add_wrapper(const char *args) {
    int iterations;

    if (sscanf(args, "%d", &iterations) != 1 || iterations <= 0) {
        hal_send_str("ERR Invalid iteration count\n");
        return;
    }

    /* Initialize test data */
    uint8_t r[N];
    uint8_t x[N] = {116, 207, 168, 182, 224, 134, 216, 243, 217, 121, 3,   89,  129, 94,  98,  145,
                    90,  176, 202, 10,  72,  194, 207, 52,  216, 38,  210, 202, 32,  235, 147, 1};
    uint8_t y[N] = {2,   65, 240, 155, 5,  171, 166, 94, 112, 133, 175, 190, 207, 51, 214, 252,
                    237, 15, 130, 167, 82, 254, 215, 26, 36,  128, 105, 75,  148, 70, 86,  75};

    /* Run benchmark */
    uint64_t total_cycles = 0;
    for (int i = 0; i < iterations; i++) {
        uint64_t start_cycles = hal_get_time();
        fe25519_add_wrapper(r, x, y);
        uint64_t end_cycles = hal_get_time();
        total_cycles += (end_cycles - start_cycles);
    }

    /* Send result */
    char result[64];
    snprintf(result, sizeof(result), "OK cycles=0x%08x%08x\n", (unsigned long)(total_cycles >> 32),
             (unsigned long)(total_cycles));
    hal_send_str(result);
}

/* Handle BENCHMARK_FE25519_MUL_WRAPPER command
 * Format: BENCHMARK_FE25519_MUL_WRAPPER <iterations> */
static void handle_benchmark_fe25519_mul_wrapper(const char *args) {
    int iterations;

    if (sscanf(args, "%d", &iterations) != 1 || iterations <= 0) {
        hal_send_str("ERR Invalid iteration count\n");
        return;
    }

    /* Initialize test data */
    uint8_t r[N];
    uint8_t x[N] = {116, 207, 168, 182, 224, 134, 216, 243, 217, 121, 3,   89,  129, 94,  98,  145,
                    90,  176, 202, 10,  72,  194, 207, 52,  216, 38,  210, 202, 32,  235, 147, 1};
    uint8_t y[N] = {2,   65, 240, 155, 5,  171, 166, 94, 112, 133, 175, 190, 207, 51, 214, 252,
                    237, 15, 130, 167, 82, 254, 215, 26, 36,  128, 105, 75,  148, 70, 86,  75};

    /* Run benchmark */
    uint64_t total_cycles = 0;
    for (int i = 0; i < iterations; i++) {
        uint64_t start_cycles = hal_get_time();
        fe25519_mul_wrapper(r, x, y);
        uint64_t end_cycles = hal_get_time();
        total_cycles += (end_cycles - start_cycles);
    }

    /* Send result */
    char result[64];
    snprintf(result, sizeof(result), "OK cycles=0x%08x%08x\n", (unsigned long)(total_cycles >> 32),
             (unsigned long)(total_cycles));
    hal_send_str(result);
}

/* Process a command */
static void process_command(const char *cmd) {
    if (strncmp(cmd, "TEST_FE25519_CMOV ", 18) == 0) {
        handle_test_fe25519_cmov(cmd + 18);
    } else if (strncmp(cmd, "TEST_FE25519_FREEZE ", 20) == 0) {
        handle_test_fe25519_freeze(cmd + 20);
    } else if (strncmp(cmd, "TEST_FE25519_ISEQ ", 18) == 0) {
        handle_test_fe25519_iseq(cmd + 18);
    } else if (strncmp(cmd, "TEST_FE25519_ISNEGATIVE ", 24) == 0) {
        handle_test_fe25519_isnegative(cmd + 24);
    } else if (strncmp(cmd, "TEST_FE25519_ADD ", 17) == 0) {
        handle_test_fe25519_add(cmd + 17);
    } else if (strncmp(cmd, "TEST_FE25519_ADD_RX ", 20) == 0) {
        handle_test_fe25519_add_rx(cmd + 20);
    } else if (strncmp(cmd, "TEST_FE25519_DOUBLE ", 20) == 0) {
        handle_test_fe25519_double(cmd + 20);
    } else if (strncmp(cmd, "TEST_FE25519_DOUBLE_INPLACE ", 28) == 0) {
        handle_test_fe25519_double_inplace(cmd + 28);
    } else if (strncmp(cmd, "TEST_FE25519_SUB ", 17) == 0) {
        handle_test_fe25519_sub(cmd + 17);
    } else if (strncmp(cmd, "TEST_FE25519_SUB_RX ", 20) == 0) {
        handle_test_fe25519_sub_rx(cmd + 20);
    } else if (strncmp(cmd, "TEST_FE25519_NEG ", 17) == 0) {
        handle_test_fe25519_neg(cmd + 17);
    } else if (strncmp(cmd, "TEST_FE25519_NEG_INPLACE ", 25) == 0) {
        handle_test_fe25519_neg_inplace(cmd + 25);
    } else if (strncmp(cmd, "TEST_FE25519_MUL ", 17) == 0) {
        handle_test_fe25519_mul(cmd + 17);
    } else if (strncmp(cmd, "TEST_FE25519_MUL_RX ", 20) == 0) {
        handle_test_fe25519_mul_rx(cmd + 20);
    } else if (strncmp(cmd, "TEST_FE25519_SQUARE ", 20) == 0) {
        handle_test_fe25519_square(cmd + 20);
    } else if (strncmp(cmd, "TEST_FE25519_SQUARE_INPLACE ", 28) == 0) {
        handle_test_fe25519_square_inplace(cmd + 28);
    } else if (strncmp(cmd, "TEST_FE25519_POW2523 ", 21) == 0) {
        handle_test_fe25519_pow2523(cmd + 21);
    } else if (strncmp(cmd, "TEST_FE25519_INVSQRT ", 21) == 0) {
        handle_test_fe25519_invsqrt(cmd + 21);
    } else if (strncmp(cmd, "TEST_GE25519_UNPACK ", 20) == 0) {
        handle_test_ge25519_unpack(cmd + 20);
    } else if (strncmp(cmd, "TEST_GE25519_PACK ", 18) == 0) {
        handle_test_ge25519_pack(cmd + 18);
    } else if (strncmp(cmd, "TEST_GE25519_ADD ", 17) == 0) {
        handle_test_ge25519_add(cmd + 17);
    } else if (strncmp(cmd, "TEST_GE25519_ADD_RP ", 20) == 0) {
        handle_test_ge25519_add_rp(cmd + 20);
    } else if (strncmp(cmd, "TEST_GE25519_DOUBLE_INPLACE ", 28) == 0) {
        handle_test_ge25519_double_inplace(cmd + 28);
    } else if (strncmp(cmd, "TEST_CRYPTO_SCALARMULT_BASE ", 28) == 0) {
        handle_test_crypto_scalarmult_base(cmd + 28);
    } else if (strncmp(cmd, "TEST_CRYPTO_SCALARMULT ", 23) == 0) {
        handle_test_crypto_scalarmult(cmd + 23);
    } else if (strncmp(cmd, "BENCHMARK_CRYPTO_SCALARMULT_BASE ", 33) == 0) {
        handle_benchmark_crypto_scalarmult_base(cmd + 33);
    } else if (strncmp(cmd, "TEST_FE25519_ADD_RD32 ", 22) == 0) {
        handle_test_fe25519_add_rd32(cmd + 22);
    } else if (strncmp(cmd, "TEST_FE25519_MUL_RD32 ", 22) == 0) {
        handle_test_fe25519_mul_rd32(cmd + 22);
    } else if (strncmp(cmd, "BENCHMARK_FE25519_ADD_RD32 ", 27) == 0) {
        handle_benchmark_fe25519_add_rd32(cmd + 27);
    } else if (strncmp(cmd, "BENCHMARK_FE25519_MUL_RD32 ", 27) == 0) {
        handle_benchmark_fe25519_mul_rd32(cmd + 27);
    } else if (strncmp(cmd, "BENCHMARK_FE25519_ADD_WRAPPER ", 30) == 0) {
        handle_benchmark_fe25519_add_wrapper(cmd + 30);
    } else if (strncmp(cmd, "BENCHMARK_FE25519_MUL_WRAPPER ", 30) == 0) {
        handle_benchmark_fe25519_mul_wrapper(cmd + 30);
    } else if (strcmp(cmd, "RESET") == 0) {
        handle_reset();
    } else {
        hal_send_str("ERR Unknown command\n");
    }
}

int main(void) {
    // Initialize platform
    hal_setup(CLOCK_BENCHMARK);

    // Welcome message
    hal_send_str("\n");
    hal_send_str("========================================================\n");
    hal_send_str("Ecdh25519 Scalar Multiplication Assignment - Nucleo-L4R5ZI\n");
    hal_send_str("========================================================\n");
    hal_send_str("Ready for commands.\n\n");

    while (1) {
        // Read command
        size_t len = hal_recv_str(cmd_buffer, CMD_BUFFER_SIZE);
        if (len > 0) {
            // Process command
            process_command(cmd_buffer);
        }
    }

    return 0;
}
