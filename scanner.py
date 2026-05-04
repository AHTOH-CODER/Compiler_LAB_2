import re
from typing import List, Tuple, Optional, Dict, Any


class Token:
    """Класс, представляющий лексему"""

    CODES = {
        'KEYWORD': 1,           # val, var, def, class, object, new, Complex
        'IDENTIFIER': 2,        # x, Complex, real
        'INTEGER': 3,           # 0, 42, 100
        'FLOAT': 4,             # 3.14, 0.5, 2.0
        'IMAGINARY': 5,         # 1.0i, 2i (мнимая единица)
        'DELIMITER': 6,         # пробел, \n, \t
        'OPERATOR': 7,          # =, +, -, *, /, ==, !=, <, >, <=, >=
        'LPAREN': 8,            # (
        'RPAREN': 9,            # )
        'LBRACKET': 10,         # [
        'RBRACKET': 11,         # ]
        'LBRACE': 12,           # {
        'RBRACE': 13,           # }
        'COMMA': 14,            # ,
        'DOT': 15,              # .
        'COLON': 16,            # :
        'SEMICOLON': 17,        # ;
        'COMMENT': 18,          # // однострочный комментарий
        'ERROR': 99             # недопустимый символ
    }

    RU_TYPES = {
        'KEYWORD': 'КЛЮЧЕВОЕ СЛОВО',
        'IDENTIFIER': 'ИДЕНТИФИКАТОР',
        'INTEGER': 'ЦЕЛОЕ ЧИСЛО',
        'FLOAT': 'ВЕЩЕСТВЕННОЕ ЧИСЛО',
        'IMAGINARY': 'МНИМОЕ ЧИСЛО',
        'DELIMITER': 'РАЗДЕЛИТЕЛЬ',
        'OPERATOR': 'ОПЕРАТОР',
        'LPAREN': 'ЛЕВАЯ СКОБКА',
        'RPAREN': 'ПРАВАЯ СКОБКА',
        'LBRACKET': 'ЛЕВАЯ КВАДРАТНАЯ СКОБКА',
        'RBRACKET': 'ПРАВАЯ КВАДРАТНАЯ СКОБКА',
        'LBRACE': 'ЛЕВАЯ ФИГУРНАЯ СКОБКА',
        'RBRACE': 'ПРАВАЯ ФИГУРНАЯ СКОБКА',
        'COMMA': 'ЗАПЯТАЯ',
        'DOT': 'ТОЧКА',
        'COLON': 'ДВОЕТОЧИЕ',
        'SEMICOLON': 'ТОЧКА С ЗАПЯТОЙ',
        'COMMENT': 'КОММЕНТАРИЙ',
        'ERROR': 'ОШИБКА'
    }

    EN_TYPES = {
        'KEYWORD': 'KEYWORD',
        'IDENTIFIER': 'IDENTIFIER',
        'INTEGER': 'INTEGER',
        'FLOAT': 'FLOAT',
        'IMAGINARY': 'IMAGINARY',
        'DELIMITER': 'DELIMITER',
        'OPERATOR': 'OPERATOR',
        'LPAREN': 'LEFT PAREN',
        'RPAREN': 'RIGHT PAREN',
        'LBRACKET': 'LEFT BRACKET',
        'RBRACKET': 'RIGHT BRACKET',
        'LBRACE': 'LEFT BRACE',
        'RBRACE': 'RIGHT BRACE',
        'COMMA': 'COMMA',
        'DOT': 'DOT',
        'COLON': 'COLON',
        'SEMICOLON': 'SEMICOLON',
        'COMMENT': 'COMMENT',
        'ERROR': 'ERROR'
    }

    def __init__(self, token_type: str, value: str, line: int, start: int, end: int):
        self.token_type = token_type
        self.value = value
        self.line = line
        self.start = start
        self.end = end
        self.code = self.CODES.get(token_type, 99)

    def __repr__(self):
        return f"Token({self.token_type}, '{self.value}', line={self.line}, pos={self.start}-{self.end})"

    def get_display_type(self, lang='ru'):
        if lang == 'ru':
            return self.RU_TYPES.get(self.token_type, self.token_type)
        else:
            return self.EN_TYPES.get(self.token_type, self.token_type)

    def get_display_value(self, lang='ru'):
        if self.value == ' ':
            return '(пробел)' if lang == 'ru' else '(space)'
        elif self.value == '\n':
            return '\\n'
        elif self.value == '\t':
            return '\\t'
        return self.value

    def to_table_row(self, lang='ru') -> tuple:
        if lang == 'ru':
            location = f"строка {self.line}, {self.start}-{self.end}"
        else:
            location = f"line {self.line}, {self.start}-{self.end}"
        return (self.code, self.get_display_type(lang), self.get_display_value(lang), location)


