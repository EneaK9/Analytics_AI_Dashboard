#!/usr/bin/env python3
"""
SFTP Manager for FileZilla-style integrations
Handles SFTP connections, file listings, and downloads
"""

import paramiko
import os
import io
import stat
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

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

class SFTPManager:
    """Manages SFTP connections and file operations"""
    
    def __init__(self):
        self.client = None
        self.sftp = None
        
    def test_connection(self, credentials: SFTPCredentials) -> Tuple[bool, str, List[SFTPFileInfo]]:
        """
        Test SFTP connection and return available files
        Returns: (success, message, files_list)
        """
        try:
            # Create SSH client
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect
            logger.info(f" Testing SFTP connection to {credentials.host}:{credentials.port}")
            ssh_client.connect(
                hostname=credentials.host,
                port=credentials.port,
                username=credentials.username,
                password=credentials.password,
                timeout=30
            )
            
            # Open SFTP session
            sftp = ssh_client.open_sftp()
            
            # List files in remote path
            try:
                files = []
                file_list = sftp.listdir_attr(credentials.remote_path)
                
                for file_attr in file_list:
                    # Filter by pattern if specified
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
                
                logger.info(f" SFTP connection successful. Found {len(files)} files")
                return True, f"Connection successful. Found {len(files)} files.", files
                
            except Exception as path_error:
                sftp.close()
                ssh_client.close()
                logger.error(f" Path error: {path_error}")
                return False, f"Could not access path '{credentials.remote_path}': {str(path_error)}", []
                
        except paramiko.AuthenticationException:
            logger.error(f" SFTP authentication failed for {credentials.username}")
            return False, "Authentication failed. Please check username and password.", []
        except paramiko.SSHException as ssh_error:
            logger.error(f" SSH error: {ssh_error}")
            return False, f"SSH connection error: {str(ssh_error)}", []
        except Exception as e:
            logger.error(f" SFTP connection failed: {e}")
            return False, f"Connection failed: {str(e)}", []
    
    def download_file(self, credentials: SFTPCredentials, filename: str) -> Tuple[bool, bytes, str]:
        """
        Download a specific file from SFTP server
        Returns: (success, file_content, error_message)
        """
        try:
            # Create SSH client
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect
            ssh_client.connect(
                hostname=credentials.host,
                port=credentials.port,
                username=credentials.username,
                password=credentials.password,
                timeout=30
            )
            
            # Open SFTP session
            sftp = ssh_client.open_sftp()
            
            # Download file to memory
            remote_file_path = os.path.join(credentials.remote_path, filename).replace('\\', '/')
            file_buffer = io.BytesIO()
            
            logger.info(f" Downloading {remote_file_path}")
            sftp.getfo(remote_file_path, file_buffer)
            
            sftp.close()
            ssh_client.close()
            
            file_content = file_buffer.getvalue()
            logger.info(f" Downloaded {filename}: {len(file_content)} bytes")
            
            return True, file_content, ""
            
        except FileNotFoundError:
            logger.error(f" File not found: {filename}")
            return False, b"", f"File '{filename}' not found on server"
        except Exception as e:
            logger.error(f" Download failed for {filename}: {e}")
            return False, b"", f"Download failed: {str(e)}"
    
    def download_multiple_files(self, credentials: SFTPCredentials, filenames: List[str]) -> Dict[str, Any]:
        """
        Download multiple files from SFTP server
        Returns: {"success": bool, "files": {filename: content}, "errors": {filename: error}}
        """
        result = {
            "success": True,
            "files": {},
            "errors": {},
            "total_files": len(filenames),
            "downloaded_count": 0
        }
        
        try:
            # Create SSH client
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect
            ssh_client.connect(
                hostname=credentials.host,
                port=credentials.port,
                username=credentials.username,
                password=credentials.password,
                timeout=30
            )
            
            # Open SFTP session
            sftp = ssh_client.open_sftp()
            
            # Download each file
            for filename in filenames:
                try:
                    remote_file_path = os.path.join(credentials.remote_path, filename).replace('\\', '/')
                    file_buffer = io.BytesIO()
                    
                    logger.info(f" Downloading {remote_file_path}")
                    sftp.getfo(remote_file_path, file_buffer)
                    
                    result["files"][filename] = file_buffer.getvalue()
                    result["downloaded_count"] += 1
                    logger.info(f" Downloaded {filename}")
                    
                except Exception as file_error:
                    logger.error(f" Failed to download {filename}: {file_error}")
                    result["errors"][filename] = str(file_error)
                    result["success"] = False
            
            sftp.close()
            ssh_client.close()
            
            logger.info(f" Batch download complete: {result['downloaded_count']}/{result['total_files']} files")
            return result
            
        except Exception as e:
            logger.error(f" Batch download failed: {e}")
            result["success"] = False
            result["errors"]["connection"] = str(e)
            return result
    
    def list_files_with_details(self, credentials: SFTPCredentials) -> Tuple[bool, List[SFTPFileInfo], str]:
        """
        Get detailed file listing from SFTP server
        Returns: (success, files_list, error_message)
        """
        try:
            success, message, files = self.test_connection(credentials)
            return success, files, message if not success else ""
        except Exception as e:
            logger.error(f" File listing failed: {e}")
            return False, [], str(e)

# Global SFTP manager instance
sftp_manager = SFTPManager()