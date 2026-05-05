import PyInstaller.__main__
import os
import shutil
import customtkinter

if __name__ == '__main__':
    print("Building CMS...")
    ctk_path = os.path.dirname(customtkinter.__file__)
    app_name = "Houzez_CMS"
    
    PyInstaller.__main__.run([
        'app.py',
        f'--name={app_name}',
        '--noconfirm',
        '--windowed',
        '--onefile',
        f'--add-data={ctk_path};customtkinter/',
        '--clean'
    ])
    
    print("Build complete.")

    def _safe_copy(src: str, dst: str) -> None:
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
        except Exception:
            # Build should succeed even if publishing fails.
            pass

    # Keep a legacy alias so users don't accidentally run an old leftover build.
    dist_dir = os.path.join(os.getcwd(), "dist")
    src_exe = os.path.join(dist_dir, f"{app_name}.exe")
    if os.path.exists(src_exe):
        _safe_copy(src_exe, os.path.join(dist_dir, "CMS.exe"))

        # Also publish into stable locations so users don't run stale EXEs.
        here = os.path.dirname(os.path.abspath(__file__))
        _safe_copy(src_exe, os.path.join(here, f"{app_name}.exe"))
        _safe_copy(src_exe, os.path.join(here, "CMS.exe"))

        repo_root = os.path.abspath(os.path.join(here, "..", ".."))
        portable_dir = os.path.join(repo_root, "Portable")
        _safe_copy(src_exe, os.path.join(portable_dir, f"{app_name}.exe"))
        _safe_copy(src_exe, os.path.join(portable_dir, "CMS.exe"))
    
    # Clean up build artifacts if necessary
    if os.path.exists('build'):
        shutil.rmtree('build')
    spec_file = f"{app_name}.spec"
    if os.path.exists(spec_file):
        os.remove(spec_file)
