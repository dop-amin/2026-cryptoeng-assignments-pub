#ifndef CHACHA20_WRAPPER_H
#define CHACHA20_WRAPPER_H

#include <stdint.h>

/**
 * ChaCha20 Jasmin Function Wrappers
 *
 * These are the C declarations for the Jasmin-implemented functions.
 * Students must implement these in chacha20.jazz.
 */

// Quarter round test (operates on array of 4 words)
void test_quarterround(uint32_t abcd[4]);

// ChaCha20 block function (note: output comes first to match Jasmin signature)
void test_chacha20_block(uint8_t output[64], const uint32_t input[16]);

// ChaCha20 IETF keystream generation
void crypto_stream_chacha20_ietf(uint8_t *ct_ptr, const uint8_t nonce[12], const uint8_t key[32],
                                 uint32_t ct_len);

// Individual ChaCha20 component functions for testing
void test_chacha20_keysetup(uint32_t state[16], const uint8_t key[32]);
void test_chacha20_ietf_ivsetup(uint32_t state[16], const uint8_t nonce[12]);
void test_chacha20_encrypt_bytes(uint32_t state[16], const uint8_t *msg, uint8_t *ct,
                                 uint32_t msg_len);

// Round functions for testing
void test_column_round(uint32_t state[16]);
void test_diagonal_round(uint32_t state[16]);

#endif /* CHACHA20_WRAPPER_H */
