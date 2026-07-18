import re
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat
from theme import Theme

class UniversalHighlighter(QSyntaxHighlighter):
    _rules_cache = {}

    def __init__(self, parent, theme_dict=Theme.LILAC):
        super().__init__(parent)
        self.theme = theme_dict
        self.rules = []
        self.current_language = None

    def set_language(self, language):
        self.current_language = language
        theme_key = getattr(self, '_theme_name', id(self.theme))
        cache_key = (language, theme_key)
        if cache_key in self._rules_cache:
            self.rules = self._rules_cache[cache_key]
        else:
            self._setup_rules()
            self._rules_cache[cache_key] = self.rules
        self.rehighlight()

    def _setup_rules(self):
        self.rules = []
        
        # --- Shared Patterns ---
        # Strings: triple quotes first, then single/double
        string_pattern = r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\''
        
        # Numbers: Floats, Hex, Octal, Binary, Decimals
        number_pattern = r'\b(?:0x[\da-fA-F]+|0b[01]+|0o[0-7]+|\d*\.\d+(?:[eE][+-]?\d+)?|\d+(?:[eE][+-]?\d+)?)\b'
        
        # Operators
        operator_pattern = r'(?:\+\+|--|=>|->|==|!=|<=|>=|&&|\|\||[+\-*/%&|^<>!=])'

        # --- Language Specific Rules ---
        keywords = []
        comment_pattern = r"#.*" # Default
        type_keywords = []
        function_pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*(?=\s*\()' # Function calls
        decorator_pattern = r'@\w+'

        if self.current_language == "python":
            keywords = [
                "False", "None", "True", "and", "as", "assert", "async", "await",
                "break", "class", "continue", "def", "del", "elif", "else", "except",
                "finally", "for", "from", "global", "if", "import", "in", "is",
                "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
                "try", "while", "with", "yield"
            ]
            comment_pattern = r"#.*"
            type_keywords = ["int", "float", "str", "bool", "list", "dict", "set", "tuple", "None"]
            decorator_pattern = r'@\w+'
        elif self.current_language == "bash":
            keywords = ["if", "then", "else", "elif", "fi", "case", "esac", "for", "while", "do", "done", "function"]
            comment_pattern = r"#.*"
        elif self.current_language == "cpp":
            keywords = ["break", "case", "continue", "default", "do", "else", "for", "if", "switch", "while", "return", "sizeof", "typedef", "volatile", "static", "extern", "const", "enum", "struct", "union", "namespace", "using", "virtual", "override", "final", "template", "typename", "throw", "try", "catch", "public", "private", "protected"]
            type_keywords = ["int", "float", "double", "char", "void", "bool", "long", "short", "signed", "unsigned", "auto", "decltype"]
            comment_pattern = r"//.*|/\*[\s\S]*?\*/"
        elif self.current_language == "javascript":
            keywords = ["break", "case", "catch", "class", "const", "continue", "debugger", "default", "delete", "do", "else", "export", "extends", "finally", "for", "function", "if", "import", "in", "instanceof", "new", "return", "super", "switch", "this", "throw", "try", "typeof", "var", "void", "while", "with", "yield", "let", "static", "async", "await"]
            comment_pattern = r"//.*|/\*[\s\S]*?\*/"
        elif self.current_language == "rust":
            keywords = ["as", "break", "const", "continue", "crate", "else", "enum", "extern", "false", "fn", "for", "if", "impl", "in", "let", "loop", "match", "mod", "move", "mut", "pub", "ref", "return", "self", "static", "struct", "super", "trait", "true", "type", "unsafe", "use", "where", "while", "async", "await", "dyn"]
            type_keywords = ["i8", "i16", "i32", "i64", "i128", "isize", "u8", "u16", "u32", "u64", "u128", "usize", "f32", "f64", "str", "bool", "char"]
            comment_pattern = r"//.*|/\*[\s\S]*?\*/"
            decorator_pattern = r'#\[\w+\]'
        elif self.current_language == "sql":
            keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "FROM", "WHERE", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER", "GROUP BY", "ORDER BY", "HAVING", "LIMIT", "OFFSET", "UNION", "ALL", "CREATE", "ALTER", "DROP", "TABLE", "INDEX", "VIEW", "DATABASE", "GRANT", "REVOKE", "COMMIT", "ROLLBACK", "SAVEPOINT", "SET", "VALUES", "INTO", "AND", "OR", "NOT", "IN", "LIKE", "IS", "NULL", "BETWEEN", "EXISTS", "ANY", "ALL"]
            comment_pattern = r"--.*"
        elif self.current_language == "json":
            keywords = []
            comment_pattern = r""  # JSON has no comments
            # JSON keys: string followed by colon
            self.rules.append((re.compile(r'"(?:[^"\\]|\\.)*"(?=\s*:)'), self._create_format(Theme.get_color(self.theme, "keyword"))))
        elif self.current_language == "yaml":
            keywords = []
            comment_pattern = r"#.*"
        elif self.current_language == "toml":
            keywords = []
            comment_pattern = r"#.*"
        elif self.current_language == "markdown":
            keywords = []
            comment_pattern = r"" # Not used for markdown
            
            # Markdown Specific Rules
            # Headers: # Header
            self.rules.append((re.compile(r'^#{1,6}\s+.*'), self._create_format(Theme.get_color(self.theme, "heading"))))
            # Bold: **bold** or __bold__
            self.rules.append((re.compile(r'(\*\*|__)(.*?)\1'), self._create_format(Theme.get_color(self.theme, "bold"))))
            # Italic: *italic* or _italic_
            self.rules.append((re.compile(r'(\*|_)(.*?)\1'), self._create_format(Theme.get_color(self.theme, "italic"))))
            # Images: ![alt](url)
            self.rules.append((re.compile(r'!\[.*?\]\(.*?\)'), self._create_format(Theme.get_color(self.theme, "number"))))
            # Links: [text](url)
            self.rules.append((re.compile(r'\[.*?\]\(.*?\)'), self._create_format(Theme.get_color(self.theme, "link"))))
            # Inline Code: `code`
            self.rules.append((re.compile(r'`.*?`'), self._create_format(Theme.get_color(self.theme, "code"))))
            # Blockquotes: > quote
            self.rules.append((re.compile(r'^>.*'), self._create_format(Theme.get_color(self.theme, "string"))))
            # Lists: - item, * item, 1. item
            self.rules.append((re.compile(r'^(\s*([-*+]|\d+\.)\s+.*)'), self._create_format(Theme.get_color(self.theme, "keyword"))))
            # HR: ---, ***, ___
            self.rules.append((re.compile(r'^(\s*([-*_])\s*([-*_])\s*([-*_])\s*$)'), self._create_format(Theme.get_color(self.theme, "operator"))))

        elif self.current_language == "html":
            keywords = []
            comment_pattern = r"<!--[\s\S]*?-->"
            # HTML Tags
            self.rules.append((re.compile(r'</?\w+.*?>'), self._create_format(Theme.get_color(self.theme, "keyword"))))
            # HTML Attributes
            self.rules.append((re.compile(r'\b\w+(?=\s*=)'), self._create_format(Theme.get_color(self.theme, "type"))))
        elif self.current_language == "css":
            keywords = []
            comment_pattern = r"/\*[\s\S]*?\*/"
            # CSS Selectors/Properties
            self.rules.append((re.compile(r'[\.#][\w-]+'), self._create_format(Theme.get_color(self.theme, "function"))))
            self.rules.append((re.compile(r'\b\w+(?=\s*:)'), self._create_format(Theme.get_color(self.theme, "type"))))
        else:
            keywords = []
            comment_pattern = r"#.*"

        # --- Applying Rules ---
        # 1. Keywords
        if keywords:
            pattern = r"\b(" + "|".join(map(re.escape, keywords)) + r")\b"
            self.rules.append((re.compile(pattern), self._create_format(Theme.get_color(self.theme, "keyword"))))
        
        # 2. Types
        if type_keywords:
            pattern = r"\b(" + "|".join(map(re.escape, type_keywords)) + r")\b"
            self.rules.append((re.compile(pattern), self._create_format(Theme.get_color(self.theme, "type"))))
            
        # 3. Functions
        self.rules.append((re.compile(function_pattern), self._create_format(Theme.get_color(self.theme, "function"))))
        
        # 4. Decorators/Attributes
        if decorator_pattern:
            self.rules.append((re.compile(decorator_pattern), self._create_format(Theme.get_color(self.theme, "decorator"))))
            
        # 5. Numbers
        self.rules.append((re.compile(number_pattern), self._create_format(Theme.get_color(self.theme, "number"))))
        
        # 6. Operators
        self.rules.append((re.compile(operator_pattern), self._create_format(Theme.get_color(self.theme, "operator"))))

        # 7. Comments (before strings — overwrites keywords inside comments)
        if comment_pattern:
            self.rules.append((re.compile(comment_pattern), self._create_format(Theme.get_color(self.theme, "comment"))))

        # 8. Strings (last — overwrites everything, so `#` inside strings stays string-colored)
        self.rules.append((re.compile(string_pattern), self._create_format(Theme.get_color(self.theme, "string"))))

    def _create_format(self, color):
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        return fmt

    def highlightBlock(self, text):
        # Handle Markdown Fenced Code Blocks
        if self.current_language == "markdown":
            if text.strip().startswith("```"):
                self.setCurrentBlockState(0 if self.previousBlockState() == 1 else 1)
                self.setFormat(0, len(text), self._create_format(Theme.get_color(self.theme, "code")))
                return

            if self.previousBlockState() == 1:
                self.setCurrentBlockState(1)
                self.setFormat(0, len(text), self._create_format(Theme.get_color(self.theme, "code")))
                return

            self.setCurrentBlockState(0)

        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)
