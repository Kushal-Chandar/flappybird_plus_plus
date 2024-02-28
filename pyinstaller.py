import zipfile
import PyInstaller.__main__
import os


def install():
    PyInstaller.__main__.run(
        [
            "main.py",
            "--onefile",
            "--distpath=.",
            "--i=./assets/flappybird++.ico",
            "--noconfirm",
            "--name=flappybird++",
            "--windowed",
            "--add-data=assets;assets",
            "--contents-directory=.",
        ]
    )


if __name__ == "__main__":
    install()
    flappybirdexec = "flappybird++.exe"
    with zipfile.ZipFile("flappybird++.zip", "w") as zipf:
        zipf.write(flappybirdexec)
        for root, _, files in os.walk("assets"):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path)
        if os.path.exists(flappybirdexec):
            os.remove(flappybirdexec)
