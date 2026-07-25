import csv

# Load the operation code table (OPTAB) from OPCode.csv
def load_optab(csv_file):
    optab = {}
    with open(csv_file, 'r', encoding='utf-8-sig') as file:  # Handle BOM
        reader = csv.reader(file)
        for row in reader:
            opcode, format_type = row[0].strip(), row[1].strip()  # Remove extra spaces
            optab[opcode] = format_type  # Store opcodes as uppercase for consistency
    return optab

# Determine the instruction length based on OPTAB and format
def get_instruction_length(opcode, optab):
    opcode = opcode.upper()  # Ensure consistent case for lookup
    if opcode.startswith('+'):
        base_opcode = opcode[1:].upper()
        if base_opcode in optab and (optab[base_opcode] == '3/4'):
            return 4
    elif opcode in optab and optab[opcode] == '4F':  # Handle Format 4F-specific opcodes
        return 4
    elif opcode in optab:
        format_type = optab[opcode]
        if format_type == '3/4':
            return 3
        elif format_type.isdigit():
            return int(format_type)
    return None

# Perform the first pass of assembly
def assemble_pass1(input_file, optab, out_file, symtab_file, block_table_file):
    LOCCTR = 0  # Location counter
    labels = {}  # Store labels with their relative addresses and blocks
    literals = {}
    symtab = {}  # Symbol table for resolved addresses
    littab = {}  # Literal table
    intermediate_lines = []  # Lines for the intermediate file
    first_instruction = True  # Track the first instruction after START
    current_block = "DEFAULT"  # Current memory block
    blocks = {"DEFAULT": 0, "DEFAULTB": 0, "CDATA": 0, "CBLKS": 0}  # End LOCCTR for each block
    block_start = {"DEFAULT": 0, "DEFAULTB": 0, "CDATA": 0, "CBLKS": 0}  # Start addresses for each block
    block_lengths = {}  # Lengths of each block

    assembler_directives = {"START", "END", "BYTE", "WORD", "RESB", "RESW", "USE", "BASE", "NOBASE", "LTORG"}

    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()
        line = line.replace('’', "'")  # Normalize curly apostrophes
        if not line or line.startswith('.'):  # Skip empty lines or comments
            continue

        parts = line.split()
        label, opcode, operand = None, None, None

        if len(parts) == 3:
            label, opcode, operand = parts
        elif len(parts) == 2:
            opcode, operand = parts
        elif len(parts) == 1:
            opcode = parts[0]

        if first_instruction and opcode == "START":
            LOCCTR = int(operand, 16)  # Initialize location counter
            blocks[current_block] = LOCCTR  # Initialize block LOCCTR
            block_start[current_block] = LOCCTR  # Save block's starting address
            intermediate_lines.append(f"{LOCCTR:04X}\t{label}\t{opcode}\t{operand}")
            first_instruction = False
            continue

        if opcode == "USE":
            blocks[current_block] = LOCCTR
            if current_block in block_start:
                block_lengths[current_block] = LOCCTR - block_start[current_block]

            if operand:  # Switch to the specified block
                if operand not in blocks:  # Initialize a new block
                    blocks[operand] = LOCCTR
                    block_start[operand] = LOCCTR
                current_block = operand
            else:  # Switch back to the DEFAULT block
                current_block = "DEFAULT"

            LOCCTR = blocks[current_block]
            intermediate_lines.append(f"{LOCCTR:04X}\t\t{opcode}\t{operand if operand else ''}")
            continue

        if opcode == "*":
            literal = operand
            if literal not in littab:
                littab[literal] = None  # Unassigned literal
            continue

        if opcode in {"LTORG", "END"}:
            if opcode == "LTORG":
                intermediate_lines.append(f"{LOCCTR:04X}\t\t{opcode}\t")
            elif opcode == "END":
                intermediate_lines.append(f"{LOCCTR:04X}\t\t{opcode}\t")

            for literal, info in littab.items():
                if info is None:
                    littab[literal] = LOCCTR
                    literal_length = get_literal_length(literal)
                    intermediate_lines.append(f"{LOCCTR:04X}\t*\t{literal}\t")
                    literals[literal] = {"relative_address": LOCCTR, "block_name": current_block}
                    LOCCTR += literal_length

            blocks[current_block] = LOCCTR
            continue

        if label:
            labels[label] = {"relative_address": LOCCTR, "block_name": current_block}

        intermediate_lines.append(f"{LOCCTR:04X}\t{label if label else ''}\t{opcode}\t{operand if operand else ''}")

        if operand and operand.startswith('='):
            if operand not in littab:
                littab[operand] = None

        instr_length = get_instruction_length(opcode, optab)
        if instr_length is not None:
            LOCCTR += instr_length
        elif opcode in assembler_directives:
            if opcode == "WORD":
                LOCCTR += 3
            elif opcode == "RESW":
                LOCCTR += 3 * int(operand)
            elif opcode == "RESB":
                LOCCTR += int(operand)
            elif opcode == "BYTE":
                constant = operand[2:-1]
                LOCCTR += len(constant) if operand.startswith("C'") else len(constant) // 2

    blocks[current_block] = LOCCTR
    if "CBLKS" in blocks:
        blocks["CBLKS"] -= 2

    block_base = {}
    base_address = 0
    for block_name, start_addr in block_start.items():
        block_lengths[block_name] = blocks[block_name] - start_addr
        block_base[block_name] = base_address
        base_address += block_lengths[block_name]

    for label, info in labels.items():
        relative_address = info["relative_address"]
        block_name = info["block_name"]
        absolute_address = block_base[block_name] + relative_address
        symtab[label] = absolute_address

    for literal, info in literals.items():
        if literal not in symtab:
            relative_address = info["relative_address"]
            block_name = info["block_name"]
            absolute_address = block_base[block_name] + relative_address
            symtab[literal] = absolute_address

    with open(out_file, 'w') as out:
        out.write('\n'.join(intermediate_lines))

    with open(symtab_file, 'w') as symtab_out:
        for symbol, address in symtab.items():
            symtab_out.write(f"{symbol}\t{address:04X}\n")

    with open(block_table_file, 'w') as block_out:
        block_out.write("BLOCK\tADDRESS\tLENGTH\n")
        for block_name, start_addr in block_start.items():
            block_out.write(f"{block_name}\t{block_base[block_name]:04X}\t{block_lengths[block_name]:04X}\n")

    print("Pass 1 complete. Files generated:")
    print(f"- {out_file}")
    print(f"- {symtab_file}")
    print(f"- {block_table_file}")

# Calculate literal length
def get_literal_length(literal):
    if literal.startswith("=C'") and literal.endswith("'"):
        return len(literal[3:-1])  # Length of characters
    elif literal.startswith("=X'") and literal.endswith("'"):
        return len(literal[3:-1]) // 2  # Length in bytes
    else:
        raise ValueError(f"Invalid literal: {literal}")

# File paths
opcode_csv = 'OPCode.csv'
input_file = 'in.txt'
intermediate_file = 'out_pass1.txt'
symbol_table_file = 'symbTable.txt'
block_table_file = 'blockTable.txt'

# Load operation code table
optab = load_optab(opcode_csv)

# Perform Pass 1 assembly
assemble_pass1(input_file, optab, intermediate_file, symbol_table_file, block_table_file)
