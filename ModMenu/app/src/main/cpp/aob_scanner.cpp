#include "aob_scanner.h"
#include "memory.h"
#include <android/log.h>
#include <cstring>
#include <vector>

#define TAG "ModMenuAOB"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, TAG, __VA_ARGS__)

uintptr_t aob_scan(int pid, uintptr_t start, uintptr_t end,
                   const uint8_t *pattern, const char *mask, size_t pattern_len) {
    if (pid <= 0 || start >= end || pattern_len == 0) return 0;

    const size_t CHUNK_SIZE = 0x10000; // 64KB chunks
    std::vector<uint8_t> buffer(CHUNK_SIZE + pattern_len);

    for (uintptr_t addr = start; addr < end; addr += CHUNK_SIZE - pattern_len) {
        size_t to_read = CHUNK_SIZE;
        if (addr + to_read > end) {
            to_read = end - addr + pattern_len;
            if (to_read > buffer.size()) to_read = buffer.size();
        }

        if (!read_memory(pid, addr, buffer.data(), to_read)) {
            continue;
        }

        for (size_t i = 0; i <= to_read - pattern_len; i++) {
            bool match = true;
            for (size_t j = 0; j < pattern_len; j++) {
                if (mask[j] == 'x' && buffer[i + j] != pattern[j]) {
                    match = false;
                    break;
                }
            }
            if (match) {
                LOGI("AOB match at 0x%lx", addr + i);
                return addr + i;
            }
        }
    }
    return 0;
}
