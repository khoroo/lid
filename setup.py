from setuptools import find_packages, setup

DEPENDENCIES = ["Pillow"]

setup(
        name="lid",
        version="0.0.1",
        author="sloum",
        install_requires=DEPENDENCIES,
        python_requires=">=3.6",
        entry_points={
        'console_scripts': [
            'lid = lid:main'
        ],
    }
)
