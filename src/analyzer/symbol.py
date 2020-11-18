class Symbol:
    def __init__(self, type, category, value=None, scope=None):
        self.__type__ = type
        self.__category__ = category
        self.__value__ = value
        self.__scope__ = scope

    @property
    def type(self):
        return self.__type__

    @type.setter
    def type(self, type):
        self.__type__ = type

    @property
    def category(self):
        return self.__category__

    @category.setter
    def category(self, category):
        self.__category__ = category

    @property
    def value(self):
        return self.__value__

    @value.setter
    def value(self, value):
        self.__value__ = value

    @property
    def scope(self):
        return self.__scope__

    @scope.setter
    def scope(self, scope):
        self.__scope__ = scope
