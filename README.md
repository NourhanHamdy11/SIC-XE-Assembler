# Modified SIC/XE Assembler (modi-SIC/XE)

## 📝 Description
A Two-Pass Assembler for the modified SIC/XE architecture (modi-SIC/XE). It supports the new 32-bit Format 4F instructions for conditional execution and advanced memory block management (DEFAULT, DEFAULTB, CDATA, CBLKS). The system generates complete HTME object records, symbol tables, and handles literal pooling automatically.

---

## 📖 Table of Contents
1. [Introduction](#introduction)
2. [Architectural Enhancements](#architectural-enhancements)
3. [Assembler Workflow](#assembler-workflow)
   - [Pass 1: Memory Allocation](#pass-1-memory-allocation-and-symbol-table-generation)
   - [Pass 2: Object Code Generation](#pass-2-object-code-generation-and-htme-record-formatting)
4. [File Structure (Inputs & Outputs)](#file-structure)
5. [Error Handling](#error-handling)
6. [How to Run](#how-to-run)

---

## 🚀 Introduction
This project aims to emulate a modified version of the SIC/XE machine, referred to as **modi-SIC/XE**, to support advanced features and enhanced functionality. The assembler developed in this project includes both the first and second passes of assembly and successfully generates **HTME** (Header, Text, Modification, End) records suitable for the modi-SIC/XE architecture. 

It retains the original SIC/XE instruction set and its data management techniques (BYTE, WORD, RESB, RESW) while introducing major upgrades to instruction formatting and memory block partitioning.

---

## 🧠 Architectural Enhancements

### 1. Format 4F Instruction
A completely new instruction format designed to enable **conditional execution**, effectively replacing traditional branching instructions like `JLT`. 
The Format 4F is 32 bits long and is laid out as follows:
* **Opcode (6 bits):** Standard operation codes (e.g., `ADD`, `SUB`).
* **Register (4 bits):** Target register (e.g., `A`, `X`, `T`).
* **Condition Flag (2 bits):** Determines the condition for execution:
  * `00` : Zero
  * `01` : Negative
  * `10` : Carry
  * `11` : Overflow
* **Address (20 bits):** Supports direct memory addressing without the need for immediate or indirect modes.

### 2. Advanced Memory Blocks
The assembler supports dividing the program into up to four distinct memory blocks to optimize memory allocation and execution:
* **`DEFAULT`**: Reserved for Format 1 and Format 2 instructions.
* **`DEFAULTB`**: Reserved for Format 3, Format 4, and Format 4F instructions.
* **`CDATA`**: Used for smaller-sized data allocations and initialized variables.
* **`CBLKS`**: Used for larger uninitialized memory blocks (e.g., buffers).

---

## ⚙️ Assembler Workflow

The assembler processes the input assembly code in two distinct passes to resolve forward references and generate accurate object code.

### Pass 1: Memory Allocation and Symbol Table Generation
1. **Location Counter (LC):** Computes the LC for each line of code based on the instruction format and memory block.
2. **Symbol Table:** Identifies and catalogs all labels and symbols to create a comprehensive symbol table (`symbTable.txt`).
3. **Literal Handling:** Automatically identifies literals, pools them, and allocates memory for them at the end of the pass using the `LTORG` directive.
4. **Intermediate Code:** Parses the input file to generate an intermediate file detailing each line's LC and memory allocation.

### Pass 2: Object Code Generation and HTME Record Formatting
1. **Machine Code Translation:** Translates the cleaned assembly instructions from the intermediate file into binary/hexadecimal machine code.
2. **HTME Generation:** Formats the final output for program loading and execution into four record types:
   * **Header Record (H):** Contains the program name, starting address, and total length.
   * **Text Records (T):** Contains the actual object code for executable instructions.
   * **Modification Records (M):** Details adjustments needed for relocatable code (especially for Format 4 and 4F instructions).
   * **End Record (E):** Specifies the program's execution start address.

---

## 📁 File Structure

### Inputs
* `in.txt`: The main text file containing the modi-SIC/XE assembly program, including comments and line numbers.

### Outputs
* `intermediate.txt`: The cleaned assembly program generated after preprocessing.
* `out_pass1.txt`: Detailed output of Pass 1, showing the Location Counter (LC) and memory allocation for each line.
* `symbTable.txt`: The generated Symbol Table containing all symbols and their respective memory addresses.
* `out_pass2.txt`: Detailed output of Pass 2, mapping each assembly instruction to its generated object code.
* `HTME.txt`: The final compiled object program ready for the loader/linker.

---

## 🛡️ Error Handling
The assembler is equipped with robust error detection mechanisms to ensure code integrity:
* **Block Validation:** Validates all memory block names against the predefined list (`DEFAULT`, `DEFAULTB`, `CDATA`, `CBLKS`).
* **Scope Resolution:** Detects and reports undefined symbols or symbols accessed outside their permitted scope.
* **Syntax Checking:** Generates errors for invalid block references or malformed Format 4F instructions.

---

## 💻 How to Run
1. Place your modi-SIC/XE assembly code inside the `in.txt` file.
2. Run the Pass 1 module to generate `intermediate.txt`, `out_pass1.txt`, and `symbTable.txt`.
3. Run the Pass 2 module to generate `out_pass2.txt` and the final `HTME.txt` object code file.
4. Check the generated `.txt` files for memory maps, object codes, and any potential assembly errors.
