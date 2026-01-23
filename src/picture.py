from datetime import datetime

from gi.repository.GObject import GObject, Property, TYPE_PYOBJECT

from .date_utils import parse_fuzzy_date


class CassetteItem(GObject):
    _name: str = ""
    _label: str = ""

    _date: datetime | None = None
    _date_err: str = ""
    _date_backing: str = ""

    _slide_date: datetime | None = None
    _slide_date_err: str = ""
    _slide_date_backing: str = ""

    @Property(type=str)
    def name(self):
        return self._name

    @name.setter
    def name(self, val):
        self._name = val

    @Property(type=str)
    def label(self):
        return self._label

    @label.setter
    def label(self, val):
        self._label = val

    @Property(type=TYPE_PYOBJECT)
    def date(self):
        return self._date

    @Property(type=str)
    def date_backing(self):
        return self._date_backing

    @date_backing.setter
    def date_backing(self, value: str):
        self._date_backing = value
        self._date, err = parse_fuzzy_date(value)
        self._date_err = err or ""

    @Property(type=TYPE_PYOBJECT)
    def slide_date(self):
        return self._slide_date

    @Property(type=str)
    def slide_date_backing(self):
        return self._slide_date_backing

    @slide_date_backing.setter
    def slide_date_backing(self, value: str):
        self._slide_date_backing = value
        self._slide_date, err = parse_fuzzy_date(value)
        self._slide_date_err = err or ""
