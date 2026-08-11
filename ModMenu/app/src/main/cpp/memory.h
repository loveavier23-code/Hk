#ifndef MEMORY_H
#define MEMORY_H

#include <cstdint>
#include <cstddef>

bool read_memory(int pid, uintptr_t address, void *buffer, size_t size);
bool write_memory(int pid, uintptr_t address, const void *buffer, size_t size);
bool make_writable(int pid, uintptr_t address, size_t size);

#endif // MEMORY_H
