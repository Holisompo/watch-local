import os
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from webdav2.client import Client

class WebDAVSyncHandler(FileSystemEventHandler):
    def __init__(self, local_path, webdav_url, username, password, remote_path):
        """
        初始化文件同步处理器
        
        :param local_path: 本地监控文件夹路径
        :param webdav_url: WebDAV服务器URL
        :param username: WebDAV用户名
        :param password: WebDAV密码
        :param remote_path: WebDAV远程路径
        """
        self.local_path = local_path
        self.remote_path = remote_path
        
        # 配置WebDAV客户端
        self.webdav_client = Client({
            'webdav_hostname': webdav_url,
            'webdav_login': username,
            'webdav_password': password
        })
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)

    def on_created(self, event):
        if not event.is_directory:
            self._upload_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._upload_file(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self._delete_remote_file(event.src_path)

    def _upload_file(self, local_file_path):
        try:
            # 计算相对路径
            relative_path = os.path.relpath(local_file_path, self.local_path)
            remote_file_path = os.path.join(self.remote_path, relative_path)
            
            # 确保远程目录存在
            remote_dir = os.path.dirname(remote_file_path)
            if not self.webdav_client.check(remote_dir):
                self.webdav_client.mkdir(remote_dir)
            
            # 上传文件
            self.webdav_client.upload_file(local_file_path, remote_file_path)
            self.logger.info(f"上传文件: {local_file_path} -> {remote_file_path}")
        except Exception as e:
            self.logger.error(f"上传文件 {local_file_path} 出错: {str(e)}")

    def _delete_remote_file(self, local_file_path):
        try:
            relative_path = os.path.relpath(local_file_path, self.local_path)
            remote_file_path = os.path.join(self.remote_path, relative_path)
            
            if self.webdav_client.check(remote_file_path):
                self.webdav_client.delete(remote_file_path)
                self.logger.info(f"删除文件: {remote_file_path}")
        except Exception as e:
            self.logger.error(f"删除文件 {remote_file_path} 出错: {str(e)}")

def start_sync(local_path, webdav_url, username, password, remote_path):
    """
    启动文件夹同步
    
    :param local_path: 本地监控文件夹路径
    :param webdav_url: WebDAV服务器URL
    :param username: WebDAV用户名
    :param password: WebDAV密码
    :param remote_path: WebDAV远程路径
    """
    event_handler = WebDAVSyncHandler(local_path, webdav_url, username, password, remote_path)
    observer = Observer()
    observer.schedule(event_handler, local_path, recursive=True)
    observer.start()
    
    try:
        print(f"开始监控文件夹: {local_path}")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    # 配置参数
    LOCAL_PATH = ""
    WEBDAV_URL = ""
    USERNAME = ""
    PASSWORD = ""
    REMOTE_PATH = ""

    start_sync(LOCAL_PATH, WEBDAV_URL, USERNAME, PASSWORD, REMOTE_PATH)
