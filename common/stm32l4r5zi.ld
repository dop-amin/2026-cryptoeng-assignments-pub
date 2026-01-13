/*
 * STM32L4R5ZI linker script
 *
 * Memory layout:
 * - Flash: 2MB at 0x08000000
 * - RAM: 640KB at 0x20000000
 */

MEMORY
{
    rom (rx) : ORIGIN = 0x08000000, LENGTH = 2048K
    ram (rwx) : ORIGIN = 0x20000000, LENGTH = 640K
}

/* Include the common STM32 linker script */
INCLUDE cortex-m-generic.ld

/* Additional symbols required by some code */
PROVIDE(_estack = ORIGIN(ram) + LENGTH(ram));
PROVIDE(_end = end);
