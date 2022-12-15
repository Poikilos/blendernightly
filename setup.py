#!/usr/bin/env python
import setuptools
import sys
import os

# versionedModule = {}
# versionedModule['urllib'] = 'urllib'
# if sys.version_info.major < 3:
#     versionedModule['urllib'] = 'urllib2'

install_requires = []

if os.path.isfile("requirements.txt"):
    with open("requirements.txt", "r") as ins:
        for rawL in ins:
            line = rawL.strip()
            if len(line) < 1:
                continue
            install_requires.append(line)

description = (
    "Add and remove Blender versions easily."
)
long_description = description
if os.path.isfile("readme.md"):
    with open("readme.md", "r") as fh:
        long_description = fh.read()

setuptools.setup(
    name='blendernightly',
    version='0.5.0',
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 3',
        ('License :: OSI Approved :: '
         'GNU General Public License v3 or later (GPLv3+)'),  # See also: license=
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Software Distribution',
        'Topic :: Artistic Software',
    ],
    keywords=('blender blender3d install upgrade download update beta alpha'),
    url="https://poikilos.org",
    author="Jake Gustafson",
    # author_email='',
    license='GPLv3+',  # See also: license classifier above.
    packages=setuptools.find_packages(),
    # packages=['blendernightly'],
    include_package_data=True,  # look for MANIFEST.in
    # scripts=['example'],
    # ^ Don't use scripts anymore (according to
    #   <https://packaging.python.org/en/latest/guides
    #   /distributing-packages-using-setuptools
    #   /?highlight=scripts#scripts>).
    # See <https://stackoverflow.com/questions/27784271/
    # how-can-i-use-setuptools-to-generate-a-console-scripts-entry-
    # point-which-calls>
    entry_points={
        'console_scripts': [
            'blendernightly=update:main',
        ],
    },
    install_requires=install_requires,
    #     versionedModule['urllib'],
    # ^ "ERROR: Could not find a version that satisfies the requirement
    #   urllib (from nopackage) (from versions: none)
    #   ERROR: No matching distribution found for urllib"
    test_suite='nose.collector',
    tests_require=['nose', 'nose-cover3'],
    zip_safe=True,  # It can't run zipped due to needing data files.
)
