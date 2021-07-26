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
        version='0.1.0',
    license='LICENSE',
        description='Comet is a simple tool to automate/facilitate automated release cycle.',
        long_description=readme(),
        url='http://github.com/beenum22/comet',
        author='Muneeb Ahmad',
        author_email='muneeb.gandapur@gmail.com',
        entry_points = {
                'console_scripts': ['comet=comet.comet:main']
        },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.6",
        install_requires=[
            "PyCryptodome",
            "colorama",
            "coloredlogs",
            "logging",
            "PyYAML",
            "jsonschema",
            "semver",
            "GitPython",
            "paramiko",
            "requests"
        ],
        zip_safe=False)