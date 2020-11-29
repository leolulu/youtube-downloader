import subprocess
import os
from concurrent.futures import ThreadPoolExecutor
import time
import shutil
import arrow
import re
from ruamel.yaml import YAML
import platform


class YoutubeDownload:
    def __init__(self):
        self.load_config("config.yaml")
        self.download_command_template = 'youtube-dl -i --proxy socks5://127.0.0.1:10808 #ecode-video-placeholder# -o "{temp_folder}/%(title)s.%(ext)s" "{url}"'
        self.downloader = ThreadPoolExecutor(max_workers=4)
        self.target_folder_path = self.conf['target_folder_path']
        if not os.path.exists(self.target_folder_path):
            os.mkdir(self.target_folder_path)
        self.recode_video_sign = self.conf['recode_video_sign']
        self.serialno = 0
        self.default_error_record_file_path = self.conf['default_error_record_file_path']

    def load_config(self, config_path):
        yaml = YAML(typ='safe')
        with open(config_path, 'r', encoding='utf-8') as f:
            conf = yaml.load(f)
        platform_node = platform.node()
        if platform_node in conf:
            self.conf = conf.get(platform_node)
            print('使用配置：', platform_node)
        else:
            self.conf = conf.get('default')
            print('使用配置：', 'default')

    def error_recorder_local_file(self, url: str, additional_info: str = None, file_path=None):
        if not file_path:
            file_path = self.default_error_record_file_path
        record = ''
        record += f"{arrow.now().format('YYYYMMDD_HHmm')}：\n"
        record += url + '\n'
        record += additional_info + '\n'
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(record)

    def init_reload_default_failed_task(self):
        if not os.path.exists(self.default_error_record_file_path):
            return
        with open(self.default_error_record_file_path, 'r', encoding='utf-8') as f:
            failed_urls = f.read().split('\n')
        failed_urls = [i for i in failed_urls if re.search(r"^http.*?youtube", i)]
        self._set_recode_video_switch()
        for url in failed_urls:
            print(f'重启上一次的失败任务：{url}')
            self.downloader.submit(self.download_dispatcher, url)
        os.remove(self.default_error_record_file_path)

    def colored_print(self, content, id):
        palette = self.conf['palette']
        template = "\033[0;{fore_color};40m{content}\033[0m"
        print(template.format(fore_color=palette[id % 4], content=content))

    def _set_recode_video_switch(self):
        if self.recode_video_sign:
            self.download_command = self.download_command_template.replace('#ecode-video-placeholder#', '--recode-video mp4')
        else:
            self.download_command = self.download_command_template.replace('#ecode-video-placeholder#', '')

    def the_guide(self):
        self.prompt = '(当前Mp4转换状态：{recode_video_status})(输入"mp4"切换状态) 输入指令或Url：'
        self.prompt = self.prompt.format(recode_video_status=self.recode_video_sign)
        self._set_recode_video_switch()

    def download_process(self, download_command, id):
        p = subprocess.Popen(download_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        for line in iter(p.stdout.readline, ''):
            line = line.strip()
            line = f"[{arrow.now().format('YYYY-MM-DD HH:mm:ss')}] " + line
            self.colored_print(line, id)
            if line.find('ERROR') != -1:
                return False, line
        return True, None

    def download_dispatcher(self, url):
        self.serialno += 1
        id = self.serialno
        self.colored_print('开始下载：' + url, id)
        temp_folder = str(time.time()).replace('.', '')
        download_command = self.download_command.format(temp_folder=temp_folder, url=url)
        self.colored_print('下载指令：' + download_command, id)
        retry_times, success_sign = self.conf['retry_times'], False
        while retry_times >= 0:
            if_success, info = self.download_process(download_command, id)
            if if_success:
                success_sign = True
                break
            else:
                retry_times -= 1
                time.sleep(self.conf['retry_delay'])
                self.colored_print(f'重试，剩余{retry_times}次机会...', id)
        if success_sign:
            for file_ in os.listdir(temp_folder):
                shutil.move(os.path.join(temp_folder, file_), self.target_folder_path)
            shutil.rmtree(temp_folder)
            self.colored_print('下载完成！' + url, id)
        else:
            self.colored_print('下载失败！' + url, id)
            self.error_recorder_local_file(url, additional_info=info)

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
    api = YoutubeDownload()
    print("当前下载文件夹：", os.path.abspath(api.target_folder_path))
    api.init_reload_default_failed_task()
    api.run_local_loop()
