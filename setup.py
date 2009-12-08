
from distutils.core import setup

import promise

NAME = "promise"
VERSION = promise.__version__
DESCRIPTION = "bytecode optimisation using staticness assertions."
AUTHOR = "Ryan Kelly"
AUTHOR_EMAIL = "ryan@rfk.id.au"
URL = "http://github.com/rfk/promise/"
LICENSE = "MIT"
KEYWORDS = "optimise optimize bytecode"
LONG_DESC = promise.__doc__

PACKAGES = ["promise","promise.tests"]
EXT_MODULES = []
PKG_DATA = {}

setup(name=NAME,
      version=VERSION,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      url=URL,
      description=DESCRIPTION,
      long_description=LONG_DESC,
      keywords=KEYWORDS,
      packages=PACKAGES,
      ext_modules=EXT_MODULES,
      package_data=PKG_DATA,
      license=LICENSE,
      test_suite="nose.collector",
     )

