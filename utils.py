from blessed import Terminal
term = Terminal()


def print_to_terminal(x, y, message, end='\n'):
    print(term.move_xy(x, y) + message, end=end)
