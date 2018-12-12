from setuptools import find_packages, setup

setup(
    name="ndoh-hub",
    version="0.5.0",
    url="http://github.com/praekeltfoundation/ndoh-hub",
    license="BSD",
    author="Praekelt Foundation",
    author_email="dev@praekeltfoundation.org",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Django==2.1.2",
        "djangorestframework==3.8.2",
        "coreapi==2.3.3",
        "dj-database-url==0.5.0",
        "psycopg2==2.7.5",
        "raven==6.9.0",
        "django-filter==2.0.0",
        "celery==4.2.1",
        "six==1.11.0",
        "django-rest-hooks==1.5.0",
        "requests==2.18.4",
        "seed-services-client==0.37.0",
        "demands==3.0.0",
        "structlog==18.2.0",
        "phonenumberslite==8.9.15",
        "django-simple-history==2.4.0",
        "openpyxl==2.5.9",
        "iso-639==0.4.5",
        "django-prometheus=1.0.15",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Django",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
