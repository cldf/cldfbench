from setuptools import setup, find_packages


setup(
    name='cldfbench',
    version='1.7.0',
    author='Robert Forkel',
    author_email='forkel@shh.mpg.de',
    description='Python library implementing a CLDF workbench',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    keywords='',
    license='Apache 2.0',
    url='https://github.com/cldf/cldfbench',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'cldfbench=cldfbench.__main__:main',
        ],
    },
    platforms='any',
    python_requires='>=3.6',
    install_requires=[
        'csvw>=1.5.6',
        'cldfcatalog>=1.3',
        'clldutils>=3.6.0',
        'pycldf>=1.19.0',
        'termcolor',
        'requests',
        'appdirs',
        'pytest',
        'rfc3986',
        'zenodoclient>=0.3',
        'tqdm',
    ],
    extras_require={
        'excel': [
            'openpyxl',
            'xlrd>=2',
        ],
        'glottolog': ['pyglottolog'],  # Access the Glottolog catalog.
        'concepticon': ['pyconcepticon'],  # Access the Concepticon catalog.
        'clts': ['pyclts'],  # Access the CLTS catalog.
        'dev': ['flake8', 'wheel', 'twine'],
        'test': [
            'pytest>=5',
            'pytest-mock',
            'pytest-cov',
            'coverage>=4.2',
            'pyglottolog>=3.2.2',
            'pyconcepticon',
            'openpyxl',
            'xlrd>=2',
        ],
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
)
