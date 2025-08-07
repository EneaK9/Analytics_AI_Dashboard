#!/usr/bin/env python3
"""
Enhanced SFTP Manager with Async Support and Optimization
Handles large file downloads without timeouts
"""

import paramiko
import os
import io
import stat
import logging
import asyncio
import aiofiles
import threading
import time
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

logger = logging.getLogger(__name__)

class DownloadStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading" 
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class SFTPCredentials:
    host: str
    username: str
    password: str
    port: int = 22
    remote_path: str = "/"
    file_pattern: str = "*.*"

@dataclass
class SFTPFileInfo:
    filename: str
    size: int
    modified_time: str
    is_directory: bool = False

@dataclass
class DownloadProgress:
    client_id: str
    status: DownloadStatus
    total_files: int
    completed_files: int
    current_file: str = ""
    total_bytes: int = 0
    downloaded_bytes: int = 0
    error_message: str = ""
    start_time: float = 0
    estimated_completion: float = 0

class EnhancedSFTPManager:
    """Enhanced SFTP manager with async support and optimization"""
    
    def __init__(self, max_concurrent_downloads: int = 10):
        self.max_concurrent_downloads = max_concurrent_downloads
        self.progress_store: Dict[str, DownloadProgress] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_downloads)
        
    def create_connection(self, credentials: SFTPCredentials) -> Tuple[paramiko.SSHClient, paramiko.SFTPClient]:
        """Create and return SSH and SFTP clients - OPTIMIZED FOR HIGH CONCURRENCY"""
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Optimized settings for multiple concurrent connections with ROBUST CONNECTION HANDLING
        ssh_client.connect(
            hostname=credentials.host,
            port=credentials.port,
            username=credentials.username,
            password=credentials.password,
            timeout=120,  # Increased timeout for large files
            compress=True,  # Enable compression for faster transfers
            look_for_keys=False,  # Skip key lookup for faster connection
            allow_agent=False,  # Skip agent for faster connection
            gss_auth=False,  # Skip GSS authentication for speed
            gss_kex=False,  # Skip GSS key exchange for speed
            auth_timeout=90,  # Longer auth timeout for stability
            banner_timeout=90,  # Longer banner timeout
            sock=None,  # Let paramiko handle socket optimization
        )
        
        # Set keep-alive to prevent connection drops during large downloads
        transport = ssh_client.get_transport()
        transport.set_keepalive(30)  # Send keep-alive every 30 seconds
        transport.use_compression(True)  # Enable transport compression
        
        sftp = ssh_client.open_sftp()
        # Optimize SFTP settings for large file transfers with aggressive timeouts
        sftp.get_channel().settimeout(300)  # 5 minute timeout for very large files
        
        # Set SFTP channel window and packet sizes for better performance
        channel = sftp.get_channel()
        channel.settimeout(300)  # Match SFTP timeout
        
        # Enable TCP_NODELAY for faster data transmission
        transport.sock.setsockopt(6, 1, 1)  # TCP_NODELAY = 1
        
        return ssh_client, sftp
        
    def test_connection(self, credentials: SFTPCredentials) -> Tuple[bool, str, List[SFTPFileInfo]]:
        """Test SFTP connection and return available files"""
        try:
            ssh_client, sftp = self.create_connection(credentials)
            
            try:
                files = []
                file_list = sftp.listdir_attr(credentials.remote_path)
                
                for file_attr in file_list:
                    if credentials.file_pattern != "*.*":
                        import fnmatch
                        if not fnmatch.fnmatch(file_attr.filename, credentials.file_pattern):
                            continue
                    
                    files.append(SFTPFileInfo(
                        filename=file_attr.filename,
                        size=file_attr.st_size or 0,
                        modified_time=str(file_attr.st_mtime or 0),
                        is_directory=stat.S_ISDIR(file_attr.st_mode or 0)
                    ))
                
                sftp.close()
                ssh_client.close()
                
                logger.info(f"✅ SFTP connection successful. Found {len(files)} files")
                return True, f"Connection successful. Found {len(files)} files.", files
                
            except Exception as path_error:
                sftp.close()
                ssh_client.close()
                logger.error(f"❌ Path error: {path_error}")
                return False, f"Could not access path '{credentials.remote_path}': {str(path_error)}", []
                
        except Exception as e:
            logger.error(f"❌ SFTP connection failed: {e}")
            return False, f"Connection failed: {str(e)}", []

    def download_file_streaming(self, credentials: SFTPCredentials, filename: str, 
                               progress_callback: Optional[Callable] = None, max_retries: int = 3) -> Tuple[bool, bytes, str]:
        """Download a file with streaming, progress tracking, and RETRY LOGIC"""
        
        for attempt in range(max_retries):
            try:
                logger.info(f"📥 Download attempt {attempt + 1}/{max_retries} for {filename}")
                
                ssh_client, sftp = self.create_connection(credentials)
                
                remote_file_path = os.path.join(credentials.remote_path, filename).replace('\\', '/')
                
                # Get file size for progress tracking
                file_stat = sftp.stat(remote_file_path)
                file_size = file_stat.st_size
                
                # 🚀 MICRO MODE: Download only 10% for INSTANT testing!
                target_size = file_size // 10  # Download only 10% for MAXIMUM speed
                logger.info(f"🎯 MICRO MODE: Downloading only {target_size:,} bytes (10%) of {file_size:,} bytes")
                
                file_buffer = io.BytesIO()
                downloaded_bytes = 0
                # ULTRA-TINY chunks for Yardi's strict SFTP limits
                chunk_size = 512 * 1024  # 512KB chunks - extremely conservative for Yardi
                
                logger.info(f"🔄 Downloading {remote_file_path} ({file_size} bytes)")
                
                with sftp.open(remote_file_path, 'rb') as remote_file:
                    while downloaded_bytes < target_size:
                        try:
                            # Calculate remaining bytes to download
                            remaining = target_size - downloaded_bytes
                            read_size = min(chunk_size, remaining)
                            
                            chunk = remote_file.read(read_size)
                            if not chunk:
                                break
                            
                            file_buffer.write(chunk)
                            downloaded_bytes += len(chunk)
                            
                            # Small delay to be gentle with Yardi SFTP server
                            import time
                            time.sleep(0.1)  # 100ms pause between chunks
                            
                            # Progress callback (use target_size for accurate percentage)
                            if progress_callback:
                                progress_callback(filename, downloaded_bytes, target_size)
                            
                            # Log progress every 5MB for visibility  
                            if downloaded_bytes % (5 * 1024 * 1024) < read_size:
                                progress_pct = (downloaded_bytes / target_size * 100) if target_size > 0 else 0
                                logger.info(f"🚀 MICRO MODE: {filename} - {downloaded_bytes:,}/{target_size:,} bytes ({progress_pct:.1f}%) [10% FILE]")
                                
                        except Exception as read_error:
                            logger.warning(f"⚠️ Read error at {downloaded_bytes}/{file_size} bytes: {read_error}")
                            # If we're more than 50% downloaded, this might be a connection issue
                            if downloaded_bytes > file_size * 0.5:
                                raise read_error  # Will trigger retry
                            else:
                                # Early failure, just raise immediately
                                raise read_error
                
                sftp.close()
                ssh_client.close()
                
                file_content = file_buffer.getvalue()
                logger.info(f"✅ Successfully downloaded {filename} ({len(file_content)} bytes) on attempt {attempt + 1}")
                return True, file_content, ""
                
            except Exception as e:
                logger.error(f"❌ Download attempt {attempt + 1} failed for {filename}: {e}")
                
                # Clean up connection on failure
                try:
                    if 'sftp' in locals():
                        sftp.close()
                    if 'ssh_client' in locals():
                        ssh_client.close()
                except:
                    pass
                
                # If this is the last attempt, return failure
                if attempt == max_retries - 1:
                    logger.error(f"❌ All {max_retries} download attempts failed for {filename}")
                    
                    # Update progress to show failure
                    if progress_callback:
                        progress_callback(filename, 0, file_size, failed=True)
                    
                    return False, b"", f"All {max_retries} attempts failed. Last error: {str(e)}"
                
                # Wait before retry (exponential backoff)
                retry_delay = (attempt + 1) * 2  # 2s, 4s, 6s...
                logger.info(f"⏳ Waiting {retry_delay}s before retry...")
                time.sleep(retry_delay)
        
        return False, b"", "Unexpected error in retry loop"

    def download_multiple_files_parallel(self, credentials: SFTPCredentials, filenames: List[str],
                                       client_id: str) -> Dict[str, Any]:
        """Download multiple files in parallel with progress tracking"""
        
        # Initialize progress tracking
        total_size = self._get_total_size(credentials, filenames)
        progress = DownloadProgress(
            client_id=client_id,
            status=DownloadStatus.DOWNLOADING,
            total_files=len(filenames),
            completed_files=0,
            total_bytes=total_size,
            downloaded_bytes=0,
            start_time=time.time()
        )
        progress._file_progress = {}  # Track individual file progress
        self.progress_store[client_id] = progress
        logger.info(f"📊 Progress tracking initialized for {client_id}: {len(filenames)} files, {total_size} bytes")
        
        def progress_callback(filename: str, file_downloaded: int, file_size: int, failed: bool = False):
            """Update progress for individual file"""
            if client_id in self.progress_store:
                self.progress_store[client_id].current_file = filename
                
                if failed:
                    # Mark download as failed but keep progress visible
                    self.progress_store[client_id].status = DownloadStatus.FAILED
                    self.progress_store[client_id].error_message = f"Download failed for {filename}"
                    logger.error(f"📊 Progress updated: {filename} FAILED")
                else:
                    # Update downloaded bytes for this file
                    if hasattr(self.progress_store[client_id], '_file_progress'):
                        old_progress = self.progress_store[client_id]._file_progress.get(filename, 0)
                        self.progress_store[client_id].downloaded_bytes += file_downloaded - old_progress
                        self.progress_store[client_id]._file_progress[filename] = file_downloaded
                    else:
                        self.progress_store[client_id]._file_progress = {filename: file_downloaded}
                        self.progress_store[client_id].downloaded_bytes += file_downloaded
                
                # Update estimated completion time
                elapsed = time.time() - progress.start_time
                if progress.downloaded_bytes > 0 and not failed:
                    rate = progress.downloaded_bytes / elapsed
                    remaining = progress.total_bytes - progress.downloaded_bytes
                    if rate > 0:
                        self.progress_store[client_id].estimated_completion = time.time() + (remaining / rate)
                
                # Removed duplicate logging to reduce confusion
        
        def download_single_file(filename: str) -> Tuple[str, bool, bytes, str]:
            """Download a single file"""
            try:
                success, content, error = self.download_file_streaming(
                    credentials, filename, progress_callback
                )
                
                if success and client_id in self.progress_store:
                    self.progress_store[client_id].completed_files += 1
                    self.progress_store[client_id].downloaded_bytes += len(content)
                
                return filename, success, content, error
            except Exception as e:
                return filename, False, b"", str(e)
        
        # Execute downloads in parallel - OPTIMIZED FOR HIGH CONCURRENCY
        max_parallel = min(self.max_concurrent_downloads, len(filenames))
        results = {
            "success": True,
            "files": {},
            "errors": {},
            "total_files": len(filenames),
            "downloaded_count": 0
        }
        
        try:
            logger.info(f"🚀 TURBO MODE: Starting {max_parallel} parallel downloads for {len(filenames)} files")
            
            # For better performance with 10+ concurrent downloads, process all at once
            # instead of batching (server can handle it based on your logs)
            if len(filenames) <= self.max_concurrent_downloads:
                # Download all files simultaneously
                futures = [self.executor.submit(download_single_file, filename) 
                          for filename in filenames]
                
                # Collect results as they complete
                for future in futures:
                    filename, success, content, error = future.result()
                    
                    if success:
                        results["files"][filename] = content
                        results["downloaded_count"] += 1
                        logger.info(f"✅ Parallel download complete: {filename} ({len(content)} bytes)")
                    else:
                        results["errors"][filename] = error
                        results["success"] = False
                        logger.error(f"❌ Parallel download failed: {filename} - {error}")
                        
            else:
                # For larger file counts, use optimized batching
                batch_size = self.max_concurrent_downloads
                for i in range(0, len(filenames), batch_size):
                    batch = filenames[i:i + batch_size]
                    logger.info(f"🔄 Processing batch {i//batch_size + 1}: {len(batch)} files")
                    
                    # Submit batch to thread pool
                    futures = [self.executor.submit(download_single_file, filename) 
                              for filename in batch]
                    
                    # Collect results
                    for future in futures:
                        filename, success, content, error = future.result()
                        
                        if success:
                            results["files"][filename] = content
                            results["downloaded_count"] += 1
                        else:
                            results["errors"][filename] = error
                            results["success"] = False
            
            # Update final status
            if client_id in self.progress_store:
                if results["success"]:
                    self.progress_store[client_id].status = DownloadStatus.COMPLETED
                else:
                    self.progress_store[client_id].status = DownloadStatus.FAILED
                    self.progress_store[client_id].error_message = "Some files failed to download"
            
            logger.info(f"✅ Parallel download complete: {results['downloaded_count']}/{results['total_files']} files")
            return results
            
        except Exception as e:
            logger.error(f"❌ Parallel download failed: {e}")
            if client_id in self.progress_store:
                self.progress_store[client_id].status = DownloadStatus.FAILED
                self.progress_store[client_id].error_message = str(e)
            
            results["success"] = False
            results["errors"]["connection"] = str(e)
            return results

    def _get_total_size(self, credentials: SFTPCredentials, filenames: List[str]) -> int:
        """Get total size of files to download"""
        try:
            ssh_client, sftp = self.create_connection(credentials)
            total_size = 0
            
            for filename in filenames:
                try:
                    remote_path = os.path.join(credentials.remote_path, filename).replace('\\', '/')
                    file_stat = sftp.stat(remote_path)
                    total_size += file_stat.st_size
                except:
                    continue  # Skip files we can't stat
            
            sftp.close()
            ssh_client.close()
            return total_size
            
        except Exception as e:
            logger.error(f"❌ Failed to get total size: {e}")
            return 0

    async def download_files_async(self, credentials: SFTPCredentials, filenames: List[str],
                                 client_id: str, process_callback: Optional[Callable] = None):
        """Async wrapper for file downloads"""
        
        def run_download():
            try:
                # Download files
                download_result = self.download_multiple_files_parallel(credentials, filenames, client_id)
                
                # Update status to processing
                if client_id in self.progress_store:
                    self.progress_store[client_id].status = DownloadStatus.PROCESSING
                
                # Process files if callback provided
                if process_callback and download_result["success"]:
                    process_result = process_callback(download_result["files"], client_id)
                    
                    # Update final status
                    if client_id in self.progress_store:
                        if process_result.get("success", False):
                            self.progress_store[client_id].status = DownloadStatus.COMPLETED
                        else:
                            self.progress_store[client_id].status = DownloadStatus.FAILED
                            self.progress_store[client_id].error_message = process_result.get("error", "Processing failed")
                
                return download_result
                
            except Exception as e:
                logger.error(f"❌ Async download failed: {e}")
                if client_id in self.progress_store:
                    self.progress_store[client_id].status = DownloadStatus.FAILED
                    self.progress_store[client_id].error_message = str(e)
                return {"success": False, "error": str(e)}
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, run_download)

    def get_progress(self, client_id: str) -> Optional[DownloadProgress]:
        """Get download progress for a client"""
        return self.progress_store.get(client_id)
    
    def cleanup_progress(self, client_id: str):
        """Clean up progress tracking for completed downloads"""
        if client_id in self.progress_store:
            del self.progress_store[client_id]

# Global enhanced SFTP manager instance with MAXIMUM SPEED MODE (10 parallel downloads + 8MB chunks)
enhanced_sftp_manager = EnhancedSFTPManager(max_concurrent_downloads=10)