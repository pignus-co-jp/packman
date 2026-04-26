from enum import Enum


class SearchStatusCondition(Enum):
    EQUALS = "equals"
    DOES_NOT_EQUAL = "does_not_equal"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"


class SearchRichTextCondition(Enum):
    CONTAINS = "contains"
    DOES_NOT_CONTAIN = "does_not_contain"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"


class SearchSelectCondition(Enum):
    EQUALS = "equals"
    DOES_NOT_EQUAL = "does_not_equal"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"


class SearchMultiSelectCondition(Enum):
    CONTAINS = "contains"
    DOES_NOT_CONTAIN = "does_not_contain"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"


class SearchTitleCondition(Enum):
    CONTAINS = "contains"
    DOES_NOT_CONTAIN = "does_not_contain"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"


class SearchPropertyType(Enum):
    STATUS = "status"
    RICH_TEXT = "rich_text"
    SELECT = "select"


class FilterBuilder:

    @staticmethod
    def status(property_name: str, value: str, condition: SearchStatusCondition = SearchStatusCondition.EQUALS):
        return {
            "property": property_name,
            "status": {
                condition.value: value
            }
        }

    @staticmethod
    def rich_text(property_name: str, value: str, condition: SearchRichTextCondition = SearchRichTextCondition.CONTAINS):
        return {
            "property": property_name,
            "rich_text": {
                condition.value: value
            }
        }

    @staticmethod
    def select(property_name: str, value: str, condition: SearchSelectCondition = SearchStatusCondition.EQUALS):
        return {
            "property": property_name,
            "select": {
                condition.value: value
            }
        }

    @staticmethod
    def multi_select(property_name: str, value: str, condition: SearchMultiSelectCondition = SearchMultiSelectCondition.CONTAINS):
        return {
            "property": property_name,
            "multi_select": {
                condition.value: value
            }
        }

    @staticmethod
    def title(property_name: str, value: str, condition: SearchTitleCondition = SearchTitleCondition.CONTAINS):
        return {
            "property": property_name,
            "title": {
                condition.value: value
            }
        }


class CompoundFilter:
    @staticmethod
    def AND(*filters: dict):
        return {"and": list(filters)}

    @staticmethod
    def OR(*filters: dict):
        return {"or": list(filters)}
