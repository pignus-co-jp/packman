from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Callable, TypedDict
import sys
import time
import signal
import shlex
from .. import log
import os


class CLIArgsError(Exception):
    """CLI引数パース時のエラー"""
    pass


class CLIArgs:
    """
    軽量CLIパーサー

    対応形式:
    - フラグ: --flag, -f
    - オプション: --key=value, --key value, -k value
    - 位置引数: positional args

    使用例:
        args = CLIArgs(sys.argv)
        if args.has_flag("verbose"):
            print("Verbose mode")
        port = args.get("port", default=8080)
        filename = args.get_positional(0, default="config.yml")
    """

    def __init__(
        self,
        argv: Optional[List[str]] = None,
        allow_single_dash: bool = True
    ):
        """
        Args:
            argv: コマンドライン引数（Noneの場合はsys.argvを使用）
            allow_single_dash: -f形式の短縮オプションを許可するか
        """
        if argv is None:
            argv = sys.argv

        self.flags: set = set()
        self.options: Dict[str, str] = {}
        self.positionals: List[str] = []
        self._raw_argv = argv
        self._allow_single_dash = allow_single_dash

        self._parse(argv[1:])  # プログラム名を除く

    @staticmethod
    def _looks_like_value(s: str) -> bool:
        """
        文字列が値（オプションの引数）として解釈すべきかを判定する。
        負の数値（例: -1, -3.14）はフラグではなく値として扱う。

        Args:
            s: 判定する文字列

        Returns:
            値として解釈すべき場合True
        """
        try:
            float(s)
            return True
        except ValueError:
            return not s.startswith("-")

    def _parse(self, args: List[str]) -> None:
        """
        引数をパース

        Args:
            args: パースする引数リスト
        """
        i = 0
        while i < len(args):
            arg = args[i]

            # -- で始まる場合（長形式オプション）
            if arg.startswith("--"):
                if arg == "--":
                    # -- 以降は全て位置引数として扱う
                    self.positionals.extend(args[i+1:])
                    break

                # --key=value 形式
                if "=" in arg:
                    key, value = arg[2:].split("=", 1)
                    if not key:
                        raise CLIArgsError(f"Invalid option format: {arg}")
                    self.options[key] = value
                else:
                    # --key value 形式 or --flag
                    key = arg[2:]
                    if not key:
                        raise CLIArgsError(f"Invalid option format: {arg}")

                    # 次の引数が値かチェック（負の数値も値として扱う）
                    if i + 1 < len(args) and self._looks_like_value(args[i + 1]):
                        self.options[key] = args[i + 1]
                        i += 1
                    else:
                        # 値がない場合はフラグとして扱う
                        self.flags.add(key)

            # - で始まる場合（短形式オプション）
            elif arg.startswith("-") and self._allow_single_dash and len(arg) > 1:
                # -abc を -a -b -c として扱う
                for char in arg[1:]:
                    self.flags.add(char)

            # 位置引数
            else:
                self.positionals.append(arg)

            i += 1

    def has_flag(self, *names: str) -> bool:
        """
        フラグが指定されているかチェック

        Args:
            *names: チェックするフラグ名（複数指定可能）

        Returns:
            いずれかのフラグが存在する場合True

        Examples:
            args.has_flag("verbose")
            args.has_flag("v", "verbose")  # -v or --verbose
        """
        return any(name in self.flags for name in names)

    def get(self, *keys: str, default: Any = None, required: bool = False) -> Any:
        """
        オプション値を取得

        Args:
            *keys: チェックするキー名（複数指定可能）
            default: デフォルト値
            required: 必須オプションの場合True

        Returns:
            オプション値

        Raises:
            CLIArgsError: required=Trueで値が見つからない場合

        Examples:
            port = args.get("port", default=8080)
            port = args.get("p", "port", default=8080)  # -p or --port
            config = args.get("config", required=True)
        """
        for key in keys:
            if key in self.options:
                return self.options[key]

        if required:
            raise CLIArgsError(f"Required option not found: {keys[0]}")

        return default

    def get_int(self, *keys: str, default: Optional[int] = None, required: bool = False) -> Optional[int]:
        """整数値として取得"""
        value = self.get(*keys, default=default, required=required)
        if value is None:
            return None
        try:
            return int(value)
        except ValueError:
            raise CLIArgsError(
                f"Option {keys[0]} must be an integer, got: {value}")

    def get_float(self, *keys: str, default: Optional[float] = None, required: bool = False) -> Optional[float]:
        """浮動小数点数として取得"""
        value = self.get(*keys, default=default, required=required)
        if value is None:
            return None
        try:
            return float(value)
        except ValueError:
            raise CLIArgsError(
                f"Option {keys[0]} must be a float, got: {value}")

    def get_bool(self, *keys: str, default: bool = False) -> bool:
        """ブール値として取得（yes/no, true/false, 1/0）"""
        value = self.get(*keys, default=None)
        if value is None:
            return default

        value_lower = value.lower()
        if value_lower in ("yes", "true", "1", "on"):
            return True
        elif value_lower in ("no", "false", "0", "off"):
            return False
        else:
            raise CLIArgsError(
                f"Option {keys[0]} must be a boolean, got: {value}")

    def get_positional(self, index: int, default: Any = None, required: bool = False) -> Any:
        """
        位置引数を取得

        Args:
            index: インデックス（0始まり）
            default: デフォルト値
            required: 必須の場合True

        Returns:
            位置引数の値

        Raises:
            CLIArgsError: required=Trueで値が見つからない場合
        """
        if index < len(self.positionals):
            return self.positionals[index]

        if required:
            raise CLIArgsError(
                f"Required positional argument at index {index} not found")

        return default

    def get_all_positionals(self) -> List[str]:
        """全ての位置引数を取得"""
        return self.positionals.copy()

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式で取得"""
        return {
            "flags": list(self.flags),
            "options": self.options.copy(),
            "positionals": self.positionals.copy(),
        }

    def __repr__(self) -> str:
        return f"CLIArgs(flags={self.flags}, options={self.options}, positionals={self.positionals})"


class ConsoleError(Exception):
    """コンソール操作時のエラー"""
    pass


# __commands の値の型を明確に定義
class CommandInfo(TypedDict):
    handler: Callable
    description: str


class WorkSpace(ABC):
    def __init__(self, id: str):
        super().__init__()
        self.id = id
        self.__is_destroy = False
        self.__system_abort_callback: Optional[Callable] = None

    @abstractmethod
    def _onDestroy(self) -> None:
        """コンソール終了時の後処理（サブクラスで実装）"""
        pass

    @abstractmethod
    def _on_input_string(self, raw_input: str) -> Optional["WorkSpace"]:
        pass

    @abstractmethod
    def _on_initialize(self) -> None:
        pass

    def initialize(self) -> None:
        self._on_initialize()

    def handle_input_string(self, raw_input: str) -> Optional["WorkSpace"]:
        return self._on_input_string(raw_input=raw_input)

    def destroy(self) -> None:
        if self.__is_destroy is True:
            return
        self.__is_destroy = True
        self._onDestroy()

    def is_destroy(self) -> bool:
        return self.__is_destroy

    def system_abort(self):
        if not self.is_destroy():
            self.destroy()
            if self.__system_abort_callback:
                self.__system_abort_callback()

    def set_abort_callback(self, system_abort_callback: Callable):
        self.__system_abort_callback = system_abort_callback


class PPConsole(ABC):
    """
    対話型コンソールの基底クラス

    使用方法:
        class MyConsole(PPConsole):
            def _on_input_string(self, raw_input: str):
                print(f"You entered: {raw_input}")

            def _onDestroy(self):
                print("Cleanup...")

        console = MyConsole()
        console.wait_forever()
    """

    def __init__(
        self,
        argv: Optional[List[str]] = None,
        console_flag: str = "console",
        exit_keyword: str = "ppexit",
        prompt: str = "> ",
    ):
        """
        Args:
            argv: コマンドライン引数（Noneの場合はsys.argv）
            console_flag: コンソールモードを有効にするフラグ名
            exit_keyword: コンソール終了キーワード
            prompt: 入力プロンプト
        """
        self.argv = CLIArgs(argv)

        self.prompt = prompt
        self.__exit_keyword = exit_keyword

        self.__workspace: Optional[WorkSpace] = None

        self.__is_console_mode = self.argv.has_flag(console_flag)
        self.__is_active = True
        self.__is_destroy = False
        self.__commands: Dict[str, Callable] = {}
        self._on_setup_signal_handlers()

        log.i(
            f"Console initialized (mode: {'interactive' if self.__is_console_mode else 'daemon'})")

    def _on_setup_signal_handlers(self) -> None:
        """シグナルハンドラーを設定"""
        def signal_handler(signum, frame):
            log.i(f"Received signal {signum}")
            self.destroy()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _on_input_string(self, raw_input: str) -> None:
        """
        入力文字列を処理する（サブクラスで実装）

        Args:
            raw_input: ユーザー入力文字列
        """
        pass

    @abstractmethod
    def _onDestroy(self) -> None:
        """コンソール終了時の後処理（サブクラスで実装）"""
        pass

    @abstractmethod
    def _on_startup(self) -> Optional[WorkSpace]:
        """起動時の処理（オプション）"""
        pass

    def register_command(self, name: str, handler: Callable[[List[str]], None], description: str = "") -> None:
        """
        コマンドを登録

        Args:
            name: コマンド名
            handler: コマンドハンドラー（引数リストを受け取る）
            description: コマンドの説明
        """
        self.__commands[name] = CommandInfo(
            handler=handler,
            description=description,
        )
        log.d(f"Registered command: {name}")

    def _process_command(self, raw_input: str) -> bool:
        """
        登録されたコマンドを処理

        Args:
            raw_input: 入力文字列

        Returns:
            コマンドが処理された場合True
        """
        if not raw_input.strip():
            return False

        # シェル風に引数をパース
        try:
            parts = shlex.split(raw_input)
        except ValueError:
            log.w(f"Failed to parse command: {raw_input}")
            return False

        if not parts:
            return False

        command_name = parts[0]
        args = parts[1:]

        if command_name in self.__commands:
            try:
                self.__commands[command_name]["handler"](args)
                return True
            except Exception as e:
                log.e(f"Command '{command_name}' failed: {e}")
                return True

        return False

    def wait_forever(self) -> None:
        """
        メインループを実行

        コンソールモードの場合は対話的に入力を受け付け、
        そうでない場合はデーモンモードで待機
        """

        def _stoploop():
            self.__is_active = False
            pass
        self.register_command(
            self.__exit_keyword,
            lambda args: _stoploop(),
            "Exit the console"
        )

        self.__workspace = self._on_startup()
        try:
            if self.__workspace:
                self.__workspace.set_abort_callback(self.abort)
                self.__workspace.initialize()
        except Exception as ex:
            log.e(ex)

        try:
            while self.__is_active:
                if self.__is_console_mode:
                    try:
                        raw_input = input(self.prompt)

                        if self.__workspace:
                            if self.__workspace.is_destroy():
                                break

                        # 空行はスキップ
                        if not raw_input.strip():
                            continue

                        # 登録されたコマンドを試す
                        if self._process_command(raw_input):
                            continue

                        # カスタム処理
                        if self.__workspace:
                            ws = self.__workspace.handle_input_string(
                                raw_input=raw_input)
                            if ws:
                                ws.set_abort_callback(self.abort)
                                if ws.id != self.__workspace.id:
                                    self.__workspace.destroy()
                                    self.__workspace = ws
                                    try:
                                        self.__workspace.initialize()
                                    except Exception as ex:
                                        log.e(ex)
                        else:
                            self._on_input_string(raw_input)

                    except EOFError:
                        log.i("EOF received")
                        break
                    except Exception as ex:
                        log.e(f"Console error: {ex}", exc_info=True)
                else:
                    # デーモンモード
                    print(".", end="", flush=True)
                    if self.__workspace:
                        if self.__workspace.is_destroy():
                            break
                    time.sleep(.5)

        except KeyboardInterrupt:
            log.i("Keyboard interrupt received")
        finally:
            log.i("Console loop ended")
        self.destroy()

    def destroy(self) -> None:
        log.i("[PPConsole]", "Request", "destroy")
        if self.__is_destroy is True:
            return

        self.__is_destroy = True

        log.i("[PPConsole]", "Start", "destroy")

        try:
            if self.__workspace:
                self.__workspace.destroy()
                self.__workspace = None
        except Exception as ex:
            log.e(ex)

        """コンソールを終了"""
        try:
            self._onDestroy()
        except Exception as e:
            log.e(f"Error during cleanup: {e}", exc_info=True)

        log.i("[PPConsole]", "End", "destroy")
        pass

    def is_active(self) -> bool:
        """アクティブ状態を取得"""
        return self.__is_active

    def is_console_mode(self) -> bool:
        """コンソールモードかどうか"""
        return self.__is_console_mode

    def get_param(self, *keys: str, default: Any = None, required: bool = False) -> Any:
        """
        コマンドライン引数から値を取得

        Args:
            *keys: 取得するキー（複数指定可能）
            default: デフォルト値
            required: 必須の場合True

        Returns:
            パラメータ値
        """
        return self.argv.get(*keys, default=default, required=required)

    def get_param_int(self, *keys: str, default: Optional[int] = None, required: bool = False) -> Optional[int]:
        """整数パラメータを取得"""
        return self.argv.get_int(*keys, default=default, required=required)

    def get_param_bool(self, *keys: str, default: bool = False) -> bool:
        """ブールパラメータを取得"""
        return self.argv.get_bool(*keys, default=default)

    def has_flag(self, *names: str) -> bool:
        """
        フラグの存在チェック

        Args:
            *names: チェックするフラグ名（複数指定可能）

        Returns:
            いずれかのフラグが存在する場合True
        """
        return self.argv.has_flag(*names)

    def print_help(self) -> None:
        """ヘルプメッセージを表示"""
        print("Available commands:")
        for name, info in sorted(self.__commands.items()):
            desc = info["description"] or "No description"
            print(f"  {name:20s} {desc}")
        print(f"\nType '{self.exit_keyword}' to exit")

    # 組み込みコマンドのデフォルト実装
    def _setup_builtin_commands(self) -> None:
        """組み込みコマンドを登録"""
        self.register_command(
            "help",
            lambda args: self.print_help(),
            "Show this help message"
        )

        self.register_command(
            "status",
            lambda args: print(
                f"Active: {self.__is_active}, Mode: {'console' if self.__is_console_mode else 'daemon'}"),
            "Show console status"
        )

    def abort(self):
        self.destroy()

        my_pid = os.getpid()

        # 自身に向けてシグナルを送信
        print("自分自身に os.kill で送信します...")
        os.kill(my_pid, signal.SIGINT)
