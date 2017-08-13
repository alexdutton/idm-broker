from setuptools import setup, find_packages

setup(
    name='idm-notification',
    version='0.1',
    description='Small Django app pushing model changes to kombu',
    #long_description=open('README.md').read(),
    author='Alexander Dutton',
    author_email='idm@alexdutton.co.uk',
    url='https://github.com/alexsdutton/idm-notification',
    license='BSD',
    packages=find_packages(exclude=("test*", )),
    install_requires=['kombu', 'djangorestframework', 'django-dirtyfields'],
)