class Scanner:
    """
    Лексический анализатор для объявления комплексных чисел в Scala.
    Примеры корректного ввода:
    val c1: Complex = new Complex(1.0, 2.0)
    val c2 = Complex(3, 4)
    val c3 = 5 + 3i
    """

    KEYWORDS = {
        'val', 'var', 'def', 'class', 'object', 'new', 'extends',
        'with', 'trait', 'import', 'package', 'private', 'protected',
        'override', 'implicit', 'lazy', 'sealed', 'final', 'abstract',
        'case', 'this', 'super', 'return', 'if', 'else', 'while',
        'for', 'yield', 'match', 'try', 'catch', 'finally', 'throw',
        'type', 'true', 'false', 'null', 'Complex'
    }

    OPERATORS = {'=', '+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>='}

    # Специальные символы с индивидуальными кодами
    SEPARATORS = {
        '(': 'LPAREN',
        ')': 'RPAREN',
        '[': 'LBRACKET',
        ']': 'RBRACKET',
        '{': 'LBRACE',
        '}': 'RBRACE',
        ',': 'COMMA',
        '.': 'DOT',
        ':': 'COLON',
        ';': 'SEMICOLON'
    }

    DELIMITERS = {' ', '\t', '\n'}

    def __init__(self):
        self.tokens: List[Token] = []
        self.errors: List[Token] = []
        self.line = 1
        self.pos = 1
        self.text = ""
        self.index = 0

    def analyze(self, text: str) -> Dict[str, Any]:
        """Основной метод анализа текста"""
        self.tokens = []
        self.errors = []
        self.line = 1
        self.pos = 1
        self.index = 0
        self.text = text

        if not text:
            return {'tokens': [], 'errors': []}

        while self.index < len(self.text):
            ch = self.text[self.index]

            # Пробельные символы (пробел, табуляция)
            if ch in (' ', '\t'):
                self._handle_whitespace()
            # Перевод строки
            elif ch == '\n':
                self._handle_newline()
            # Цифра → целое / вещественное / мнимое
            elif ch.isdigit():
                self._handle_number()
            # Буква или _ → идентификатор / ключевое слово
            elif ch.isalpha() or ch == '_':
                self._handle_identifier_or_keyword()
            # Специальные символы (скобки, запятые и т.д.)
            elif ch in self.SEPARATORS:
                self._handle_special_char(ch)
            # Операторы (+, -, *, /, =, <, >, !)
            elif ch in '+-*/=<>!':
                self._handle_operator()
            # Комментарий //
            elif ch == '/' and self.index + 1 < len(self.text) and self.text[self.index + 1] == '/':
                self._handle_comment()
            # Недопустимый символ
            else:
                self._handle_error(f"Недопустимый символ: '{ch}'")

        return {
            'tokens': self.tokens,
            'errors': self.errors
        }

    def _handle_whitespace(self):
        """Обработка пробелов и табуляций"""
        start_pos = self.pos
        value = ''
        while self.index < len(self.text) and self.text[self.index] in (' ', '\t'):
            value += self.text[self.index]
            self._advance()
        token = Token('DELIMITER', value, self.line, start_pos, start_pos + len(value) - 1)
        self.tokens.append(token)

    def _handle_newline(self):
        """Обработка символа новой строки"""
        token = Token('DELIMITER', '\n', self.line, self.pos, self.pos)
        self.tokens.append(token)
        self.line += 1
        self.pos = 1
        self.index += 1

    def _handle_number(self):
        """Обработка чисел: целых, вещественных и мнимых (например: 5, 3.14, 2i, 1.0i)"""
        start_pos = self.pos
        value = ''
        is_float = False

        # Целая часть
        while self.index < len(self.text) and self.text[self.index].isdigit():
            value += self.text[self.index]
            self._advance()

        # Дробная часть
        if self.index < len(self.text) and self.text[self.index] == '.':
            if self.index + 1 < len(self.text) and self.text[self.index + 1].isdigit():
                is_float = True
                value += '.'
                self._advance()
                while self.index < len(self.text) and self.text[self.index].isdigit():
                    value += self.text[self.index]
                    self._advance()

        # Мнимая единица 'i'
        if self.index < len(self.text) and self.text[self.index] == 'i':
            value += 'i'
            self._advance()
            token = Token('IMAGINARY', value, self.line, start_pos, start_pos + len(value) - 1)
            self.tokens.append(token)
            return

        # Определяем тип
        if is_float:
            token_type = 'FLOAT'
        else:
            token_type = 'INTEGER'
        token = Token(token_type, value, self.line, start_pos, start_pos + len(value) - 1)
        self.tokens.append(token)

    def _handle_identifier_or_keyword(self):
        """Обработка идентификаторов и ключевых слов"""
        start_pos = self.pos
        value = ''
        while self.index < len(self.text) and (self.text[self.index].isalnum() or self.text[self.index] == '_'):
            value += self.text[self.index]
            self._advance()

        if value in self.KEYWORDS:
            token_type = 'KEYWORD'
        else:
            token_type = 'IDENTIFIER'

        token = Token(token_type, value, self.line, start_pos, start_pos + len(value) - 1)
        self.tokens.append(token)

    def _handle_operator(self):
        """Обработка операторов (включая составные: ==, !=, <=, >=)"""
        start_pos = self.pos
        ch = self.text[self.index]
        if ch in '=!<>' and self.index + 1 < len(self.text) and self.text[self.index + 1] == '=':
            op = ch + '='
            self._advance()
            self._advance()
        else:
            op = ch
            self._advance()

        if op in self.OPERATORS:
            token = Token('OPERATOR', op, self.line, start_pos, start_pos + len(op) - 1)
            self.tokens.append(token)
        else:
            self._add_error(f"Недопустимый оператор: '{op}'", self.line, start_pos, start_pos + len(op) - 1)

    def _handle_special_char(self, ch):
        """Обработка специальных символов с индивидуальными кодами"""
        token_type = self.SEPARATORS[ch]
        token = Token(token_type, ch, self.line, self.pos, self.pos)
        self.tokens.append(token)
        self._advance()

    def _handle_comment(self):
        """Обработка однострочного комментария //"""
        start_pos = self.pos
        value = ''
        while self.index < len(self.text) and self.text[self.index] != '\n':
            value += self.text[self.index]
            self._advance()
        token = Token('COMMENT', value, self.line, start_pos, start_pos + len(value) - 1)
        self.tokens.append(token)

    def _handle_error(self, message: str):
        """Обработка недопустимого символа"""
        self._add_error(message, self.line, self.pos, self.pos)
        self._advance()

    def _add_error(self, message: str, line: int, start: int, end: int):
        """Добавление ошибки в список"""
        token = Token('ERROR', message, line, start, end)
        self.errors.append(token)
        self.tokens.append(token)

    def _advance(self):
        """Переход к следующему символу"""
        self.index += 1
        self.pos += 1

    def get_token_table_data(self, lang='ru') -> List[tuple]:
        return [token.to_table_row(lang) for token in self.tokens]

    def get_errors_table_data(self, lang='ru') -> List[tuple]:
        return [token.to_table_row(lang) for token in self.errors]


# ══════════════════════════════════════════════════════════════════════════
# Если запустить scanner.py напрямую — выполнится простой тест
if __name__ == '__main__':
    scanner = Scanner()
    test_code = 'val c1: Complex = new Complex(1.0, 2.0)'
    results = scanner.analyze(test_code)
    print("Токены:")
    for t in results['tokens']:
        print(t.to_table_row('ru'))
    print("\nОшибки:")
    for e in results['errors']:
        print(e.to_table_row('ru'))