"""
A data science workflow tool.
"""

import os
from setuptools import setup, find_packages


def get_version():
    basedir = os.path.dirname(__file__)
    try:
        with open(os.path.join(basedir, 'dstrace/version.py')) as f:
            loc = {}
            exec(f.read(), loc)
            return loc['VERSION']
    except:
        raise RuntimeError('No version info found.')

setup(
    name='dstrace',
    version=get_version(),
    url='https://github.com/sancau/dstrace/',
    license='MIT',
    author='Alexander Tatchin',
    author_email='alexander.tatchin@gmail.com',
    description='Data science workflow automation tool.',
    long_description=__doc__,
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'fire==0.2.1',
        'GitPython==3.0.8',
        'html5lib==1.0.1',
        'nbconvert==5.6.1',
        'PyYAML==5.2',
        'requests==2.22.0',
        'traitlets==4.3.3',
        'bleach==3.1.4',
    ],
    entry_points={
        'console_scripts': [
            'dstrace=dstrace.dstrace:main',
        ],
    },
    classifiers=[
        #  As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Intended Audience :: Developers',
        # 'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        # 'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        # 'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        # 'Topic :: Internet',
        # 'Topic :: Internet :: Log Analysis',
        'Topic :: Scientific/Engineering',
        # 'Topic :: System :: Systems Administration',
        # 'Topic :: System :: Monitoring',
        # 'Topic :: System :: Distributed Computing',
    ]
)
