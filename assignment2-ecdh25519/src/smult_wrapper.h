#ifndef SMULT_WRAPPER_H
#define SMULT_WRAPPER_H

#include <stdint.h>

#define N 32
#define N_P3 (N * 4)
#define N_RD32 8

// Radix-2^8 representation
typedef struct {
    uint32_t v[N];
} fe25519;

typedef struct {
    fe25519 x;
    fe25519 y;
    fe25519 z;
    fe25519 t;
} ge25519;

// Radix-2^32 representation
typedef struct {
    uint32_t v[N_RD32];
} fe25519_rd32;

// Field arithemtics
void fe25519_cmov_wrapper(fe25519 *r, fe25519 *x, uint32_t cond);

void fe25519_freeze_wrapper(fe25519 *r);

int fe25519_iseq_wrapper(const fe25519 *x, const fe25519 *y);

int fe25519_isnegative_wrapper(const fe25519 *x);

void fe25519_add_wrapper(fe25519 *r, const fe25519 *x, const fe25519 *y);

void fe25519_add_xx_wrapper(fe25519 *r, const fe25519 *x);

void fe25519_add_rx_wrapper(fe25519 *r, const fe25519 *x);

void fe25519_double_wrapper(fe25519 *r, const fe25519 *x);

void fe25519_double_inplace_wrapper(fe25519 *r);

void fe25519_sub_wrapper(fe25519 *r, const fe25519 *x, const fe25519 *y);

void fe25519_sub_rx_wrapper(fe25519 *r, const fe25519 *x);

void fe25519_neg_wrapper(fe25519 *r, const fe25519 *x);

void fe25519_neg_inplace_wrapper(fe25519 *r);

void fe25519_mul_wrapper(fe25519 *r, const fe25519 *x, const fe25519 *y);

void fe25519_mul_rx_wrapper(fe25519 *r, const fe25519 *x);

void fe25519_square_wrapper(fe25519 *r, const fe25519 *x);

void fe25519_square_inplace_wrapper(fe25519 *r);

void fe25519_pow2523_wrapper(fe25519 *r, const fe25519 *x);

void fe25519_invsqrt_wrapper(fe25519 *r, const fe25519 *x);

// Group arithemtics
void ge25519_unpack_wrapper(uint32_t *r, const unsigned char *x);

void ge25519_pack_wrapper(unsigned char *r, const uint32_t *x);

void ge25519_add_wrapper(uint32_t *r, const uint32_t *p, const uint32_t *q);

void ge25519_add_rp_wrapper(uint32_t *r, const uint32_t *p);

void ge25519_double_inplace_wrapper(uint32_t *r);

// Scalar multiplication
void crypto_scalarmult_wrapper(unsigned char *ss, const unsigned char *sk, const unsigned char *pk);

void crypto_scalarmult_base(unsigned char *pk, const unsigned char *sk);

// Field arithmetic in radix-2^32
void fe25519_add_rd32_wrapper(fe25519_rd32 *r, const fe25519_rd32 *x, const fe25519_rd32 *y);
void fe25519_mul_rd32_wrapper(fe25519_rd32 *r, const fe25519_rd32 *x, const fe25519_rd32 *y);

#endif
