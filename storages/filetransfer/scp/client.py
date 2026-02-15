from typing import Optional, List, Tuple  # Tupleをインポート
import paramiko
from scp import SCPClient
from pathlib import PurePosixPath
import shlex
from contextlib import contextmanager
from . import dto


class SCPCurrentDirectory:
    def __init__(self, start: str = "/"):
        self._cwd = PurePosixPath(start)

    def cwd(self) -> PurePosixPath:
        return self._cwd

    def cd(self, path: str) -> PurePosixPath:
        new_path = self.resolve(path)
        self._cwd = new_path
        return self._cwd

    def resolve(self, path: str) -> PurePosixPath:
        p = PurePosixPath(path)
        if p.is_absolute():
            return p
        return self._cwd / p


class SCPConnectionError(Exception):
    """SCP接続関連のエラー"""
    pass


class SCPOperationError(Exception):
    """SCP操作関連のエラー"""
    pass


class ScpTransferClient:
    def __init__(
        self,
        host: str,
        user: str,
        password: Optional[str] = None,
        key_path: Optional[str] = None,
        timeout: int = 10,
        port: int = 22,
        known_hosts_file: Optional[str] = None,
    ):
        self.host = host
        self.user = user
        self.port = port
        self.password = password
        self.key_path = key_path
        self.timeout = timeout
        self.known_hosts_file = known_hosts_file
        self._rcwd: Optional[SCPCurrentDirectory] = None
        self._ssh: Optional[paramiko.SSHClient] = None
        self._scp: Optional[SCPClient] = None

    @contextmanager
    def _get_connection(self):
        """接続を取得するコンテキストマネージャー"""
        ssh = paramiko.SSHClient()
        scp = None

        # ホストキーポリシーの設定
        if self.known_hosts_file:
            ssh.load_host_keys(self.known_hosts_file)
            ssh.set_missing_host_key_policy(paramiko.RejectPolicy())
        else:
            # 警告: 本番環境では known_hosts_file を使用すべき
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # 接続
            connect_kwargs = {
                "hostname": self.host,
                "port": self.port,
                "username": self.user,
                "timeout": self.timeout,
            }

            if self.key_path:
                connect_kwargs["key_filename"] = self.key_path
            else:
                connect_kwargs["password"] = self.password

            ssh.connect(**connect_kwargs)
            scp = SCPClient(ssh.get_transport())

            yield ssh, scp

        except paramiko.AuthenticationException as e:
            raise SCPConnectionError(f"認証エラー: {e}")
        except paramiko.SSHException as e:
            raise SCPConnectionError(f"SSH接続エラー: {e}")
        except Exception as e:
            raise SCPConnectionError(f"接続エラー: {e}")
        finally:
            if scp:
                scp.close()
            if ssh:
                ssh.close()

    def _execute_command(self, ssh: paramiko.SSHClient, command: str) -> Tuple[str, str, int]:
        """
        SSHコマンドを実行し、結果を返す

        Returns:
            (stdout, stderr, exit_code)
        """
        stdin, stdout, stderr = ssh.exec_command(command)
        exit_code = stdout.channel.recv_exit_status()
        stdout_str = stdout.read().decode().strip()
        stderr_str = stderr.read().decode().strip()
        return stdout_str, stderr_str, exit_code

    def _safe_path(self, path: str) -> str:
        """パスを安全にクォートする（コマンドインジェクション対策）"""
        return shlex.quote(path)

    def initialize(self) -> Optional[str]:
        """SSH の pwd を使ってリモート側のカレントディレクトリを初期化"""
        with self._get_connection() as (ssh, _):
            stdout, stderr, exit_code = self._execute_command(ssh, "pwd")

            if exit_code != 0 or not stdout:
                raise SCPOperationError(f"pwd コマンド失敗: {stderr}")

            self._rcwd = SCPCurrentDirectory(stdout)
            return str(self._rcwd.cwd())

    def _ensure_initialized(self) -> None:
        """初期化済みかチェック"""
        if self._rcwd is None:
            raise RuntimeError("initialize() を先に呼び出してください")

    def upload(self, local_path: str, remote_path: str) -> None:
        """
        ファイルをアップロード

        Args:
            local_path: ローカルファイルパス
            remote_path: リモートファイルパス
        """
        self._ensure_initialized()

        if self.exists(remote_path):
            return

        remote_abs = self._rcwd.resolve(remote_path).as_posix()

        with self._get_connection() as (ssh, scp):
            try:
                scp.put(local_path, remote_abs)
            except Exception as e:
                raise SCPOperationError(f"アップロード失敗: {e}")

    def upload_dir(self, local_dir: str, remote_dir: str) -> None:
        """
        ディレクトリを再帰的にアップロード

        Args:
            local_dir: ローカルディレクトリパス
            remote_dir: リモートディレクトリパス
        """
        self._ensure_initialized()

        if self.exists(remote_dir):
            return

        remote_abs = self._rcwd.resolve(remote_dir).as_posix()

        with self._get_connection() as (ssh, scp):
            try:
                scp.put(local_dir, remote_abs, recursive=True)
            except Exception as e:
                raise SCPOperationError(f"ディレクトリアップロード失敗: {e}")

    def download(self, remote_path: str, local_path: str, is_recursive: bool = False) -> None:
        """
        ファイルまたはディレクトリをダウンロード

        Args:
            remote_path: リモートパス
            local_path: ローカルパス
            is_recursive: 再帰的にダウンロードするか
        """
        self._ensure_initialized()

        remote_abs = self._rcwd.resolve(remote_path).as_posix()

        with self._get_connection() as (ssh, scp):
            try:
                scp.get(remote_abs, local_path, recursive=is_recursive)
            except Exception as e:
                raise SCPOperationError(f"ダウンロード失敗: {e}")

    def cd(self, path: str) -> str:
        """
        リモートカレントディレクトリを変更

        Args:
            path: 移動先パス

        Returns:
            新しいカレントディレクトリ
        """
        self._ensure_initialized()

        new_path = self._rcwd.resolve(path).as_posix()

        with self._get_connection() as (ssh, _):
            cmd = f"test -d {self._safe_path(new_path)}"
            _, stderr, exit_code = self._execute_command(ssh, cmd)

            if exit_code != 0:
                raise NotADirectoryError(
                    f"リモートディレクトリが見つかりません: {new_path}"
                )

        return str(self._rcwd.cd(path))

    def exists(self, remote_path: str) -> bool:
        """
        リモートパスが存在するかチェック

        Args:
            remote_path: チェックするパス

        Returns:
            存在する場合True
        """
        self._ensure_initialized()

        target = self._rcwd.resolve(remote_path).as_posix()

        with self._get_connection() as (ssh, _):
            cmd = f"test -e {self._safe_path(target)}"
            _, _, exit_code = self._execute_command(ssh, cmd)
            return exit_code == 0

    def rename(self, old_path: str, new_path: str) -> bool:
        """
        リモートファイル/ディレクトリをリネーム

        Args:
            old_path: 元のパス
            new_path: 新しいパス
            overwrite: 上書きを許可するか

        Returns:
            成功した場合True
        """
        self._ensure_initialized()

        if self.exists(new_path):
            return False

        old_abs = self._rcwd.resolve(old_path).as_posix()
        new_abs = self._rcwd.resolve(new_path).as_posix()

        with self._get_connection() as (ssh, _):
            cmd = f"mv {self._safe_path(old_abs)} {self._safe_path(new_abs)}"
            _, stderr, exit_code = self._execute_command(ssh, cmd)

            if exit_code != 0:
                raise SCPOperationError(f"リネーム失敗: {stderr}")

            return True

    def list_entries(self, path: str = ".") -> List[dto.RemoteEntry]:
        """
        ディレクトリ内のエントリ一覧を取得（改善版）

        Args:
            path: リストするディレクトリパス

        Returns:
            RemoteEntryのリスト
        """
        self._ensure_initialized()

        target = self._rcwd.resolve(path).as_posix()

        with self._get_connection() as (ssh, _):
            # ls -la を使用して一度に情報を取得
            # -la: 全ファイル、詳細情報
            # -1: 1行に1ファイル
            cmd = f"ls -la {self._safe_path(target)}"
            stdout, stderr, exit_code = self._execute_command(ssh, cmd)

            if exit_code != 0:
                raise SCPOperationError(f"ls コマンド失敗: {stderr}")

            entries: List[dto.RemoteEntry] = []
            lines = stdout.splitlines()

            # 最初の行（"total ..."）をスキップ
            for line in lines[1:]:
                if not line:
                    continue

                parts = line.split(None, 8)  # 最大9個に分割
                if len(parts) < 9:
                    continue

                permissions = parts[0]
                name = parts[8]

                # ディレクトリ判定（パーミッション文字列の最初の文字が'd'）
                is_dir = permissions.startswith('d')

                full_path = PurePosixPath(target) / name

                entries.append(
                    dto.RemoteEntry(
                        name=name,
                        path=full_path.as_posix(),
                        is_dir=is_dir,
                    )
                )

            return entries

    def mkdir(self, path: str, parents: bool = False, exist_ok: bool = False) -> bool:
        """
        リモートにディレクトリを作成

        Args:
            path: 作成するディレクトリパス
            parents: 親ディレクトリも作成するか
            exist_ok: 既存の場合エラーにしない

        Returns:
            成功した場合True
        """
        self._ensure_initialized()

        target = self._rcwd.resolve(path).as_posix()

        with self._get_connection() as (ssh, _):
            cmd_parts = ["mkdir"]
            if parents:
                cmd_parts.append("-p")
            cmd_parts.append(self._safe_path(target))

            cmd = " ".join(cmd_parts)
            _, stderr, exit_code = self._execute_command(ssh, cmd)

            if exit_code != 0:
                if exist_ok and "File exists" in stderr:
                    return True
                raise SCPOperationError(f"ディレクトリ作成失敗: {stderr}")

            return True

    def __enter__(self):
        """コンテキストマネージャーのサポート"""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャーのクリーンアップ"""
        # 必要に応じてクリーンアップ処理を追加
        pass
