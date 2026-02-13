from abc import ABC, abstractmethod
import time
import sys


class CLIArgs:
    """
    --flag
    --key=value
    positional args
    に対応した軽量 CLI パーサ
    """

    def __init__(self, argv):
        self.flags = set()
        self.options = {}
        self.positionals = []

        for arg in argv[1:]:
            if arg.startswith("--"):
                if "=" in arg:
                    key, value = arg[2:].split("=", 1)
                    self.options[key] = value
                else:
                    self.flags.add(arg[2:])
            else:
                self.positionals.append(arg)

    def has_flag(self, name: str) -> bool:
        return name in self.flags

    def get(self, key: str, default=None):
        return self.options.get(key, default)

    def get_positional(self, index: int, default=None):
        if index < len(self.positionals):
            return self.positionals[index]
        return default


class PPConsole(ABC):
    @abstractmethod
    def _onInputString(self, raw_input: str):
        """入力文字列を処理する（サブクラスで実装）"""
        pass

    @abstractmethod
    def _onDestroy(self):
        """コンソール終了時の後処理（サブクラスで実装）"""
        pass

    def __init__(self):
        self.argv = CLIArgs(sys.argv)

        self.cmark = ">"
        self.exitkeyword = "ppexit"

        self.__is_input = self.argv.has_flag("console")
        self._active = True

    def wait_forever(self):
        try:
            while self._active:
                if self.__is_input:
                    try:
                        raw_input = input(self.cmark)
                        if raw_input == self.exitkeyword:
                            self.destroy()
                            break
                        self._onInputString(raw_input)
                    except Exception as ex:
                        print(f"[Console Error] {ex}")
                else:
                    time.sleep(1)
        except KeyboardInterrupt:
            self.destroy()

    def destroy(self):
        self._active = False
        self._onDestroy()

    def is_active(self):
        return self._active

    def is_input(self):
        return self.__is_input

    def get_param(self, key: str, default=None):
        return self.argv.get(key, default)

    def has_flag(self, name: str):
        return self.argv.has_flag(name)
