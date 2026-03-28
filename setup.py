"""Package configuration."""

from setuptools import setup, find_packages

setup(
    name="cloudflare-warp-py",
    version="1.0.0",
    description="Cloudflare WARP desktop client – Python/Tkinter UI",
    author="microshark2024",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "Pillow>=10.0.0",
        "pystray>=0.19.0",
    ],
    entry_points={
        "console_scripts": [
            "cloudflare-warp-py=cloudflare_warp.main:main",
        ],
        "gui_scripts": [
            "cloudflare-warp-pyw=cloudflare_warp.main:main",
        ],
    },
)
