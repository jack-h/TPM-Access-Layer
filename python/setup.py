from setuptools import setup

setup(
    name='pyfabil',
    version='0.4',
    packages=['pyfabil', 'pyfabil.base', 'pyfabil.boards', 'pyfabil.plugins',
              'pyfabil.tests', 'pyfabil.plugins.uniboard', 'pyfabil.plugins.tpm'],
    url='https://github.com/lessju/TPM-Access-Layer/tree/master/python',
    license='',
    author='Alessio Magro',
    author_email='alessio.magro@um.edu.mt',
    description='',
    install_requires=['futures', 'enum34'],
    test_suite="pyfabil/tests",
)
