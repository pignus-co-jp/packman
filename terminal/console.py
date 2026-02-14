from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Callable
import sys
import time
import signal
import shlex
from .. import log


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

                    # 次の引数が値かチェック
                    if i + 1 < len(args) and not args[i + 1].startswith("-"):
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
        self.exit_keyword = exit_keyword

        self.__is_console_mode = self.argv.has_flag(console_flag)
        self.__is_active = True
        self.__commands: Dict[str, Callable] = {}
        self._setup_signal_handlers()

        log.i(
            f"Console initialized (mode: {'interactive' if self.__is_console_mode else 'daemon'})")

    def _setup_signal_handlers(self) -> None:
        """シグナルハンドラーを設定"""
        def signal_handler(signum, frame):
            log.i(f"Received signal {signum}")
            self.destroy()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    @abstractmethod
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

    def _on_startup(self) -> None:
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
        self.__commands[name] = {
            "handler": handler,
            "description": description,
        }
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

        self.register_command(
            "ppexit",
            lambda args: self.destroy(),
            "Exit the console"
        )

        self._on_startup()

        try:
            while self.__is_active:
                if self.__is_console_mode:
                    try:
                        raw_input = input(self.prompt)

                        # 空行はスキップ
                        if not raw_input.strip():
                            continue

                        # 登録されたコマンドを試す
                        if self._process_command(raw_input):
                            continue

                        # カスタム処理
                        self._on_input_string(raw_input)

                    except EOFError:
                        log.i("EOF received")
                        self.destroy()
                        break
                    except Exception as ex:
                        log.e(f"Console error: {ex}", exc_info=True)
                else:
                    # デーモンモード
                    print(".", end="", flush=True)
                    time.sleep(5)

        except KeyboardInterrupt:
            log.i("Keyboard interrupt received")
            self.destroy()
        finally:
            log.i("Console loop ended")

    def destroy(self) -> None:
        """コンソールを終了"""
        if not self.__is_active:
            return

        log.i("Destroying console...")
        self.__is_active = False

        try:
            self._onDestroy()
        except Exception as e:
            log.e(f"Error during cleanup: {e}", exc_info=True)

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
