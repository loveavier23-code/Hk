#ifndef AOB_SCANNER_H
#define AOB_SCANNER_H

#include <cstdint>

uintptr_t aob_scan(int pid, uintptr_t start, uintptr_t end,
                   const uint8_t *pattern, const char *mask, size_t pattern_len);

#endif // AOB_SCANNER_H
