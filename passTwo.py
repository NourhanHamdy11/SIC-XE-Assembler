import csv


# Load the operation code table (OPTAB) from OPCode.csv
def load_optab(csv_file):
    optab = {}
    with open(csv_file, 'r', encoding='utf-8-sig') as file:  # Handle BOM
        reader = csv.reader(file)
        for row in reader:
            opcode, format_type, code = row[0].strip(), row[1].strip(), row[2].strip()  # Remove extra spaces
            optab[opcode] = [format_type,code]  # Store opcodes as uppercase for consistency
    return optab


# Load the symbol table (SYMTAB) from symbTable.txt
def load_symtab(symtab_file):
    symtab = {}
    with open(symtab_file, 'r') as file:
        for line in file:
            parts = line.strip().split('\t')
            if len(parts) == 2:  # Ensure line is well-formed
                symbol, address = parts[0], int(parts[1], 16)
                symtab[symbol] = address
    return symtab

# Helper function to convert ASCII to hex
def ascii_to_hex(char):
    ascii_map = {}
    with open("ASCII.csv", "r") as f:
        reader = csv.reader(f)
        for row in reader:
            ascii_map[row[1]] = row[0]

    return ''.join(ascii_map.get(c, '00') for c in char)

# Register codes for format 2 instructions
REGISTER_CODES = {
    "A": 0, "X": 1, "L": 2, "B": 3, "S": 4, "T": 5, "F": 6,
    "PC": 8, "SW": 9
}

# Generate object code for an instruction
def generate_object_code(label, opcode, operand, optab, symtab, pc):
    try:
        if opcode in optab:
            hex_opcode = int(optab[opcode][1], 16)
            format_type = optab[opcode][0]

            if format_type == "1":  # Format 1
                return f"{hex_opcode:02X}"

            elif format_type == "2":  # Format 2
                if operand:
                    regs = operand.split(',')
                    reg1 = REGISTER_CODES.get(regs[0], 0)
                    reg2 = REGISTER_CODES.get(regs[1], 0) if len(regs) > 1 else 0
                    return f"{hex_opcode:02X}{reg1:01X}{reg2:01X}"
                else:
                    return f"{hex_opcode:02X}00"

            elif format_type == "3/4":  # Format 3
                flags = 0b110010  # n, i, x, b, p, e flags
                address = 0

                # Determine addressing mode
                if operand:
                    if operand.startswith('#'):  # Immediate
                        flags = 0b010000  # Set `i` flag
                        operand = operand.lstrip('#')
                        if operand in symtab:  # Symbol
                            address = symtab[operand]
                        else:  # Immediate value
                            address = int(operand)
                        disp = address
                    elif operand.startswith('@'):  # Indirect
                        flags = 0b100010  # Set `n` flag
                        operand = operand.lstrip('@')
                        address = symtab.get(operand, 0)
                        disp = address - (int(pc, 16)+3)
                    else:  # Simple
                        if ',' in operand:  # Indexed addressing
                            operand, _ = operand.split(',')
                            flags = 0b111010  # Set `x` flag
                        address = symtab.get(operand, 0)
                        disp = address - (int(pc, 16) + 3)

                hex_opcode = (hex_opcode << 4) | flags

                return f"{hex_opcode:03X}{disp:03X}"

            elif format_type == "4F":  # NEW: Format 4F
                if opcode == "CJUMP":
                    i = 1
                    j = 0
                    reg = 0
                else:
                    i = 2
                    j = 1
                    reg = REGISTER_CODES.get(operand.split(',')[0], 0)  # Extract target register
                if operand.split(',')[i] == "Z":
                    flags = 0b00
                elif operand.split(',')[i] == "N":
                    flags = 0b01
                elif operand.split(',')[i] == "C":
                    flags = 0b10
                elif operand.split(',')[i] == "V":
                    flags = 0b11
                address = symtab.get(operand.split(',')[j], 0)  # Extract memory address
                hex_opcode = (hex_opcode << 4) | reg
                hex_opcode = hex_opcode | flags
                return f"{hex_opcode:02X}{address:05X}"

        elif opcode.startswith('+'):  # Format 4 (Extended)
            base_opcode = opcode[1:]
            if base_opcode in optab:
                hex_opcode = int(optab[base_opcode][1], 16) # Hex opcode
                if operand:
                    if operand.startswith('#'):
                        hex_opcode = (hex_opcode << 4) | 0b010001
                        operand = operand.lstrip('#')
                        if operand.isdigit():
                            address = int(operand, 16)  # Immediate value
                        else:
                            address = symtab.get(operand, 0) # label
                    elif operand in symtab:
                        hex_opcode = (hex_opcode << 4) | 0b110001  # Set `e` flag (extended format)
                        address = symtab[operand]
                    return f"{hex_opcode:03X}{address:05X}"
                else:
                    return f"{hex_opcode:02X}00000"
        elif label == '*':
            operand = operand.split("'")[1]
            operand = operand if operand.isdigit() else ascii_to_hex(operand)
            return f"{operand}"
        elif opcode == "WORD" or opcode == "BYTE":
            if operand.startswith("X"):
                operand = operand[1:].split("'")[1]
            return f"{int(operand,16):06X}" if opcode == "WORD" else f"{int(operand,16):02X}"
        return None
    except Exception as e:
        print(f"Error generating object code for {opcode} {operand}: {e}")
        return None

# /////////////////////////////////////////////////////////////////


# Error handling for unidentified block names and symbols
# def validate_block(block_name):
#     if block_name not in BLOCKS:
#         raise print(f"Error: Unrecognized block name '{block_name}'.")


def validate_symbol(symbol, symtab):
    if symbol not in symtab:
        raise print(f"Error: Undefined symbol '{symbol}'.")


