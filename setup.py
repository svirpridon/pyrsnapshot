from setuptools import setup

config = {
    'description': 'A rsnapshot re-implementation with push-over-ssh capability',
    'author': 'Jonathan Booth',
    'url': 'https://github.com/svirpridon/pyrsnapshot',
    'download_url': 'https://github.com/svirpridon/pyrsnapshot',
    'author_email': 'jbooth@gmail.com',
    'version': '0.2',
    'install_requires': ['nose2', 'assertpy', 'arrow', 'fabric3'],
    'packages': [''],
    'scripts': [],
    'name': 'pyrsnapshot',
}

setup(**config)
