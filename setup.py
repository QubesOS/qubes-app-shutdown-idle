# pylint: disable=missing-docstring
import setuptools

if __name__ == '__main__':
    setuptools.setup(
        name='qubesidle',
        version=open('version').read().strip(),
        author='Invisible Things Lab',
        author_email='qubes-devel@googlegroups.com',
        description='Qubes Shutdown Idle Script',
        license='GPL2+',
        url='https://www.qubes-os.org/',
        packages=['qubesidle'],
        entry_points={
            'console_scripts': [
                'qubes-idle-watcher = qubesidle.idleness_monitor:main'
            ],
            'idle_watcher': [
                'x-window-monitor = qubesidle.idle_watcher_window:IdleWatcher'
            ]
        })
