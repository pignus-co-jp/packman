# cloudstorage/s3.py
import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Callable
from .. import iclient


class S3Client(iclient.IStorageClient):
    def __init__(
        self,
        bucket: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region: str,
        max_workers: int = 5
    ):
        self.bucket = bucket
        self.max_workers = max_workers
        
        try:
            self.s3 = boto3.client(
                "s3",
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region,
            )
            # 接続テスト
            self.s3.head_bucket(Bucket=bucket)
        except NoCredentialsError:
            raise ValueError("Invalid AWS credentials")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise ValueError(f"Bucket '{bucket}' does not exist")
            raise

    # --- 単一ファイル ---
    
    def upload(
        self,
        local_path: str,
        remote_path: str,
        callback: Optional[Callable] = None
    ) -> None:
        """
        ファイルをS3にアップロード
        
        Args:
            local_path: ローカルファイルパス
            remote_path: S3上のパス
            callback: 進捗コールバック関数
        """
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Local file not found: {local_path}")
        
        try:
            self.s3.upload_file(
                local_path,
                self.bucket,
                remote_path,
                Callback=callback
            )
        except ClientError as e:
            raise IOError(f"Failed to upload {local_path}: {e}")

    def download(
        self,
        remote_path: str,
        local_path: str,
        callback: Optional[Callable] = None
    ) -> None:
        """
        S3からファイルをダウンロード
        
        Args:
            remote_path: S3上のパス
            local_path: ローカル保存先パス
            callback: 進捗コールバック関数
        """
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            self.s3.download_file(
                self.bucket,
                remote_path,
                local_path,
                Callback=callback
            )
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise FileNotFoundError(f"Remote file not found: {remote_path}")
            raise IOError(f"Failed to download {remote_path}: {e}")

    def read_text(self, remote_path: str, encoding: str = "utf-8") -> str:
        """テキストファイルの内容を読み込み"""
        try:
            obj = self.s3.get_object(Bucket=self.bucket, Key=remote_path)
            return obj["Body"].read().decode(encoding)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(f"Remote file not found: {remote_path}")
            raise IOError(f"Failed to read {remote_path}: {e}")

    def write_text(
        self,
        remote_path: str,
        text: str,
        encoding: str = "utf-8"
    ) -> None:
        """テキストをS3に書き込み"""
        try:
            self.s3.put_object(
                Bucket=self.bucket,
                Key=remote_path,
                Body=text.encode(encoding)
            )
        except ClientError as e:
            raise IOError(f"Failed to write {remote_path}: {e}")

    def list(self, prefix: str = "", max_keys: Optional[int] = None) -> List[str]:
        """
        オブジェクトの一覧を取得（ページネーション対応）
        
        Args:
            prefix: プレフィックス
            max_keys: 最大取得件数（Noneの場合は全件）
        
        Returns:
            キーのリスト
        """
        keys = []
        continuation_token = None
        
        try:
            while True:
                params = {
                    'Bucket': self.bucket,
                    'Prefix': prefix
                }
                
                if continuation_token:
                    params['ContinuationToken'] = continuation_token
                
                if max_keys is not None:
                    remaining = max_keys - len(keys)
                    if remaining <= 0:
                        break
                    params['MaxKeys'] = min(remaining, 1000)
                
                resp = self.s3.list_objects_v2(**params)
                
                if 'Contents' in resp:
                    keys.extend([obj['Key'] for obj in resp['Contents']])
                
                if not resp.get('IsTruncated', False):
                    break
                
                continuation_token = resp.get('NextContinuationToken')
            
            return keys
        except ClientError as e:
            raise IOError(f"Failed to list objects: {e}")

    def delete(self, remote_path: str, ignore_missing: bool = False) -> None:
        """
        オブジェクトを削除
        
        Args:
            remote_path: S3上のパス
            ignore_missing: 存在しないファイルを無視するか
        """
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=remote_path)
        except ClientError as e:
            if not ignore_missing:
                raise IOError(f"Failed to delete {remote_path}: {e}")

    def exists(self, remote_path: str) -> bool:
        """オブジェクトの存在確認"""
        try:
            self.s3.head_object(Bucket=self.bucket, Key=remote_path)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise IOError(f"Failed to check existence of {remote_path}: {e}")

    # --- フォルダ操作 ---
    
    def upload_folder(
        self,
        local_folder: str,
        remote_prefix: str,
        parallel: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> None:
        """
        フォルダをS3にアップロード
        
        Args:
            local_folder: ローカルフォルダパス
            remote_prefix: S3上のプレフィックス
            parallel: 並列アップロードを使用するか
            progress_callback: 進捗コールバック (完了数, 総数)
        """
        if not os.path.isdir(local_folder):
            raise NotADirectoryError(f"Not a directory: {local_folder}")
        
        # アップロード対象のファイル一覧を作成
        files_to_upload = []
        for root, _, files in os.walk(local_folder):
            for file in files:
                local_path = os.path.join(root, file)
                rel_path = os.path.relpath(local_path, local_folder)
                remote_path = f"{remote_prefix.rstrip('/')}/{rel_path.replace(os.sep, '/')}"
                files_to_upload.append((local_path, remote_path))
        
        total = len(files_to_upload)
        if total == 0:
            return
        
        if parallel and total > 1:
            # 並列アップロード
            completed = 0
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self.upload, local_path, remote_path): (local_path, remote_path)
                    for local_path, remote_path in files_to_upload
                }
                
                for future in as_completed(futures):
                    try:
                        future.result()
                        completed += 1
                        if progress_callback:
                            progress_callback(completed, total)
                    except Exception as e:
                        local_path, _ = futures[future]
                        raise IOError(f"Failed to upload {local_path}: {e}")
        else:
            # 逐次アップロード
            for i, (local_path, remote_path) in enumerate(files_to_upload, 1):
                self.upload(local_path, remote_path)
                if progress_callback:
                    progress_callback(i, total)

    def download_folder(
        self,
        remote_prefix: str,
        local_folder: str,
        parallel: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> None:
        """
        S3からフォルダをダウンロード
        
        Args:
            remote_prefix: S3上のプレフィックス
            local_folder: ローカル保存先フォルダ
            parallel: 並列ダウンロードを使用するか
            progress_callback: 進捗コールバック (完了数, 総数)
        """
        keys = self.list(remote_prefix)
        
        if not keys:
            # 空のフォルダを作成
            os.makedirs(local_folder, exist_ok=True)
            return
        
        total = len(keys)
        
        if parallel and total > 1:
            # 並列ダウンロード
            completed = 0
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {}
                for key in keys:
                    rel_path = key[len(remote_prefix):].lstrip("/")
                    local_path = os.path.join(local_folder, rel_path)
                    futures[executor.submit(self.download, key, local_path)] = key
                
                for future in as_completed(futures):
                    try:
                        future.result()
                        completed += 1
                        if progress_callback:
                            progress_callback(completed, total)
                    except Exception as e:
                        key = futures[future]
                        raise IOError(f"Failed to download {key}: {e}")
        else:
            # 逐次ダウンロード
            for i, key in enumerate(keys, 1):
                rel_path = key[len(remote_prefix):].lstrip("/")
                local_path = os.path.join(local_folder, rel_path)
                self.download(key, local_path)
                if progress_callback:
                    progress_callback(i, total)

    def get_file_size(self, remote_path: str) -> int:
        """ファイルサイズを取得（バイト単位）"""
        try:
            resp = self.s3.head_object(Bucket=self.bucket, Key=remote_path)
            return resp['ContentLength']
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise FileNotFoundError(f"Remote file not found: {remote_path}")
            raise IOError(f"Failed to get file size: {e}")

    def delete_folder(self, remote_prefix: str) -> int:
        """
        フォルダ（プレフィックス）配下のオブジェクトを全削除
        
        Returns:
            削除したオブジェクト数
        """
        keys = self.list(remote_prefix)
        
        if not keys:
            return 0
        
        # 一括削除（最大1000件ずつ）
        deleted_count = 0
        for i in range(0, len(keys), 1000):
            batch = keys[i:i + 1000]
            try:
                self.s3.delete_objects(
                    Bucket=self.bucket,
                    Delete={'Objects': [{'Key': k} for k in batch]}
                )
                deleted_count += len(batch)
            except ClientError as e:
                raise IOError(f"Failed to delete objects: {e}")
        
        return deleted_count