# Generate output with object code appended to each line
def generate_pass2_output(intermediate_file, symtab, optab, output_file):
    with open(intermediate_file, 'r') as infile, open(output_file, 'w') as outfile:
        lines = infile.readlines()

        for index, line in enumerate(lines):
            parts = line.strip().split('\t')
            if len(parts) < 2:
                outfile.write(line + '\n')
                continue

            opcode = parts[2] if parts[1] != "*" else ""
            if opcode != "END":
                label = parts[1] if parts[1] else ""
                if len(parts) > 3:
                    operand = parts[3]
                elif label == "*":
                    operand = parts[2]
                else:
                    operand = ""
            else:
                label = ""
                operand = ""

            if opcode == "START":
                outfile.write(line.strip() + '\n')
                continue

            elif opcode == "BASE":
                outfile.write(line.strip() + '\n')
                continue

            elif opcode == "END":
                outfile.write(line.strip() + '\n')
                break

            # Get the current PC value
            pc = lines[index].strip().split('\t')[0]
            use = lines[index + 1].strip().split('\t')[2]
            instruction = lines[index].strip().split('\t')[2]
            if instruction.startswith("+"):
                format = optab[instruction[1:]][0] if instruction[1:] in optab else None
            else:
                format = optab[instruction][0] if instruction in optab else None

            # Check if the next line has a USE directive
            if (use == "USE") & (format == '1'):
                # Add 3 to the current PC value and format as 4-digit hex
                pc = f"{int(pc, 16) + 1:04X}"
            elif (use == "USE") & (format == '2'):
                pc = f"{int(pc, 16) + 2:04X}"
            elif (use == "USE") & (instruction.startswith("+") or format == '4F'):
                pc = f"{int(pc, 16) + 4:04X}"
            elif (use == "USE") & (format == '3/4'):
                pc = f"{int(pc, 16) + 3:04X}"
            else:
                # Use the address from the next line
                pc = lines[index + 1].strip().split('\t')[0]  # Increment PC
            obj_code = generate_object_code(label, opcode, operand, optab, symtab, pc)

            # Write the line with object code appended
            # print(obj_code)
            outfile.write(f"{line.strip()}\t{obj_code if obj_code else ''}\n")


# ///////////////////////////////////////////////


def generate_htme_records(output_file, htme_file):
    with open(output_file, 'r') as infile, open(htme_file, 'w') as outfile:
        lines = infile.readlines()

        program_name = ""
        start_address = None
        program_length = 0
        text_records = []
        modification_records = []
        current_text_record = []
        current_start_address = None
        current_length = 0
        max_record_length = 30  # Max bytes in a T record
        literals = {}  # Map to track literal values

        for line in lines:
            parts = line.strip().split('\t')
            if len(parts) < 3:  # Ensure sufficient parts exist
                continue

            location = parts[0]
            label = parts[1]
            opcode = parts[2]
            operand = parts[3] if len(parts) > 3 else ""
            if opcode == "TIO":
                obj_code = parts[3]
            else:
                obj_code = parts[4] if len(parts) > 4 else ""

            # Process H Record (Header)
            if opcode == "START":
                program_name = label
                start_address = location
                continue

            # Handle Literals
            if opcode.startswith("="):  # Literal definition
                literals[opcode] = obj_code
                continue

            # Handle Format 1 Instructions
            if opcode in literals:  # If opcode matches literal, use its object code
                obj_code = literals[opcode]

            # Break Text Records for USE, RESW, RESB
            if opcode in ["USE", "RESW", "RESB"]:
                if current_text_record:
                    # Commit current text record
                    text_records.append(
                        f"T^{int(current_start_address, 16):06X}^{current_length:02X}^" + '^'.join(current_text_record)
                    )
                    current_text_record = []
                    current_start_address = None
                    current_length = 0
                continue

            # Process T Records (Text)
            if obj_code:
                if current_start_address is None:
                    current_start_address = location
                if current_length + len(obj_code) // 2 > max_record_length:
                    # Commit the current text record and start a new one
                    text_records.append(
                        f"T^{int(current_start_address, 16):06X}^{current_length:02X}^" + '^'.join(current_text_record)
                    )
                    current_text_record = []
                    current_start_address = location
                    current_length = 0
                current_text_record.append(obj_code)
                current_length += len(obj_code) // 2

            # Process M Records (Modification)
            if opcode.startswith('+'):  # Format 4 instruction
                mod_address = int(location, 16) + 1
                modification_records.append(f"M^{mod_address:06X}^05")

        # Add the last text record
        if current_text_record:
            text_records.append(
                f"T^{int(current_start_address, 16):06X}^{current_length:02X}^" + '^'.join(current_text_record)
            )

        # Calculate program length
        program_length = int(location, 16) - int(start_address, 16)

        # Write H Record
        outfile.write(f"H^{program_name[:6]:<6}^{int(start_address, 16):06X}^{program_length:06X}\n")

        # Write T Records
        for record in text_records:
            outfile.write(record + "\n")

        # Write M Records
        for record in modification_records:
            outfile.write(record + "\n")

        # Write E Record
        outfile.write(f"E^{int(start_address, 16):06X}\n")

    print(f"HTME records written to {htme_file}.")


# Load OPTAB, SYMTAB, and process Pass 2
opcode_csv = 'OPCode.csv'
symtab_file = 'symbTable.txt'
intermediate_file = 'out_pass1.txt'
output_file = 'out_pass2.txt'

htme_file = 'HTME.txt'  # Output for HTME records

optab = load_optab(opcode_csv)
symtab = load_symtab(symtab_file)
generate_pass2_output(intermediate_file, symtab, optab, output_file)

generate_htme_records(output_file, htme_file)

print(f"Pass 2 complete. Output written to {output_file}.")
