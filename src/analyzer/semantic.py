import re

from .symbol import Symbol
from .token import Token


class Semantic:
    def __init__(self):
        self.__errors__ = []
        self.__symbols__ = []
        self.__position__ = 0
        self.__input__ = []
        self.__scope__ = ["Global"]
        self.__loking_class__ = False
        self.__loking_func__ = False
        self.__class_open__ = False
        self.__func_open__ = False
        self.__skips__ = 0

    # Get a list with the errors
    @property
    def errors(self):
        return self.__errors__

    # Get the table symbols
    @property
    def symbols(self):
        return self.__symbols__

    # Try analyze
    def analyze(self, tokens):
        self.__input__ = tokens

        while True:
            current = self.__input__[self.__position__]
            self.__position__ += 1
            if self.__position__ >= len(self.__input__):
                break

            if current.category == "Identifier":
                lookahead = self.__input__[self.__position__]

                # If next one identifier skip, possible object
                if lookahead.category == "Identifier":
                    continue

                # Check if symbol exists
                if (
                    self.__get_symbol__(current.word, ",".join(self.__scope__))
                    is None
                ):

                    # Check for assignement
                    if lookahead.word == "=":

                        # Check if declared in any parent scope
                        decl, scp = self.__declared_before__(current.word)

                        if decl:
                            self.__update_symbol__(current, scp)
                        else:
                            reason = "Assigning to undeclared variable"
                            self.__errors__.append(
                                [current, reason, current.word]
                            )
                            while lookahead.word != ";":
                                self.__position__ += 1
                                lookahead = self.__input__[self.__position__]

                    # Possible function call or accesing object
                    elif lookahead.word == ".":

                        # Check if declared in any parent scope
                        decl, scp = self.__declared_before__(current.word)

                        if decl:
                            self.__position__ += 1
                            current = self.__input__[self.__position__]
                            self.__position__ += 1

                            if self.__special_object__(current, scp):
                                self.__add_symbol__(current)
                            else:
                                while lookahead.word != ";":
                                    self.__position__ += 1
                                    lookahead = self.__input__[self.__position__]
                        else:
                            reason = "Assigning to undeclared object"
                            self.__errors__.append(
                                [current, reason, current.word]
                            )
                            while lookahead.word != ";":
                                self.__position__ += 1
                                lookahead = self.__input__[self.__position__]

                    # Possible new declaration
                    else:
                        # Check if declared in parent scope
                        self.__add_symbol__(current)

                # Symbol exists
                else:

                    # Function invoke or accesing object
                    if lookahead.word == ".":
                        self.__position__ += 1
                        current = self.__input__[self.__position__]
                        self.__position__ += 1

                        if self.__check_property__(current):
                            self.__add_symbol__(current)
                        else:
                            while lookahead.word != ";":
                                self.__position__ += 1
                                lookahead = self.__input__[self.__position__]

                    # Update the symbol or error
                    else:
                        self.__update_symbol__(current, ",".join(self.__scope__))

            # Not an identifier
            else:

                # Check for scope starting
                if current.word == "{":
                    if self.__loking_class__:
                        self.__class_open__ = True
                        self.__loking_class__ = False
                    elif self.__loking_func__:
                        self.__func_open__ = True
                        self.__loking_func__ = False
                    else:
                        self.__skips__ += 1

                # Check for scope ending
                elif current.word == "}":
                    if self.__skips__ > 0:
                        self.__skips__ -= 1
                    elif self.__func_open__:
                        self.__func_open__ = False
                        self.__scope__.pop()
                    elif self.__class_open__:
                        self.__class_open__ = False
                        self.__scope__.pop()

                # Skip Statetements block (provitional)
                elif (
                    current.word == "if"
                    or current.word == "while"
                    or current.word == "for"
                ):
                    lookahead = current
                    while lookahead.word != ")":
                        lookahead = self.__input__[self.__position__]
                        self.__position__ += 1

                elif current.word == "return" or current.word == "System":
                    lookahead = current
                    while lookahead.word != ";":
                        lookahead = self.__input__[self.__position__]
                        self.__position__ += 1

                # Not important character
                else:
                    continue

        return True if len(self.__errors__) == 0 else False

    # Add new symbol to symbols table
    def __add_symbol__(self, token):
        before_previous = self.__input__[self.__position__ - 3]
        previous = self.__input__[self.__position__ - 2]
        next = self.__input__[self.__position__]

        type = ""
        category = ""
        value = None
        scope = ",".join(self.__scope__)
        lexeme = token.word
        extends = None
        implements = None
        params = None

        # Check if static variable
        if before_previous.word == "static":
            type = previous.word
            category = "static"

        # Check if array
        elif previous.word == "[]":
            type = "array of " + before_previous.word
            category = "variable"

        # Check if class declaration
        elif previous.word == "class":
            type = category = "class"
            self.__scope__.append(lexeme)
            self.__loking_class__ = True

            # Get extends and implements
            if next.word != "{":

                if next.word == "extends":
                    self.__position__ += 1
                    next = self.__input__[self.__position__]
                    extends = next.word
                    self.__position__ += 1
                    next = self.__input__[self.__position__]

                    if next.word == "implements":
                        implements = ""

                        while next.word != "{":
                            self.__position__ += 1
                            next = self.__input__[self.__position__]
                            implements += next.word

                        implements = implements[: len(implements) - 1]

                # Validate extends and implements
                extend_found = True
                implement_found = True

                if extends is not None:
                    extend_found = False

                    for element in self.__symbols__:
                        if (
                            element.lexeme == extends
                            and element.scope == "Global"
                            and element.type == "class"
                        ):
                            extend_found = True
                            break

                    if not extend_found:
                        reason = "Can't extend, undeclared class"
                        self.__errors__.append([token, reason, extends])

                if implements is not None:
                    for implement in implements.split(","):
                        implement_found = False

                        for element in self.__symbols__:
                            if (
                                element.lexeme == implement
                                and element.scope == "Global"
                                and element.type == "interface"
                            ):
                                implement_found = True
                                break

                        if implement_found is False:
                            reason = "Can't implement, undeclared interface"
                            self.__errors__.append([token, reason, implement])

                if extend_found is False or implement_found is False:
                    return

        # Check for interface declaration
        elif previous.word == "interface":
            type = category = "interface"

        # Check for object declaration
        elif previous.category == "Identifier":
            value_found = None
            for element in self.__symbols__:
                if (
                    element.lexeme == previous.word
                    and element.category == "class"
                ):
                    value_found = element
                    break

            if value_found is not None:
                type = previous.word
                category = "object"
            else:
                reason = "Creating object of undefined type"
                self.__errors__.append([previous, reason, previous.word])
                return

        # Check if funtion declaration or function call
        elif next.word == "(":

            # Function call
            if previous.word == ".":
                type = self.__get_actual_type__(before_previous.word, token.word)
                category = "function call"

                # Get params
                params = ""

                while next.word != ")":
                    self.__position__ += 1
                    next = self.__input__[self.__position__]
                    params += next.word + " "

                params.strip()
                params = params[: len(params) - 2]

                # Check the paramater matchs
                if not self.__check_parameters__(before_previous, token, params):
                    return

            # Function declaration
            else:
                type = previous.word
                category = "function"
                self.__loking_func__ = True
                self.__scope__.append(lexeme)

                # Get params
                params = ""
                helper = self.__position__

                while next.word != ")":
                    helper += 1
                    next = self.__input__[helper]
                    params += next.word + " "

                params.strip()
                params = params[: len(params) - 2]

        # Check if accesing object
        elif next.word == ".":
            while True:
                if next.word == "=" or next.word == ";":
                    break

                lexeme += next.word
                self.__position__ += 1
                next = self.__input__[self.__position__]

            type = token.word

            if next.word == ";":
                value = None
            else:
                value = ""
                while True:
                    if next.word == ";":
                        break

                    self.__position__ += 1
                    next = self.__input__[self.__position__]
                    value += next.word + " "

            category = "access object"
            value.strip()
            value = value[: len(value) - 2]

            if value is not None and len(value.strip().split(" ")) == 1:

                val = None
                for element in self.__symbols__:
                    if element.lexeme == lexeme:
                        val = element
                        break

                if val is not None:
                    at = val.type
                    t = self.__get_category__(value.strip())

                    if t is None:
                        for element in self.__symbols__:
                            if element.lexeme == value.strip():
                                t = element.type
                                value = element.value
                                reference = element.lexeme

                    if value is None:
                        reason = "Assigning to undefined variable"
                        self.__errors__.append([token, reason, reference])
                        return

                    if t is not None:
                        at = element.type
                        if at != t:
                            reason = (
                                "Types don't match, expected " + at + " and got"
                            )
                            self.__errors__.append([token, reason, t])
                            return

                else:
                    reason = "Accesing to undeclared property"
                    self.__errors__.append([token, reason, token.word])
                    return

            symbol = Symbol(
                lexeme,
                type,
                category,
                value.word,
                scope,
                extends,
                implements,
                params,
            )
            self.__symbols__.append(symbol)
            return

        # Check if accesing object
        elif previous.word == ".":
            while True:
                if next.word == "=" or next.word == ";":
                    break

                lexeme += next.word
                self.__position__ += 1
                next = self.__input__[self.__position__]

            type = before_previous.word

            if next.word == ";":
                value = None
            else:
                value = ""
                while True:
                    if next.word == ";":
                        break

                    self.__position__ += 1
                    next = self.__input__[self.__position__]
                    value += next.word + " "

            category = "access object"
            value.strip()
            value = value[: len(value) - 2]

            if value is not None and len(value.strip().split(" ")) == 1:

                val = None
                for element in self.__symbols__:
                    if element.lexeme == lexeme:
                        val = element
                        break

                if val is not None:
                    at = val.type
                    t = self.__get_category__(value.strip())

                    if t is None:
                        for element in self.__symbols__:
                            if element.lexeme == value.strip():
                                t = element.type
                                value = element.value
                                reference = element.lexeme

                    if value is None:
                        reason = "Assigning to undefined variable"
                        self.__errors__.append([token, reason, reference])
                        return

                    if t is not None:
                        at = element.type
                        if at != t:
                            reason = (
                                "Types don't match, expected " + at + " and got"
                            )
                            self.__errors__.append([token, reason, t])
                            return

                else:
                    reason = "Accesing to undeclared property"
                    self.__errors__.append([token, reason, token.word])
                    return

        # Simple variable declaration
        else:
            type = previous.word
            category = "variable"

        symbol = Symbol(
            lexeme, type, category, value, scope, extends, implements, params
        )
        self.__symbols__.append(symbol)

        return

    # Return existing symbol
    def __get_symbol__(self, symbol, scope):
        value = None

        for element in self.__symbols__:
            if element.lexeme == symbol and element.scope == scope:
                value = element
                break

        return value

    # Update existing symbol
    def __update_symbol__(self, symbol, scope):
        next = self.__input__[self.__position__]
        value = ""

        if next.word == "=":

            while True:
                if next.word == ";":
                    break

                self.__position__ += 1
                next = self.__input__[self.__position__]
                value += next.word + " "

            value.strip()
            value = value[: len(value) - 2]
            for element in self.__symbols__:
                if element.lexeme == symbol.word and element.scope == scope:
                    if len(value.strip().split(" ")) == 1:

                        t = self.__get_category__(value.strip())

                        if t is None:
                            for element in self.__symbols__:
                                if element.lexeme == value.strip():
                                    t = element.type

                        if t is not None:
                            at = element.type
                            if at != t:
                                reason = (
                                    "Types don't match, expected "
                                    + at
                                    + " and got"
                                )
                                self.__errors__.append([symbol, reason, t])
                                break
                            else:
                                element.value = value.strip()

                    else:
                        element.value = value.strip()

                    break

            return True

        # Symbol already declared
        else:
            value = None
            for element in self.__symbols__:
                if element.lexeme == symbol.word:
                    value = element

                    if (
                        len(scope.split(",")) == 1
                        and value.category == "class"
                        or value.category == "interface"
                    ):
                        break

            if value is not None:
                reason = "Alredy declared " + value.category
            else:
                reason = "Alredy declared"

            self.__errors__.append([symbol, reason, symbol.word])
            skipped = 0
            next = symbol

            while not (next.word == "}" and skipped == 0):
                if next.word == "{":
                    skipped += 1
                elif next.word == "}":
                    skipped -= 1 if skipped != 0 else 0

                self.__position__ += 1
                next = self.__input__[self.__position__]

            return False

    # Check if symbol was declared in any parent scope
    def __declared_before__(self, lexeme):
        helper = self.__scope__.copy()

        while len(helper) > 0:
            value = self.__get_symbol__(lexeme, ",".join(helper))

            if value is None:
                helper.pop()
            else:
                break

        if value is None:
            return False, None
        else:
            return True, value.scope

    # Check if an object is a function call or accesing property
    def __special_object__(self, current, scp):
        before_previous = self.__input__[self.__position__ - 3]
        next = self.__input__[self.__position__]

        value = None
        for element in self.__symbols__:
            if element.lexeme == before_previous.word and element.scope == scp:
                value = element
                break

        if value is not None:
            new_scope = value.scope

            if next.word == "(":

                method_found = None
                for element in self.__symbols__:
                    if (
                        element.lexeme == current.word
                        and element.scope == new_scope
                    ):
                        method_found = element
                        break

                if method_found is None:
                    new_symbol = None
                    for element in self.__symbols__:
                        if (
                            element.lexeme == before_previous.word
                            and element.scope == "Global"
                        ):
                            new_symbol = element
                            break

                    if new_symbol is not None:
                        if new_symbol.implements is not None:
                            for element in self.__symbols__:
                                if (
                                    element.lexeme == current.word
                                    and element.scope
                                    == "Global," + new_symbol.implements
                                ):
                                    method_found = element
                                    break

                        if method_found is None:
                            found = False
                            for extended in new_symbol.extends.split(","):
                                for element in self.__symbols__:
                                    if (
                                        element.lexeme == current.word
                                        and element.scope == "Global," + extended
                                    ):
                                        found = True
                                        method_found = element
                                        break

                                if found:
                                    break

                if method_found is not None:
                    return True
                else:
                    reason = "Calling to undeclared method"
                    self.__errors__.append([current, reason, current.word])
                    return False

            else:
                property_found = None
                for element in self.__symbols__:
                    if (
                        element.lexeme == current.word
                        and element.scope == new_scope
                    ):
                        property_found = element
                        break

                if property_found is None:
                    new_symbol = None
                    for element in self.__symbols__:
                        if (
                            element.lexeme == before_previous.word
                            and element.scope == "Global"
                        ):
                            new_symbol = element
                            break

                    if new_symbol is not None:
                        if new_symbol.implements is not None:
                            for element in self.__symbols__:
                                if (
                                    element.lexeme == current.word
                                    and element.scope
                                    == "Global," + new_symbol.implements
                                ):
                                    property_found = element
                                    break

                        if property_found is None:
                            found = False
                            for extended in new_symbol.extends.split(","):
                                for element in self.__symbols__:
                                    if (
                                        element.lexeme == current.word
                                        and element.scope == "Global," + extended
                                    ):
                                        found = True
                                        property_found = element
                                        break

                                if found:
                                    break

                if property_found is not None:
                    return True
                else:
                    reason = "Accesing to undeclared property"
                    self.__errors__.append([current, reason, current.word])
                    return False

        else:
            reason = "Accesing to undeclared object"
            self.__errors__.append([current, reason, current.word])
            return False

    # Check if a method an parameters matchs
    def __check_parameters__(self, before, current, params):
        if before.category == "Identifier":
            value = None
            for element in self.__symbols__:
                if element.lexeme == before.word:
                    value = element
                    break

            if value is not None:
                class_found = value.type

                method_found = None
                for element in self.__symbols__:
                    if (
                        element.lexeme == current.word
                        and element.scope == "Global," + class_found
                    ):
                        method_found = element
                        break

                if method_found is None:
                    new_symbol = None
                    for element in self.__symbols__:
                        if (
                            element.lexeme == class_found
                            and element.scope == "Global"
                        ):
                            new_symbol = element
                            break

                    if new_symbol is not None:
                        if new_symbol.implements is not None:
                            for element in self.__symbols__:
                                if (
                                    element.lexeme == current.word
                                    and element.scope
                                    == "Global," + new_symbol.implements
                                ):
                                    method_found = element
                                    break

                        if method_found is None:
                            found = False
                            for extended in new_symbol.extends.split(","):
                                for element in self.__symbols__:
                                    if (
                                        element.lexeme == current.word
                                        and element.scope == "Global," + extended
                                    ):
                                        found = True
                                        method_found = element
                                        break

                                if found:
                                    break

            else:
                reason = "Accesing to undeclared object"
                self.__errors__.append([current, reason, current.word])
                return False

        else:
            method_found = None
            for element in self.__symbols__:
                if element.lexeme == current.word and element.scope == ",".join(
                    self.__scope__
                ):
                    method_found = element
                    break

        if method_found is not None:
            actuals = method_found.params.strip().split(" , ")
            to_check = params.strip().split(" , ")
            errors = False

            if len(actuals) == len(to_check):
                for i, _ in enumerate(actuals):
                    a = actuals[i]
                    p = to_check[i]

                    # Get the category
                    t = self.__get_category__(p)

                    if t is None:
                        for element in self.__symbols__:
                            if element.lexeme == p:
                                t = element.type

                    if t is not None:
                        at = a.split(" ")[0].strip()
                        if at != t:
                            reason = (
                                "Types don't match in argument number "
                                + str(i + 1)
                                + ", expected "
                                + at
                                + " and got"
                            )
                            self.__errors__.append([current, reason, t])
                            errors = True

                return not errors

            else:
                if len(to_check) > len(actuals):
                    reason = (
                        "Too many parameters, expected "
                        + str(len(actuals))
                        + " and got"
                    )
                    self.__errors__.append([current, reason, str(len(to_check))])
                    return False
                else:
                    reason = (
                        "Missing parameters, expected "
                        + str(len(actuals))
                        + " and got"
                    )
                    self.__errors__.append([current, reason, str(len(to_check))])
                    return False

        else:
            reason = "Calling to undeclared method"
            self.__errors__.append([current, reason, current.word])
            return False

    # Check if a property is defined in a class
    def __check_property__(self, current):
        before_previous = self.__input__[self.__position__ - 3]
        next = self.__input__[self.__position__]

        value = None
        for element in self.__symbols__:
            if element.lexeme == before_previous.word:
                value = element
                break

        if value is not None:
            class_found = value.type

            if next.word == "(":

                method_found = None
                for element in self.__symbols__:
                    if (
                        element.lexeme == current.word
                        and element.scope == "Global," + class_found
                    ):
                        method_found = element
                        break

                if method_found is None:
                    new_symbol = None
                    for element in self.__symbols__:
                        if (
                            element.lexeme == class_found
                            and element.scope == "Global"
                        ):
                            new_symbol = element
                            break

                    if new_symbol is not None:
                        if new_symbol.implements is not None:
                            for element in self.__symbols__:
                                if (
                                    element.lexeme == current.word
                                    and element.scope
                                    == "Global," + new_symbol.implements
                                ):
                                    method_found = element
                                    break

                        if method_found is None:
                            found = False
                            for extended in new_symbol.extends.split(","):
                                for element in self.__symbols__:
                                    if (
                                        element.lexeme == current.word
                                        and element.scope == "Global," + extended
                                    ):
                                        found = True
                                        method_found = element
                                        break

                                if found:
                                    break

                if method_found is not None:
                    return True
                else:
                    reason = "Calling to undeclared method"
                    self.__errors__.append([current, reason, current.word])
                    return False

            else:
                property_found = None
                for element in self.__symbols__:
                    if (
                        element.lexeme == current.word
                        and element.scope == "Global," + class_found
                    ):
                        property_found = element
                        break

                if property_found is None:
                    new_symbol = None
                    for element in self.__symbols__:
                        if (
                            element.lexeme == class_found
                            and element.scope == "Global"
                        ):
                            new_symbol = element
                            break

                    if new_symbol is not None:
                        if new_symbol.implements is not None:
                            for element in self.__symbols__:
                                if (
                                    element.lexeme == current.word
                                    and element.scope
                                    == "Global," + new_symbol.implements
                                ):
                                    property_found = element
                                    break

                        if property_found is None:
                            found = False
                            for extended in new_symbol.extends.split(","):
                                for element in self.__symbols__:
                                    if (
                                        element.lexeme == current.word
                                        and element.scope == "Global," + extended
                                    ):
                                        found = True
                                        property_found = element
                                        break

                                if found:
                                    break

                if property_found is not None:
                    return True
                else:
                    reason = "Accesing to undeclared property"
                    self.__errors__.append([current, reason, current.word])
                    return False

        else:
            reason = "Accesing to undeclared object"
            self.__errors__.append([current, reason, current.word])
            return False

    def __get_actual_type__(self, previous, current):
        value = None

        for element in self.__symbols__:
            if element.lexeme == previous:
                value = element
                break

        if value is not None:
            method_found = value.scope.split(",")[-1]
            scope_found = value.scope.split(",")[:-1]

            type_found = None
            for element in self.__symbols__:
                if element.lexeme == method_found and element.scope == ",".join(
                    scope_found
                ):
                    type_found = element
                    break

            if type_found is not None:
                return type_found.type
            else:
                return None
        else:
            return None

    def __get_category__(self, word):
        # Recognize int base 10 number
        if re.search(r"^[0-9]+$", word):
            return "int"

        # Recognize int base 16 number
        elif re.search(r"^0[x|X][0-9a-fA-F]+$", word):
            return "int"

        # Recognize double number
        elif re.search(r"^[0-9]+\.?[0-9]*([e|E][+|-]?[0-9]+)?$", word):
            return "double"

        # Recognize string
        elif re.search(r"^\".*\"$", word):
            return "string"

        # Recognize boolean
        elif word == "true" or word == "false":
            return "boolean"

        else:
            return None
