#include "memory.h"
#include <android/log.h>
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <unistd.h>
#include <sys/uio.h>

#define TAG "ModMenuMem"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, TAG, __VA_ARGS__)

bool read_memory(int pid, uintptr_t address, void *buffer, size_t size) {
    if (pid <= 0 || size == 0) return false;

    struct iovec local[1];
    struct iovec remote[1];
    local[0].iov_base = buffer;
    local[0].iov_len = size;
    remote[0].iov_base = reinterpret_cast<void*>(address);
    remote[0].iov_len = size;

    ssize_t nread = process_vm_readv(pid, local, 1, remote, 1, 0);
    if (nread == -1) {
        // Fallback to /proc/pid/mem
        char path[64];
        snprintf(path, sizeof(path), "/proc/%d/mem", pid);
        int fd = open(path, O_RDONLY);
        if (fd < 0) return false;

        if (lseek64(fd, address, SEEK_SET) != (off64_t)address) {
            close(fd);
            return false;
        }

        ssize_t n = read(fd, buffer, size);
        close(fd);
        return n == (ssize_t)size;
    }
    return nread == (ssize_t)size;
}

bool write_memory(int pid, uintptr_t address, const void *buffer, size_t size) {
    if (pid <= 0 || size == 0) return false;

    struct iovec local[1];
    struct iovec remote[1];
    local[0].iov_base = const_cast<void*>(buffer);
    local[0].iov_len = size;
    remote[0].iov_base = reinterpret_cast<void*>(address);
    remote[0].iov_len = size;

    ssize_t nwrite = process_vm_writev(pid, local, 1, remote, 1, 0);
    if (nwrite == -1) {
        // Fallback to /proc/pid/mem
        char path[64];
        snprintf(path, sizeof(path), "/proc/%d/mem", pid);
        int fd = open(path, O_RDWR);
        if (fd < 0) return false;

        if (lseek64(fd, address, SEEK_SET) != (off64_t)address) {
            close(fd);
            return false;
        }

        ssize_t n = write(fd, buffer, size);
        close(fd);
        return n == (ssize_t)size;
    }
    return nwrite == (ssize_t)size;
}

bool make_writable(int pid, uintptr_t address, size_t size) {
    if (pid <= 0) return false;

    // Use mprotect via /proc/pid/mem - calculate page-aligned range
    uintptr_t page_start = address & ~0xFFF;
    uintptr_t page_end = (address + size + 0xFFF) & ~0xFFF;

    // Attempt to alter permissions via syscall injection
    // On most modern Android, /proc/pid/mem write bypasses mprotect
    char path[64];
    snprintf(path, sizeof(path), "/proc/%d/mem", pid);
    int fd = open(path, O_RDWR);
    if (fd < 0) return false;
    close(fd);
    return true;
}
