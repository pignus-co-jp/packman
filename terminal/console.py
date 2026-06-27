"""
PPConsole - 対話型コンソールフレームワーク

構成:
  CLIArgs    - コマンドライン引数パーサー
  WorkSpace  - コンソール内の状態単位（切り替え可能）
  PPConsole  - メインループを持つ対話型コンソール基底クラス
"""

from __future__ import annotations

import os
import shlex
import signal
import sys
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, TypedDict

from .. import log


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class CLIArgsError(Exception):
    """CLIArgs のパース・取得エラー"""


class ConsoleError(Exception):
    """PPConsole の操作エラー"""


# ---------------------------------------------------------------------------
# CLIArgs
# ---------------------------------------------------------------------------

class CLIArgs:
    """
    軽量コマンドライン引数パーサー。

    対応形式:
      - フラグ    : --verbose / -v
      - オプション: --port=8080 / --port 8080 / -p 8080
      - 位置引数  : positional args
      - セパレータ: -- 以降を全て位置引数として扱う

    Examples:
        args = CLIArgs(sys.argv)
        args.has_flag("verbose")          # --verbose / -v
        args.get("port", default=8080)    # --port 8080
        args.get_positional(0)            # 最初の位置引数
    """

    def __init__(
        self,
        argv: Optional[List[str]] = None,
        allow_single_dash: bool = True,
    ) -> None:
        """
        Args:
            argv: コマンドライン引数。None の場合は sys.argv を使用。
            allow_single_dash: -abc を -a -b -c に展開するか。
        """
        if argv is None:
            argv = sys.argv

        self.flags: set = set()
        self.options: Dict[str, str] = {}
        self.positionals: List[str] = []
        self._raw_argv = argv
        self._allow_single_dash = allow_single_dash

        self._parse(argv[1:])  # argv[0] はプログラム名なので除外

    # ------------------------------------------------------------------
    # Internal parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _looks_like_value(s: str) -> bool:
        """
        文字列が値（オプションの引数）として解釈すべきかを判定する。
        負の数値（例: -1, -3.14）はフラグではなく値として扱う。
        """
        try:
            float(s)
            return True
        except ValueError:
            return not s.startswith("-")

    def _parse(self, args: List[str]) -> None:
        i = 0
        while i < len(args):
            token = args[i]

            if token == "--":
                # -- 以降は全て位置引数
                self.positionals.extend(args[i + 1:])
                break

            if token.startswith("--"):
                i = self._parse_long(args, i)

            elif token.startswith("-") and self._allow_single_dash and len(token) > 1:
                # -abc → flags: {a, b, c}
                for ch in token[1:]:
                    self.flags.add(ch)

            else:
                self.positionals.append(token)

            i += 1

    def _parse_long(self, args: List[str], i: int) -> int:
        """長形式オプションをパースし、次に処理すべきインデックスを返す。"""
        token = args[i]
        body = token[2:]  # "--" を除いた部分

        if not body:
            raise CLIArgsError(f"Invalid option: '{token}'")

        if "=" in body:
            key, value = body.split("=", 1)
            if not key:
                raise CLIArgsError(f"Invalid option: '{token}'")
            self.options[key] = value
            return i

        key = body
        # 次のトークンが値かチェック（負の数値も値として扱う）
        if i + 1 < len(args) and self._looks_like_value(args[i + 1]):
            self.options[key] = args[i + 1]
            return i + 1

        self.flags.add(key)
        return i

    # ------------------------------------------------------------------
    # Public accessors
    # ------------------------------------------------------------------

    def has_flag(self, *names: str) -> bool:
        """
        いずれかのフラグが指定されているか確認する。

        Examples:
            args.has_flag("v", "verbose")   # -v or --verbose
        """
        return any(name in self.flags for name in names)

    def get(self, *keys: str, default: Any = None, required: bool = False) -> Any:
        """
        オプション値を取得する。

        Args:
            *keys: 検索するキー（エイリアスを複数指定可）。
            default: 見つからない場合の戻り値。
            required: True のとき、見つからなければ CLIArgsError を送出。

        Examples:
            args.get("p", "port", default=8080)
            args.get("config", required=True)
        """
        for key in keys:
            if key in self.options:
                return self.options[key]

        if required:
            raise CLIArgsError(f"Required option missing: {keys[0]!r}")

        return default

    def get_int(self, *keys: str, default: Optional[int] = None, required: bool = False) -> Optional[int]:
        """整数値として取得する。"""
        value = self.get(*keys, default=default, required=required)
        if value is None or isinstance(value, int):
            return value
        try:
            return int(value)
        except (ValueError, TypeError):
            raise CLIArgsError(f"Option {keys[0]!r} must be an integer, got: {value!r}")

    def get_float(self, *keys: str, default: Optional[float] = None, required: bool = False) -> Optional[float]:
        """浮動小数点数として取得する。"""
        value = self.get(*keys, default=default, required=required)
        if value is None or isinstance(value, float):
            return value
        try:
            return float(value)
        except (ValueError, TypeError):
            raise CLIArgsError(f"Option {keys[0]!r} must be a float, got: {value!r}")

    def get_bool(self, *keys: str, default: bool = False) -> bool:
        """
        ブール値として取得する。

        受け付ける文字列: yes/no, true/false, 1/0, on/off (大文字小文字不問)
        """
        _TRUTHY = {"yes", "true", "1", "on"}
        _FALSY  = {"no", "false", "0", "off"}

        value = self.get(*keys, default=None)
        if value is None:
            return default

        lower = str(value).lower()
        if lower in _TRUTHY:
            return True
        if lower in _FALSY:
            return False

        raise CLIArgsError(f"Option {keys[0]!r} must be a boolean, got: {value!r}")

    def get_positional(self, index: int, default: Any = None, required: bool = False) -> Any:
        """
        位置引数を取得する。

        Args:
            index: 0 始まりのインデックス。
            default: 範囲外の場合の戻り値。
            required: True のとき、範囲外なら CLIArgsError を送出。
        """
        if index < len(self.positionals):
            return self.positionals[index]

        if required:
            raise CLIArgsError(f"Required positional argument at index {index} not found")

        return default

    def get_all_positionals(self) -> List[str]:
        """全ての位置引数のコピーを返す。"""
        return list(self.positionals)

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換する（フラグは安定したソート順）。"""
        return {
            "flags": sorted(self.flags),
            "options": dict(self.options),
            "positionals": list(self.positionals),
        }

    def __repr__(self) -> str:
        return (
            f"CLIArgs("
            f"flags={sorted(self.flags)}, "
            f"options={self.options}, "
            f"positionals={self.positionals})"
        )


# ---------------------------------------------------------------------------
# WorkSpace
# ---------------------------------------------------------------------------

class WorkSpace(ABC):
    """
    コンソール内の「状態単位」。

    PPConsole は常に 1 つの WorkSpace を保持し、
    _on_input_string が別の WorkSpace を返すと切り替わる。
    """

    def __init__(self, id: str) -> None:
        self.id = id
        self.__is_destroy = False
        self.__system_abort_callback: Optional[Callable] = None

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def _onDestroy(self) -> None:
        """破棄時のクリーンアップ処理。"""

    @abstractmethod
    def _on_input_string(self, raw_input: str) -> Optional["WorkSpace"]:
        """
        ユーザー入力を処理する。

        Returns:
            切り替え先の WorkSpace、または None（現状維持）。
        """

    @abstractmethod
    def _on_initialize(self) -> None:
        """初期化処理。initialize() から呼ばれる。"""

    # ------------------------------------------------------------------
    # Public lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        self._on_initialize()

    def handle_input_string(self, raw_input: str) -> Optional["WorkSpace"]:
        return self._on_input_string(raw_input=raw_input)

    def destroy(self) -> None:
        if self.__is_destroy:
            return
        self.__is_destroy = True
        self._onDestroy()

    def is_destroy(self) -> bool:
        return self.__is_destroy

    def system_abort(self) -> None:
        """WorkSpace 側から強制終了を要求する。"""
        if not self.is_destroy():
            self.destroy()
        if self.__system_abort_callback:
            self.__system_abort_callback()

    def set_abort_callback(self, system_abort_callback: Callable) -> None:
        self.__system_abort_callback = system_abort_callback


# ---------------------------------------------------------------------------
# PPConsole
# ---------------------------------------------------------------------------

class _CommandEntry(TypedDict):
    handler: Callable
    description: str


class PPConsole(ABC):
    """
    対話型コンソールの基底クラス。

    コンソールモード (--console フラグあり):
        プロンプトを表示してユーザー入力を処理する。

    デーモンモード (--console フラグなし):
        バックグラウンドでループし、WorkSpace の終了を監視する。

    Examples:
        class MyConsole(PPConsole):
            def _on_startup(self) -> Optional[WorkSpace]:
                return MyWorkSpace("main")

            def _onDestroy(self) -> None:
                print("Cleanup")

        MyConsole().wait_forever()
    """

    def __init__(
        self,
        argv: Optional[List[str]] = None,
        console_flag: Optional[str] = "console",
        exit_keyword: Optional[str] = "ppexit",
        prompt: Optional[str] = "> ",
    ) -> None:
        """
        Args:
            argv: コマンドライン引数。None の場合は sys.argv を使用。
            console_flag: コンソールモードを有効にするフラグ名。
            exit_keyword: コンソール終了キーワード。
            prompt: 対話モードの入力プロンプト。
        """
        self.argv = CLIArgs(argv)
        self.prompt = prompt
        self.__exit_keyword = exit_keyword

        self.__workspace: Optional[WorkSpace] = None
        if console_flag:
            self.__is_console_mode = self.argv.has_flag(console_flag)
        else:
            self.__is_console_mode = True
        self.__is_active = True
        self.__is_destroy = False
        self.__commands: Dict[str, _CommandEntry] = {}

        self._on_setup_signal_handlers()
        self._setup_builtin_commands()

        log.i(f"Console initialized (mode: {'interactive' if self.__is_console_mode else 'daemon'})")

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def _on_startup(self) -> Optional[WorkSpace]:
        """
        起動直後に呼ばれる。

        Returns:
            最初の WorkSpace、または None。
        """

    @abstractmethod
    def _onDestroy(self) -> None:
        """終了時のクリーンアップ処理。"""

    # ------------------------------------------------------------------
    # Optional override
    # ------------------------------------------------------------------

    def _on_input_string(self, raw_input: str) -> None:
        """
        WorkSpace が存在しない場合の入力ハンドラ（サブクラスで必要に応じてオーバーライド）。
        """

    # ------------------------------------------------------------------
    # Signal handlers
    # ------------------------------------------------------------------

    def _on_setup_signal_handlers(self) -> None:
        def _handler(signum: int, frame: object) -> None:
            log.i(f"Received signal {signum}")
            self.destroy()
            sys.exit(0)

        signal.signal(signal.SIGINT, _handler)
        signal.signal(signal.SIGTERM, _handler)

    # ------------------------------------------------------------------
    # Command registration
    # ------------------------------------------------------------------

    def register_command(
        self,
        name: str,
        handler: Callable[[List[str]], None],
        description: str = "",
    ) -> None:
        """
        コマンドを登録する。

        Args:
            name: コマンド名。
            handler: コマンドハンドラー (args: List[str]) -> None。
            description: help で表示される説明文。
        """
        self.__commands[name] = _CommandEntry(handler=handler, description=description)
        log.d(f"Registered command: {name!r}")

    def _setup_builtin_commands(self) -> None:
        """組み込みコマンドを登録する。"""
        self.register_command(
            "help",
            lambda args: self.print_help(),
            "Show available commands",
        )
        self.register_command(
            "status",
            lambda args: self._print_status(),
            "Show console status",
        )

    def _process_command(self, raw_input: str) -> bool:
        """
        登録済みコマンドにディスパッチする。

        Returns:
            コマンドが処理された場合 True。
        """
        if not raw_input.strip():
            return False

        try:
            parts = shlex.split(raw_input)
        except ValueError:
            log.w(f"Failed to parse input: {raw_input!r}")
            return False

        if not parts:
            return False

        name, args = parts[0], parts[1:]

        if name not in self.__commands:
            return False

        try:
            self.__commands[name]["handler"](args)
        except Exception as exc:
            log.e(f"Command {name!r} raised an exception: {exc}")

        return True

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def wait_forever(self) -> None:
        """メインループを開始する（ブロッキング）。"""

        def _stop(args: List[str]) -> None:
            self.__is_active = False

        self.register_command(self.__exit_keyword, _stop, "Exit the console")

        self.__workspace = self._on_startup()
        if self.__workspace:
            self.__workspace.set_abort_callback(self.abort)
            try:
                self.__workspace.initialize()
            except Exception as exc:
                log.e(exc)

        try:
            if self.__is_console_mode:
                self._interactive_loop()
            else:
                self._daemon_loop()
        except KeyboardInterrupt:
            log.i("Keyboard interrupt received")
        finally:
            log.i("Console loop ended")

        self.destroy()

    def _interactive_loop(self) -> None:
        while self.__is_active:
            if self.__workspace and self.__workspace.is_destroy():
                break

            try:
                raw_input = input(self.prompt)
            except EOFError:
                log.i("EOF received")
                break
            except Exception as exc:
                log.e(f"Console error: {exc}", exc_info=True)
                continue

            if not raw_input.strip():
                continue

            if self._process_command(raw_input):
                continue

            if self.__workspace:
                self._handle_workspace_input(raw_input)
            else:
                self._on_input_string(raw_input)

    def _daemon_loop(self) -> None:
        while self.__is_active:
            if self.__workspace and self.__workspace.is_destroy():
                break
            time.sleep(0.5)

    def _handle_workspace_input(self, raw_input: str) -> None:
        """WorkSpace に入力を渡し、必要に応じて切り替える。"""
        assert self.__workspace is not None

        try:
            next_ws = self.__workspace.handle_input_string(raw_input=raw_input)
        except Exception as exc:
            log.e(f"WorkSpace input handler failed: {exc}", exc_info=True)
            return

        if next_ws is None or next_ws.id == self.__workspace.id:
            return

        self.__workspace.destroy()
        self.__workspace = next_ws
        self.__workspace.set_abort_callback(self.abort)
        try:
            self.__workspace.initialize()
        except Exception as exc:
            log.e(f"New WorkSpace initialization failed: {exc}", exc_info=True)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def destroy(self) -> None:
        """コンソールを終了する（冪等）。"""
        if self.__is_destroy:
            return
        self.__is_destroy = True
        log.i("[PPConsole] Start destroy")

        if self.__workspace:
            try:
                self.__workspace.destroy()
            except Exception as exc:
                log.e(exc)
            self.__workspace = None

        try:
            self._onDestroy()
        except Exception as exc:
            log.e(f"Error during cleanup: {exc}", exc_info=True)

        log.i("[PPConsole] End destroy")

    def abort(self) -> None:
        """WorkSpace から強制終了が要求されたときに呼ばれる。"""
        self.__is_active = False
        self.destroy()

    # ------------------------------------------------------------------
    # Helpers / accessors
    # ------------------------------------------------------------------

    def print_help(self) -> None:
        """登録済みコマンドの一覧を表示する。"""
        print("Available commands:")
        for name, entry in sorted(self.__commands.items()):
            desc = entry["description"] or "(no description)"
            print(f"  {name:<20} {desc}")
        print(f"\nType '{self.__exit_keyword}' to exit")

    def _print_status(self) -> None:
        mode = "console" if self.__is_console_mode else "daemon"
        ws_id = self.__workspace.id if self.__workspace else "none"
        print(f"active={self.__is_active}, mode={mode}, workspace={ws_id}")

    def is_active(self) -> bool:
        return self.__is_active

    def is_console_mode(self) -> bool:
        return self.__is_console_mode

    def get_param(self, *keys: str, default: Any = None, required: bool = False) -> Any:
        return self.argv.get(*keys, default=default, required=required)

    def get_param_int(self, *keys: str, default: Optional[int] = None, required: bool = False) -> Optional[int]:
        return self.argv.get_int(*keys, default=default, required=required)

    def get_param_bool(self, *keys: str, default: bool = False) -> bool:
        return self.argv.get_bool(*keys, default=default)

    def has_flag(self, *names: str) -> bool:
        return self.argv.has_flag(*names)
