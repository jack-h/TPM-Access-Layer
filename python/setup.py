from setuptools import setup

setup(
    name='pyfabil',
    version='0.4',
    packages=['pyfabil', 'pyfabil.base', 'pyfabil.boards', 'pyfabil.plugins'],
    url='https://github.com/lessju/TPM-Access-Layer/tree/master/python',
    license='',
    author='Alessio Magro',
    author_email='alessio.magro@um.edu.mt',
    description='',
    install_requires=['futures', 'enum34'],
    test_suite="pyfabil/tests",
)
