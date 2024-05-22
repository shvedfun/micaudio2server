from distutils.core import setup
import py2exe

DISTUTILS_DEBUG = True

setup(
    # version_info={'name': 'client_ws' ,'version':'0.1'},
    # options={"include": ["sounddevice"]},
    # zipfile='.\\dist\\library.zip',
    # packages=['_sounddevice_data', ],
    # package_dir={'_sounddevice_data': 'C:\\workspace\\Daniil\\venv\\Lib\\site-packages\\_sounddevice_data\\'},
    # package_data={'_sounddevice_data': ['portaudio-binaries\\*.dll']},
    console=['client_ws.py'],
    py_modules=['config']
)
