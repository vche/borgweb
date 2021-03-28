# -*- encoding: utf-8 *-*
import sys

from setuptools import setup, find_packages

min_python = (3, 4)
if sys.version_info < min_python:
    print("BorgWeb requires Python %d.%d or later" % min_python)
    sys.exit(1)


long_description = "WEB UI for borg backup tool"

setup(
    name='borgweb',
    # use_scm_version=dict(write_to='borgweb/_version.py'),
    author='Vivien Chene, original work by The Borg Collective (see AUTHORS)',
    author_email='viv@vivc.org',
    url='https://github.com/vche/borgweb',
    description='Browser-based user interface for BorgBackup, inspired',
    long_description=long_description,
    license='BSD',
    platforms=['Linux', 'MacOS X', 'FreeBSD', 'OpenBSD', 'NetBSD', ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: BSD :: FreeBSD',
        'Operating System :: POSIX :: BSD :: OpenBSD',
        'Operating System :: POSIX :: BSD :: NetBSD',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: System :: Archiving :: Backup',
    ],
    packages=find_packages(),
    package_data={
        'borgweb': [
            'static/*.*',  # does NOT match subdirectories!
            'static/bootstrap/*',
            'static/fonts/*',
            'static/i18n/*',
            'templates/*',
        ],
    },
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'borgweb = borgweb.app:main',
        ]
    },
    setup_requires=['setuptools_scm>=1.7'],
    install_requires=[
        'flask>=0.7',  # >= 0.10 required for python 3
    ],
)
