#ifndef PROCESS_H
#define PROCESS_H

#include <cstdint>

int find_process(const char *package_name);
uintptr_t get_module_base(int pid, const char *module_name);
uintptr_t get_module_end(int pid, const char *module_name);
bool ptrace_attach(int pid);
bool ptrace_detach(int pid);
bool ptrace_write(int pid, uintptr_t address, uintptr_t value, int size);

#endif // PROCESS_H
