import os
import sys
import json
import time
import tempfile
import subprocess

import pyautogui
import imageio

import hunter
hunter.trace(module='execute', action=hunter.CallPrinter)

LINUX = False

if 'linux' in sys.platform.lower():
    LINUX = True
    from pyvirtualdisplay import Display
    import Xlib.display as Xdisp

CONST = {
    'arg' : 'argument',
    'do' : 'do',
    'exec' : 'execute',
    'init_timeout' : 'initial timeout',
    'method' : 'method',
    'perform' : 'perform',
    'res' : 'resolution',
    'steps' : 'steps',
    'test_timeout' : 'timeout',
    'tests' : 'tests',
    'timeout_between' : 'timeout between tests',
    'confidence': 'confidence'
}

def load(filename):
    with open(filename, 'r') as config:
        return json.loads(config.read())

def make_config_context(filename, temp_dir):
    config = load(filename)

    def make_screenshot():
        pyautogui.screenshot(os.path.join(temp_dir, str(time.clock()) + '.png'))

    def find_test(test_name):
        return next(filter(lambda t: t[CONST['do']] == test_name, config[CONST['tests']]))

    def HANDMADE(step):
        exec(step[CONST['arg']])
        time.sleep(step[CONST['test_timeout']])

    def handle_pyauto(step):
        if step[CONST['method']] == 'HANDMADE':
            HANDMADE(step)
            return
        call = getattr(pyautogui, step[CONST['method']])
        call(eval(step[CONST['arg']]))
        time.sleep(step[CONST['test_timeout']])

    def execute_test(test, timeout):
        if isinstance(test, str):
            test = find_test(test)
        time.sleep(timeout)
        time.sleep(test[CONST['test_timeout']])
        for step in test[CONST['steps']]:
            make_screenshot()
            if isinstance(step,dict):
                handle_pyauto(step)
                continue
            if not ('.' in step):
                execute_test(find_test(step), timeout)
                continue
            located = pyautogui.locateOnScreen(step, confidence=config[CONST['confidence']])
            center_point = pyautogui.center(located)
            pyautogui.click(center_point.x, center_point.y)
            make_screenshot()

    def launch_subprocess():
        def kill_subprocess():
            subp.kill()
        subp = subprocess.Popen(config[CONST['exec']])
        time.sleep(config[CONST['init_timeout']])
        return kill_subprocess

    return (config, execute_test, launch_subprocess)

def main(configname):
    def body():
        subprocess_killer = subprocess_launcher()
        for test in config[CONST['perform']]:
            try:
                test_executor(test, config[CONST['timeout_between']])
            except Exception:
                print('Тест "{}" не прошел!'.format(test))
                continue
            print('Тест "{}" прошел!'.format(test))
        subprocess_killer()
        animation = []
        for frame in (os.path.join(temp_dir, f) for f in sorted(os.listdir(temp_dir))):
            animation.append(imageio.imread(frame))
        imageio.mimsave(config[CONST['exec']] + '.gif', animation, fps=4)

    with tempfile.TemporaryDirectory() as temp_dir:
        config, test_executor, subprocess_launcher = make_config_context(configname, temp_dir)
        width, height = config[CONST['res']].split('x')
        if LINUX:
            with Display(size=(int(width), int(height))) as virt_disp:
                pyautogui._pyautogui_x11._display = Xdisp.Display(os.environ['DISPLAY'])
                body()
        else:
            body()

for configname in sys.argv[1:]:
    main(configname)

