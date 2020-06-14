import os
import json
import time
import tempfile
import subprocess

import pyautogui
import Xlib.display as Xdisp
import imageio

from pyvirtualdisplay import Display

def load(filename):
    with open(filename, 'r') as config:
        return json.loads(config.read())
    
def make_config_context(filename, temp_dir):
    config = load(filename)

    def make_screenshot():
        pyautogui.screenshot(os.path.join(temp_dir, str(time.clock()) + '.png'))

    def find_test(test_name):
        return next(filter(lambda t: t['do'] == test_name, config['tests']))

    def execute_test(test, timeout):
        time.sleep(timeout)
        time.sleep(test['timeout'])
        for step in test['steps']:
            if not ('.' in step):
                execute_test(find_test(step), timeout)
                continue
            make_screenshot()
            located = pyautogui.locateOnScreen(step)
            center_point = pyautogui.center(located)
            pyautogui.click(center_point.x, center_point.y)
            make_screenshot()

    def launch_subprocess():
        def kill_subprocess():
            subp.kill()
        subp = subprocess.Popen(config['execute'])
        time.sleep(config['initial timeout'])
        return kill_subprocess

    return (config, execute_test, launch_subprocess)

def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        config, test_executor, subprocess_launcher = make_config_context('test_example.json', temp_dir)
        subprocess_killer = subprocess_launcher()
        for test in config['tests']:
            test_executor(test, config['timeout'])
        subprocess_killer()
        animation = []
        for frame in (os.path.join(temp_dir, f) for f in sorted(os.listdir(temp_dir))):
            animation.append(imageio.imread(frame))
        imageio.mimsave(config['execute'] + '.gif', animation, fps=4)

with Display(size=(800,600)) as virt_disp:
    pyautogui._pyautogui_x11._display = Xdisp.Display(os.environ['DISPLAY'])
    main()

