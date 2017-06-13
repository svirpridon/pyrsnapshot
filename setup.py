from setuptools import setup

config = {
    'name': 'pyrsnapshot',
    'description': 'A rsnapshot re-implementation with push-over-ssh capability',
    'url': 'https://github.com/svirpridon/pyrsnapshot',
    'author': 'Jonathan Booth',
    'author_email': 'jbooth@gmail.com',
    'version': '0.3.2',
    'license': 'GPLv3',
    'classifiers': [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: System :: Archiving :: Backup',
        'Topic :: System :: Systems Administration',
    ],
    'keywords': 'rsync backup',
    'packages': ['pyrsnapshot'],
    'install_requires': ['arrow', 'fabric3'],
    'tests_require': ['assertpy', 'nose2'],
    'entry_points': {
        'console_scripts': [
            'pyrsnapshot = pyrsnapshot.__main__:main',
        ],
    },
}

setup(**config)
