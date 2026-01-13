#include "sum_c.h"

uint32_t sumc(const uint32_t *integers, const size_t len_integers) {
    uint32_t sum = 0;
    for (size_t i = 0; i < len_integers; i++) {
        sum += integers[i];
    }

    return sum;
}
