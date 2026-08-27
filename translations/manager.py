from translations import LANGUAGES


class LanguageManager:

    def __init__(self):
        self.language = "ENG"

    def set_language(self, language):
        if language in LANGUAGES:
            self.language = language

    def get(self, key, default=""):
        return LANGUAGES[self.language].get(key, default or key)



#.