# cloudstorage/iclient.py (or base.py)

from abc import ABC, abstractmethod
from typing import List, Optional, Callable


class IStorageClient(ABC):
    """Unified interface for cloud object storage providers."""

    # --- 単一ファイル操作 ---

    @abstractmethod
    def upload(
        self,
        local_path: str,
        remote_path: str,
        callback: Optional[Callable] = None
    ) -> None:
        """
        ファイルをストレージにアップロード

        Args:
            local_path: ローカルファイルパス
            remote_path: リモートパス
            callback: 進捗コールバック関数

        Raises:
            FileNotFoundError: ローカルファイルが存在しない
            IOError: アップロードに失敗
        """
        pass

    @abstractmethod
    def download(
        self,
        remote_path: str,
        local_path: str,
        callback: Optional[Callable] = None
    ) -> None:
        """
        ストレージからファイルをダウンロード

        Args:
            remote_path: リモートパス
            local_path: ローカル保存先パス
            callback: 進捗コールバック関数

        Raises:
            FileNotFoundError: リモートファイルが存在しない
            IOError: ダウンロードに失敗
        """
        pass

    @abstractmethod
    def read_text(self, remote_path: str, encoding: str = "utf-8") -> str:
        """
        テキストファイルの内容を読み込み

        Args:
            remote_path: リモートパス
            encoding: 文字エンコーディング

        Returns:
            ファイルの内容

        Raises:
            FileNotFoundError: ファイルが存在しない
            IOError: 読み込みに失敗
        """
        pass

    @abstractmethod
    def write_text(
        self,
        remote_path: str,
        text: str,
        encoding: str = "utf-8"
    ) -> None:
        """
        テキストをストレージに書き込み

        Args:
            remote_path: リモートパス
            text: 書き込むテキスト
            encoding: 文字エンコーディング

        Raises:
            IOError: 書き込みに失敗
        """
        pass

    @abstractmethod
    def list(self, prefix: str = "", max_keys: Optional[int] = None) -> List[str]:
        """
        オブジェクトの一覧を取得

        Args:
            prefix: プレフィックス（フォルダパス）
            max_keys: 最大取得件数（Noneの場合は全件）

        Returns:
            オブジェクトキーのリスト

        Raises:
            IOError: 一覧取得に失敗
        """
        pass

    @abstractmethod
    def delete(self, remote_path: str, ignore_missing: bool = False) -> None:
        """
        オブジェクトを削除

        Args:
            remote_path: リモートパス
            ignore_missing: 存在しないファイルを無視するか

        Raises:
            IOError: 削除に失敗
        """
        pass

    @abstractmethod
    def exists(self, remote_path: str) -> bool:
        """
        オブジェクトの存在確認

        Args:
            remote_path: リモートパス

        Returns:
            存在する場合True

        Raises:
            IOError: 確認に失敗（404以外のエラー）
        """
        pass

    # --- フォルダ操作 ---

    @abstractmethod
    def upload_folder(
        self,
        local_folder: str,
        remote_prefix: str,
        parallel: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> None:
        """
        フォルダをストレージにアップロード

        Args:
            local_folder: ローカルフォルダパス
            remote_prefix: リモートプレフィックス
            parallel: 並列アップロードを使用するか
            progress_callback: 進捗コールバック (完了数, 総数)

        Raises:
            NotADirectoryError: 指定パスがディレクトリでない
            IOError: アップロードに失敗
        """
        pass

    @abstractmethod
    def download_folder(
        self,
        remote_prefix: str,
        local_folder: str,
        parallel: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> None:
        """
        ストレージからフォルダをダウンロード

        Args:
            remote_prefix: リモートプレフィックス
            local_folder: ローカル保存先フォルダ
            parallel: 並列ダウンロードを使用するか
            progress_callback: 進捗コールバック (完了数, 総数)

        Raises:
            IOError: ダウンロードに失敗
        """
        pass

    # --- 追加メソッド ---

    @abstractmethod
    def get_file_size(self, remote_path: str) -> int:
        """
        ファイルサイズを取得

        Args:
            remote_path: リモートパス

        Returns:
            ファイルサイズ（バイト単位）

        Raises:
            FileNotFoundError: ファイルが存在しない
            IOError: 取得に失敗
        """
        pass

    @abstractmethod
    def delete_folder(self, remote_prefix: str) -> int:
        """
        フォルダ（プレフィックス）配下のオブジェクトを全削除

        Args:
            remote_prefix: リモートプレフィックス

        Returns:
            削除したオブジェクト数

        Raises:
            IOError: 削除に失敗
        """
        pass
