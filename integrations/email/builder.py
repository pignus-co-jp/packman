from typing import List, Optional, Union
from email.message import EmailMessage
from email.utils import formataddr, parseaddr
import mimetypes
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class EmailBuilderError(Exception):
    """メール構築時のエラー"""
    pass


class EmailMessageBuilder:
    """
    EmailMessageを構築するビルダークラス

    使用例:
        builder = EmailMessageBuilder()
        msg = (builder
            .from_addr("sender@example.com", "Sender Name")
            .to_addrs(["recipient@example.com"])
            .subject("Test Email")
            .text("Plain text body")
            .html("<h1>HTML body</h1>")
            .attach("document.pdf")
            .build()
        )
    """

    def __init__(self):
        self._msg = EmailMessage()
        self._msg.set_charset("utf-8")
        self._to_addrs: List[str] = []
        self._cc_addrs: List[str] = []
        self._bcc_addrs: List[str] = []
        self._from_addr: Optional[str] = None
        self._from_name: Optional[str] = None
        self._subject: Optional[str] = None
        self._has_text_content = False
        self._has_html_content = False

    def subject(self, text: str) -> "EmailMessageBuilder":
        """
        件名を設定

        Args:
            text: 件名

        Returns:
            self（メソッドチェーン用）
        """
        if not text:
            raise EmailBuilderError("Subject cannot be empty")
        self._subject = text
        self._msg["Subject"] = text
        return self

    def from_addr(
        self,
        addr: str,
        name: Optional[str] = None
    ) -> "EmailMessageBuilder":
        """
        送信者アドレスを設定

        Args:
            addr: メールアドレス
            name: 送信者名（オプション）

        Returns:
            self（メソッドチェーン用）

        Examples:
            .from_addr("sender@example.com")
            .from_addr("sender@example.com", "John Doe")
        """
        if not self._is_valid_email(addr):
            raise EmailBuilderError(f"Invalid email address: {addr}")

        self._from_addr = addr
        self._from_name = name

        if name:
            self._msg["From"] = formataddr((name, addr))
        else:
            self._msg["From"] = addr

        return self

    def to_addrs(
        self,
        addrs: Union[str, List[str]],
        validate: bool = True
    ) -> "EmailMessageBuilder":
        """
        宛先アドレスを追加

        Args:
            addrs: メールアドレス（文字列またはリスト）
            validate: メールアドレスの妥当性をチェックするか

        Returns:
            self（メソッドチェーン用）
        """
        if isinstance(addrs, str):
            addrs = [addrs]

        if validate:
            for addr in addrs:
                if not self._is_valid_email(addr):
                    raise EmailBuilderError(f"Invalid email address: {addr}")

        self._to_addrs.extend(addrs)
        return self

    def cc_addrs(
        self,
        addrs: Union[str, List[str]],
        validate: bool = True
    ) -> "EmailMessageBuilder":
        """
        CCアドレスを追加

        Args:
            addrs: メールアドレス（文字列またはリスト）
            validate: メールアドレスの妥当性をチェックするか

        Returns:
            self（メソッドチェーン用）
        """
        if isinstance(addrs, str):
            addrs = [addrs]

        if validate:
            for addr in addrs:
                if not self._is_valid_email(addr):
                    raise EmailBuilderError(f"Invalid email address: {addr}")

        self._cc_addrs.extend(addrs)
        return self

    def bcc_addrs(
        self,
        addrs: Union[str, List[str]],
        validate: bool = True
    ) -> "EmailMessageBuilder":
        """
        BCCアドレスを追加

        Args:
            addrs: メールアドレス（文字列またはリスト）
            validate: メールアドレスの妥当性をチェックするか

        Returns:
            self（メソッドチェーン用）
        """
        if isinstance(addrs, str):
            addrs = [addrs]

        if validate:
            for addr in addrs:
                if not self._is_valid_email(addr):
                    raise EmailBuilderError(f"Invalid email address: {addr}")

        self._bcc_addrs.extend(addrs)
        return self

    def reply_to(self, addr: str, name: Optional[str] = None) -> "EmailMessageBuilder":
        """
        Reply-Toヘッダーを設定

        Args:
            addr: メールアドレス
            name: 名前（オプション）

        Returns:
            self（メソッドチェーン用）
        """
        if not self._is_valid_email(addr):
            raise EmailBuilderError(f"Invalid email address: {addr}")

        if name:
            self._msg["Reply-To"] = formataddr((name, addr))
        else:
            self._msg["Reply-To"] = addr

        return self

    def text(self, body: str) -> "EmailMessageBuilder":
        """
        プレーンテキスト本文を設定

        Args:
            body: テキスト本文

        Returns:
            self（メソッドチェーン用）
        """
        if not body:
            logger.warning("Empty text body provided")

        if not self._has_text_content:
            self._msg.set_content(body, subtype="plain", charset="utf-8")
            self._has_text_content = True
        else:
            logger.warning("Text content already set, replacing...")
            # 既存のテキストコンテンツを置き換え
            for part in self._msg.iter_parts():
                if part.get_content_type() == "text/plain":
                    self._msg.set_payload(
                        [p for p in self._msg.iter_parts() if p != part])
                    break
            self._msg.set_content(body, subtype="plain", charset="utf-8")

        return self

    def html(self, html_body: str) -> "EmailMessageBuilder":
        """
        HTML本文を追加（マルチパート）

        Args:
            html_body: HTML本文

        Returns:
            self（メソッドチェーン用）
        """
        if not html_body:
            logger.warning("Empty HTML body provided")

        if not self._has_text_content:
            logger.warning(
                "HTML added without plain text. Consider adding text() first for better compatibility.")

        self._msg.add_alternative(html_body, subtype="html", charset="utf-8")
        self._has_html_content = True
        return self

    def attach(
        self,
        file_path: Union[str, Path],
        filename: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> "EmailMessageBuilder":
        """
        ファイルを添付

        Args:
            file_path: ファイルパス
            filename: 添付ファイル名（省略時はファイル名を使用）
            content_type: MIMEタイプ（省略時は自動判定）

        Returns:
            self（メソッドチェーン用）

        Raises:
            EmailBuilderError: ファイルが存在しない場合
        """
        path = Path(file_path)

        if not path.exists():
            raise EmailBuilderError(f"File not found: {file_path}")

        if not path.is_file():
            raise EmailBuilderError(f"Not a file: {file_path}")

        # ファイル名の決定
        attach_filename = filename or path.name

        # MIMEタイプの決定
        if content_type:
            mime_type = content_type
        else:
            mime_type, _ = mimetypes.guess_type(path)
            mime_type = mime_type or "application/octet-stream"

        # MIMEタイプを分割
        try:
            maintype, subtype = mime_type.split("/", 1)
        except ValueError:
            logger.warning(
                f"Invalid MIME type: {mime_type}, using application/octet-stream")
            maintype, subtype = "application", "octet-stream"

        try:
            with open(path, "rb") as f:
                self._msg.add_attachment(
                    f.read(),
                    maintype=maintype,
                    subtype=subtype,
                    filename=attach_filename
                )
        except Exception as e:
            raise EmailBuilderError(f"Failed to attach file {file_path}: {e}")

        return self

    def attach_bytes(
        self,
        data: bytes,
        filename: str,
        content_type: str = "application/octet-stream"
    ) -> "EmailMessageBuilder":
        """
        バイトデータを添付

        Args:
            data: バイトデータ
            filename: 添付ファイル名
            content_type: MIMEタイプ

        Returns:
            self（メソッドチェーン用）
        """
        try:
            maintype, subtype = content_type.split("/", 1)
        except ValueError:
            logger.warning(
                f"Invalid MIME type: {content_type}, using application/octet-stream")
            maintype, subtype = "application", "octet-stream"

        self._msg.add_attachment(
            data,
            maintype=maintype,
            subtype=subtype,
            filename=filename
        )
        return self

    def header(self, name: str, value: str) -> "EmailMessageBuilder":
        """
        カスタムヘッダーを追加

        Args:
            name: ヘッダー名
            value: ヘッダー値

        Returns:
            self（メソッドチェーン用）
        """
        self._msg[name] = value
        return self

    def priority(self, level: str = "normal") -> "EmailMessageBuilder":
        """
        優先度を設定

        Args:
            level: "high", "normal", "low"

        Returns:
            self（メソッドチェーン用）
        """
        priority_map = {
            "high": ("1", "urgent", "high"),
            "normal": ("3", "normal", "normal"),
            "low": ("5", "non-urgent", "low"),
        }

        if level not in priority_map:
            raise EmailBuilderError(f"Invalid priority level: {level}")

        x_priority, priority, importance = priority_map[level]
        self._msg["X-Priority"] = x_priority
        self._msg["Priority"] = priority
        self._msg["Importance"] = importance

        return self

    def _is_valid_email(self, email: str) -> bool:
        """
        メールアドレスの簡易検証

        Args:
            email: メールアドレス

        Returns:
            有効な場合True
        """
        if not email or "@" not in email:
            return False

        # 基本的な形式チェック
        local, domain = email.rsplit("@", 1)
        if not local or not domain:
            return False

        if "." not in domain:
            return False

        return True

    def _validate(self) -> None:
        """
        メッセージの妥当性を検証

        Raises:
            EmailBuilderError: 必須項目が不足している場合
        """
        if not self._from_addr:
            raise EmailBuilderError("From address is required")

        if not self._to_addrs and not self._cc_addrs and not self._bcc_addrs:
            raise EmailBuilderError(
                "At least one recipient (To, CC, or BCC) is required")

        if not self._subject:
            logger.warning("Email has no subject")

        if not self._has_text_content and not self._has_html_content:
            logger.warning("Email has no content (neither text nor HTML)")

    def build(self) -> EmailMessage:
        """
        EmailMessageオブジェクトを構築

        Returns:
            構築されたEmailMessage

        Raises:
            EmailBuilderError: 必須項目が不足している場合
        """
        # 妥当性検証
        self._validate()

        # 宛先の設定
        if self._to_addrs:
            self._msg["To"] = ", ".join(self._to_addrs)

        if self._cc_addrs:
            self._msg["Cc"] = ", ".join(self._cc_addrs)

        if self._bcc_addrs:
            self._msg["Bcc"] = ", ".join(self._bcc_addrs)

        return self._msg

    def get_all_recipients(self) -> List[str]:
        """
        全ての受信者（To, CC, BCC）のリストを取得

        Returns:
            全受信者のメールアドレスリスト
        """
        return self._to_addrs + self._cc_addrs + self._bcc_addrs

    def reset(self) -> "EmailMessageBuilder":
        """
        ビルダーをリセット（再利用可能に）

        Returns:
            self（メソッドチェーン用）
        """
        self.__init__()
        return self

    # 後方互換性のためのエイリアス
    def to_EmailMessage(self) -> EmailMessage:
        """後方互換性のためのエイリアス（非推奨）"""
        logger.warning("to_EmailMessage() is deprecated, use build() instead")
        return self.build()
