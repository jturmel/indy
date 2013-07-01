from distutils.core import setup

setup(
    name='indy',
    version='0.2',
    packages=['indy', ],
    license='GNU',
    entry_points={
        'console_scripts': ['indy = indy:main']
    },
    install_requires=[]
)
