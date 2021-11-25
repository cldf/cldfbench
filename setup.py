from setuptools import setup, find_packages


setup(
    name='cldfbench',
    version='1.9.0',
    author='Robert Forkel',
    author_email='dlce.rdm@eva.mpg.de',
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
        'clldutils>=3.9.0',
        'cldfcatalog>=1.3',
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
        'odf': ['odfpy'],
        'excel': [
            'openpyxl',
            'xlrd>=2',
        ],
        'glottolog': ['pyglottolog'],  # Access the Glottolog catalog.
        'concepticon': ['pyconcepticon'],  # Access the Concepticon catalog.
        'clts': ['pyclts'],  # Access the CLTS catalog.
        'dev': ['flake8', 'wheel', 'twine', 'tox'],
        'test': [
            'pytest>=5',
            'pytest-mock',
            'pytest-cov',
            'coverage>=4.2',
            'pyglottolog>=3.2.2',
            'pyconcepticon',
            'odfpy',
            'openpyxl',
            'xlrd>=2',
        ],
       'docs': [
            'sphinx',
            'sphinx-autodoc-typehints',
            'sphinx-rtd-theme',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
)
