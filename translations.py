import gettext

# Set the locale directory, where the translation files will be stored.
locale_dir = 'locale'


def _get_text(text):
    """Returns translated strings"""

    # Translates lists of strings
    if(isinstance(text, list)):
        translated_list = []
        for elem in text:
            translated_list.append(_get_text(elem))
        return translated_list


    return gettext.gettext(text)
    


def setup_i18n(language_code, locale_dir='locale'):
    # Set up the translations.
    gettext.bindtextdomain('my_app', locale_dir)
    gettext.textdomain('my_app')

    if language_code:
        import locale
        import os

        os.environ['LANGUAGE'] = language_code
        locale.setlocale(locale.LC_ALL, '')
    return _get_text