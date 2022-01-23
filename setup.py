import setuptools
import time

setuptools.setup(
    name='backend',
    version="0.0" + str(time.time()),
    packages=setuptools.find_packages(),
    url='',
    license='',
    author='Imperial22',
    author_email='',
    description='Back-end services for crypto payment sales funnel.'
)
