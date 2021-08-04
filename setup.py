from setuptools import setup, find_packages


def readme():
    with open('README.rst') as f:
        return f.read()


def get_requirements():
    """
    lists the requirements to install.
    """
    pkgs = []
    links = []
    requirements = []
    try:
        with open('requirements.txt') as f:
            requirements = f.read().splitlines()
        for r in requirements:
            if "git+git" in r:
                links.append(r)
            else:
                pkgs.append(r)
    except Exception as ex:
        raise Exception("Error parsing requirements.txt. Check its availability.")
    return pkgs, links


pkgs, links = get_requirements()

setup(
    name='comet',
    version='0.2.0-dev.7',
    license='LICENSE',
    description='Comet is a simple tool to automate/facilitate automated release cycle.',
    long_description=readme(),
    url='http://github.com/beenum22/comet',
    author='Muneeb Ahmad',
    author_email='muneeb.gandapur@gmail.com',
    entry_points = {
            'console_scripts': ['comet=comet.cli:main']
    },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.6",
    install_requires=[
        "colorama==0.4.4",
        "coloredlogs==15.0.1",
        "PyYAML==5.1",
        "jsonschema==3.2.0",
        "semver==3.0.0.dev2",
        "GitPython==3.1.18",
        "paramiko==2.7.2",
        "requests==2.25.0"
    ],
    zip_safe=False
)