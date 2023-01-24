from setuptools import find_packages, setup

DEPENDENCIES = ["Pillow"]

setup(
        name="lid",
        version="0.0.2",
        author="sloum, khoroo",
        install_requires=DEPENDENCIES,
        python_requires=">=3.11",
        entry_points={
        'console_scripts': [
            'lid = lid:main'
        ],
    }
)
