#include "process.h"
#include <android/log.h>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <dirent.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ptrace.h>
#include <sys/wait.h>

#define TAG "ModMenuProc"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, TAG, __VA_ARGS__)

static bool read_file(const char *path, char *buf, size_t maxlen) {
    int fd = open(path, O_RDONLY);
    if (fd < 0) return false;
    ssize_t n = read(fd, buf, maxlen - 1);
    close(fd);
    if (n > 0) {
        buf[n] = '\0';
        // Strip trailing newline
        if (n > 0 && buf[n-1] == '\n') buf[n-1] = '\0';
        return true;
    }
    return false;
}

int find_process(const char *package_name) {
    DIR *proc = opendir("/proc");
    if (!proc) return -1;

    struct dirent *entry;
    while ((entry = readdir(proc)) != nullptr) {
        if (entry->d_type != DT_DIR) continue;

        int pid = atoi(entry->d_name);
        if (pid <= 0) continue;

        char cmdline_path[64];
        snprintf(cmdline_path, sizeof(cmdline_path), "/proc/%d/cmdline", pid);

        char cmdline[256] = {0};
        if (read_file(cmdline_path, cmdline, sizeof(cmdline))) {
            if (strstr(cmdline, package_name)) {
                closedir(proc);
                return pid;
            }
        }
    }
    closedir(proc);
    return -1;
}

uintptr_t get_module_base(int pid, const char *module_name) {
    char maps_path[64];
    snprintf(maps_path, sizeof(maps_path), "/proc/%d/maps", pid);

    FILE *fp = fopen(maps_path, "r");
    if (!fp) return -1;

    char line[512];
    while (fgets(line, sizeof(line), fp)) {
        if (strstr(line, module_name)) {
            // First appearance with 'r-xp' permissions = base
            if (strstr(line, "r-xp") || strstr(line, "r--p")) {
                uintptr_t base;
                sscanf(line, "%lx", &base);
                fclose(fp);
                return base;
            }
        }
    }
    fclose(fp);

    // Fallback: find first occurrence regardless of permissions
    fp = fopen(maps_path, "r");
    if (!fp) return -1;
    while (fgets(line, sizeof(line), fp)) {
        if (strstr(line, module_name)) {
            uintptr_t base;
            sscanf(line, "%lx", &base);
            fclose(fp);
            return base;
        }
    }
    fclose(fp);
    return -1;
}

uintptr_t get_module_end(int pid, const char *module_name) {
    char maps_path[64];
    snprintf(maps_path, sizeof(maps_path), "/proc/%d/maps", pid);

    FILE *fp = fopen(maps_path, "r");
    if (!fp) return -1;

    char line[512];
    uintptr_t end = -1;
    while (fgets(line, sizeof(line), fp)) {
        if (strstr(line, module_name)) {
            uintptr_t seg_end;
            sscanf(line, "%*lx-%lx", &seg_end);
            if (seg_end > end) end = seg_end;
        }
    }
    fclose(fp);
    return end;
}

bool ptrace_attach(int pid) {
    if (ptrace(PTRACE_ATTACH, pid, 0, 0) == -1) {
        LOGE("ptrace_attach failed: %s", strerror(errno));
        return false;
    }
    waitpid(pid, nullptr, WUNTRACED);
    return true;
}

bool ptrace_detach(int pid) {
    if (ptrace(PTRACE_DETACH, pid, 0, 0) == -1) {
        LOGE("ptrace_detach failed: %s", strerror(errno));
        return false;
    }
    return true;
}

bool ptrace_write(int pid, uintptr_t address, uintptr_t value, int size) {
    if (!ptrace_attach(pid)) return false;

    // Align to word boundary
    long word_size = sizeof(long);
    uintptr_t aligned_addr = address & ~(word_size - 1);
    long offset = address - aligned_addr;

    // Read original word
    errno = 0;
    long original = ptrace(PTRACE_PEEKDATA, pid, aligned_addr, 0);
    if (errno != 0) {
        LOGE("ptrace peek failed: %s", strerror(errno));
        ptrace_detach(pid);
        return false;
    }

    // Modify bytes
    long modified = original;
    for (int i = 0; i < size && (offset + i) < word_size; i++) {
        uint8_t *byte_ptr = (uint8_t*)&value;
        uint8_t *mod_ptr = (uint8_t*)&modified;
        mod_ptr[offset + i] = byte_ptr[i];
    }

    // Write back
    if (ptrace(PTRACE_POKEDATA, pid, aligned_addr, modified) == -1) {
        LOGE("ptrace poke failed: %s", strerror(errno));
        ptrace_detach(pid);
        return false;
    }

    ptrace_detach(pid);
    return true;
}
