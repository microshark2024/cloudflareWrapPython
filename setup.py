"""Package configuration."""

from setuptools import setup, find_packages

setup(
    name="cloudflare-warp-py",
    version="1.0.0",
    description="Cloudflare WARP desktop client – Python/Qt UI",
    author="microshark2024",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "PySide6>=6.5.0",
        "Pillow>=10.0.0",
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
