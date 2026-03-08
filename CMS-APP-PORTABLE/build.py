import PyInstaller.__main__
import os
import shutil
import customtkinter

if __name__ == '__main__':
    print("Building CMS...")
    ctk_path = os.path.dirname(customtkinter.__file__)
    
    PyInstaller.__main__.run([
        'app.py',
        '--name=CMS',
        '--noconfirm',
        '--windowed',
        '--onefile',
        f'--add-data={ctk_path};customtkinter/',
        '--clean'
    ])
    
    print("Build complete.")
    
    # Clean up build artifacts if necessary
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('CMS.spec'):
        os.remove('CMS.spec')
