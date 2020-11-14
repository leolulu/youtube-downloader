import subprocess
import os
from concurrent.futures import ThreadPoolExecutor
import time
import shutil
from time import sleep


class YoutubeDownload:
    def __init__(self, target_folder_path='./DOWNLOADED'):
        self.download_command_template = 'youtube-dl -i --proxy socks5://127.0.0.1:10808 #ecode-video-placeholder# -o "{temp_folder}/%(title)s.%(ext)s" "{url}"'
        self.downloader = ThreadPoolExecutor(max_workers=4)
        self.target_folder_path = target_folder_path
        if not os.path.exists(target_folder_path):
            os.mkdir(target_folder_path)
        self.recode_video_sign = False
        self.serialno = 0

    def colored_print(self, content, id):
        palette = {0: 31, 1: 35, 2: 33, 3: 36}
        template = "\033[0;{fore_color};40m{content}\033[0m"
        print(template.format(fore_color=palette[id % 4], content=content))

    def the_guide(self):
        self.prompt = '(当前Mp4转换状态：{recode_video_status})(输入"mp4"切换状态) 输入指令或Url：'
        self.prompt = self.prompt.format(recode_video_status=self.recode_video_sign)
        if self.recode_video_sign:
            self.download_command = self.download_command_template.replace('#ecode-video-placeholder#', '--recode-video mp4')
        else:
            self.download_command = self.download_command_template.replace('#ecode-video-placeholder#', '')

    def download_process(self, download_command, id):
        p = subprocess.Popen(download_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        for line in iter(p.stdout.readline, ''):
            line = line.strip()
            self.colored_print(line, id)
            if line.find('ERROR') != -1:
                return False
        return True

    def download_dispatcher(self, url):
        self.serialno += 1
        id = self.serialno
        self.colored_print('开始下载：' + url, id)
        temp_folder = str(time.time()).replace('.', '')
        download_command = self.download_command.format(temp_folder=temp_folder, url=url)
        self.colored_print('下载指令：' + download_command, id)
        retry_times, success_sign = 10, False
        while retry_times >= 0:
            if self.download_process(download_command, id):
                success_sign = True
                break
            else:
                retry_times -= 1
                time.sleep(10)
                self.colored_print(f'重试，剩余{retry_times}次机会...', id)
        if success_sign:
            for file_ in os.listdir(temp_folder):
                shutil.move(os.path.join(temp_folder, file_), self.target_folder_path)
            shutil.rmtree(temp_folder)
            self.colored_print('下载完成！' + url, id)
        else:
            self.colored_print('下载失败！' + url, id)

    def run_local_loop(self):
        while True:
            self.the_guide()
            input_value = input(self.prompt).strip()
            if not input_value:
                continue
            if input_value == 'mp4':
                self.recode_video_sign = not self.recode_video_sign
            else:
                self.downloader.submit(self.download_dispatcher, input_value)


if __name__ == "__main__":
    api = YoutubeDownload(r"D:\syncthing-windows-amd64-v1.11.1\LOCAL_STORAGE\youtube手机在线文件夹")
    print("当前下载文件夹：",os.path.abspath(api.target_folder_path))
    api.run_local_loop()
