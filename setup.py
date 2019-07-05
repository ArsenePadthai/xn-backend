import glob
import stat
import sys
import os

from setuptools import setup, find_packages

try:
    from pip.req import parse_requirements
    from pip.download import PipSession
except ImportError:
    from pip._internal.req import parse_requirements
    from pip._internal.download import PipSession

# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = parse_requirements('requirements.txt', session=PipSession())

# reqs is a list of requirement
# e.g. ['django==1.5.1', 'mezzanine==1.4.6']
reqs = [str(ir.req) for ir in install_reqs]

if sys.platform.lower().startswith('linux'):
    production_reqs = parse_requirements('requirements-production.txt', session=PipSession())
    reqs += [str(ir.req) for ir in production_reqs]

migration_files = {}
if os.path.isdir('migrations'):
    for f in glob.glob('migrations/**', recursive=True):
        if '__pycache__' in f.split(os.sep):
            continue
        if not stat.S_ISREG(os.stat(f).st_mode):
            continue

        migration_files.setdefault(os.path.split(f)[0], list()).append(f)

setup(
    name='XNBackend',
    version='1.0',
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=reqs,
    data_files=list(migration_files.items()),
    url='http://www.huangloong.com',
    author='huangloong IoT Inc.',
    author_email='rd@huangloong.com',
    entry_points={
        'console_scripts': [
            'xn-backend=XNBackend.cli:cli'
        ],
    },
)
