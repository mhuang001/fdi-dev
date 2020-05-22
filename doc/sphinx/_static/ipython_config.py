# sample ipython_config.py
from IPython.terminal.prompts import Prompts, Token
import os
c = get_config()


class MyPrompts(Prompts):
    def in_prompt_tokens(self, cli=None):
        return [(Token, '>>> ')]

    def continuation_prompt_tokens(self, cli=None):
        return [(Token, '... ')]

    def out_prompt_tokens(self, cli=None):
        return [(Token, '')]


c.InteractiveShell.prompts_class = MyPrompts
