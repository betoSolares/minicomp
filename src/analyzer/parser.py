from .grammar import Grammar
from .token import Token


class Parser:
    def __init__(self):
        self.__errors__ = []
        self.__grammar__ = Grammar()
        self.__results__ = []
        self.__position__ = 0
        self.__stack__ = ["0"]
        self.__symbols__ = []
        self.__input__ = []

    # Try analyze
    def Analyze(self, tokens):
        last = tokens[-1]
        eof = Token("$", last.line, last.start, last.finish, "EOF")
        self.__input__ = tokens + [eof]

        while True:
            state = int(self.__stack__[-1])
            current = self.__input__[self.__position__]

            # Check if the word is a terminal
            if self.__get_equivalent__(current) in self.__grammar__.table[0]:
                actions = self.__get_action__(current, state)

                # Actions
                if len(actions) == 1:
                    if actions[0][0] == "Shift":
                        self.__shift__(actions[0][1], current, state)
                    elif actions[0][0] == "Reduce":
                        self.__reduce__(actions[0][1], state)
                        self.__goto__(actions[0][1], state)
                    else:
                        print("Accept")
                        break

                # Conflicts
                elif len(actions) > 1:
                    reduce = [x for x in actions if x[0] == "Reduce"]
                    shift = [x for x in actions if x[0] == "Shift"]
                    rp = self.__grammar__.rules.get(reduce[0][1])[2]
                    terminal = self.__get_equivalent__(current)
                    tp = self.__grammar__.terminals.get(terminal)

                    # Declaring variable of type ident in func
                    if shift[0][1] == 10 and reduce[0][1] == 32 and state == 50:
                        nextone = self.__input__[self.__position__ + 1].category
                        tp = 100 if nextone == "Identifier" else tp

                    # Function declaration out of class
                    elif shift[0][1] == 19 and reduce[0][1] == 16 and state == 6:
                        nextone = self.__input__[self.__position__ + 1].word
                        rp = 100 if nextone == "(" else rp

                    if rp >= tp:
                        self.__reduce__(reduce[0][1], state)
                        self.__goto__(reduce[0][1], state)
                    else:
                        self.__shift__(shift[0][1], current, state)

                # Not an action
                else:
                    print("Error not action", self.__symbols__, current.word)
                    break

            # Error not word in terminals
            else:
                print("Error not terminal", current.word)
                break

    # Get the equivalent terminal for the category of the token
    def __get_equivalent__(self, token):
        if (
            token.category == "IntConstant_Decimal"
            or token.category == "IntConstant_Hexadecimal"
        ):
            return "intConstant"

        elif token.category == "DoubleConstant":
            return "doubleConstant"

        elif token.category == "StringConstant":
            return "stringConstant"

        elif token.category == "BooleanConstant":
            return "booleanConstant"

        elif (
            token.category == "DoubleOperator"
            or token.category == "SingleOperator"
        ):
            return token.word

        elif token.category == "Identifier":
            return "ident"

        else:
            return token.word

    # Get the action to make
    def __get_action__(self, token, state):
        terminal = self.__get_equivalent__(token)
        actions = []
        index = self.__grammar__.table[0].index(terminal)
        raw = str(self.__grammar__.table[state + 1][index]).split("/")

        for item in raw:
            if not item:
                continue
            item = item.strip()

            if item.startswith("s"):
                actions.append(("Shift", int(item[1:])))
            elif item.startswith("r"):
                actions.append(("Reduce", int(item[1:])))
            else:
                actions.append(("Accept", -1))

        return actions

    # Shift from one state to another
    def __shift__(self, new_state, current, state):
        self.__stack__.append(str(new_state))
        self.__symbols__.append(current.word)
        self.__position__ += 1
        print("Shift from", state, "to", new_state, self.__symbols__)
        self.__results__.append(("Shift", state, new_state))

    # Reduce symbols to productions
    def __reduce__(self, production, state):
        rule = self.__grammar__.rules.get(int(production))
        length = 0 if rule[1] == "''" else len(rule[1].split())
        self.__stack__ = self.__stack__[: len(self.__stack__) - length]
        self.__symbols__ = self.__symbols__[: len(self.__symbols__) - length]
        self.__symbols__.append(rule[0])
        self.__results__.append(("Reduce", state, production))
        print("Reduce from", state, "with", production, self.__symbols__)

    # Go to a different state after reduction
    def __goto__(self, production, state):
        rule = self.__grammar__.rules.get(int(production))
        state = int(self.__stack__[-1])
        index = self.__grammar__.table[0].index(rule[0])
        goto = str(self.__grammar__.table[state + 1][index])
        self.__stack__.append(str(goto))
        print("Goto from", state, "to", goto, self.__symbols__)
        self.__results__.append(("Goto", state, goto))
