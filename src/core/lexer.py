import sys


class Lexer:
    def get_lexemes(self, lines):
        # Check if the file is empty
        if len(lines) == 0:
            print("There is nothing to do, the file is empty")
            sys.exit(1)

        # Get all the words in the file
        for line_number, text in lines.items():
            for char in text:
                print(line_number, "->", char)
