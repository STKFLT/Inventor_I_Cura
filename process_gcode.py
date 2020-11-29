# globals set by actors
LINE_NUM = 1
CURR_EXTRUDER = None
LAST_EXTRUDER_SWAP = 0

def split_on_line_num(line):
    if line.startswith("N"):
        line_num, line = line.split(" ", 1)
        return line_num + " ", line
    return "", line

def split_on_comments(line):
    if (comment_start := line.find(";")) != -1:
        return line[:comment_start], line[comment_start:]
    return line, ""

def split_on_comments(line):
    comment_start = line.find(";")
    if comment_start != -1:
        return line[:comment_start], line[comment_start:]
    return line, ""

def tokenize(line):
    try:
        args = line.split(" ")
        command = args[0]
        if len(args) > 1 and args[1] != "":
            params = {x[0]: x[1:] for x in args[1:]}
        else:
            params = {}
        return command, params
    except:
        print(line)



def untokenize(tokens):
    return " ".join([tokens[0]] + [x + y for x, y in tokens[1].items()])

# list of functions that take in and output lines of gcode
actors = []

def actor(func):
    actors.append(func)
    return func

@actor
def watch_for_extruder_change(tokens):
    global CURR_EXTRUDER
    global LAST_EXTRUDER_SWAP
    if tokens[0] == "M108":
        CURR_EXTRUDER = tokens[1]["T"]
        LAST_EXTRUDER_SWAP = LINE_NUM
        print(f"current extruder changed to: {CURR_EXTRUDER}")
    return tokens, []

@actor
def fixup_temp_setting(tokens):
    global CURR_EXTRUDER
    if tokens[0] == "M104" and not "T" in tokens[1]:
        if CURR_EXTRUDER is None:
            raise ValueError("G-Code tried to set active extruder temp without active extruder set")
        tokens[1]["T"] = CURR_EXTRUDER
        print("fixed up temp setting")
        print(tokens)
    return tokens, []

@actor
def wait_for_inactive_nozzle_cooling(tokens):
    if (LINE_NUM-10) <= LAST_EXTRUDER_SWAP and tokens[0] == "M104":
        # either heating up active or cooling inactive, let's check
        if tokens[1]["T"] != CURR_EXTRUDER:
            # insert wait
            return tokens, [("M6", {"T": tokens[1]["T"]})]
            print(f"inserting pause for cooling {tokens[1]}")
    return tokens, []


def process_file(input_file, output_file):
    global LINE_NUM
    for line in input_file:
        line = line[:-1]
        line, comment = split_on_comments(line)
        line_num, line = split_on_line_num(line)
        tokens = tokenize(line)
        newline_list = []
        for act in actors:
            tokens, newlines = act(tokens)
            newline_list = newline_list + newlines
        line = untokenize(tokens)
        line = line_num + line + comment
        output_file.write(line + "\n")
        LINE_NUM += 1
        for newline in newline_list:
            line = untokenize(newline)
            output_file.write(line + "\n")
            LINE_NUM += 1


if __name__ == "__main__":
    import sys
    with open(sys.argv[1], 'r') as in_file, open(sys.argv[2], 'w') as out_file:
        process_file(in_file, out_file)
    




