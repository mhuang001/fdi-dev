from pygments.token import Keyword, Name, Comment, String, Error, \
    Number, Operator, Generic, Literal, Punctuation, Whitespace, \
    Text, STANDARD_TYPES, Token, Other
from pygments.style import Style
from pygments.styles.monokai import MonokaiStyle


class MonokaiMod(MonokaiStyle):
    styles = MonokaiStyle.styles
    styles.update({
        Comment: 'bold italic #af2',
        Literal.String.Doc: 'bold italic #af2',
        Generic.Output: 'bg:#022 ansibrightcyan',
        Text: 'bg:#022 ansibrightcyan'
    })
