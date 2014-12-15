#! /usr/bin/env python

import sys
import os
import atexit

def install_setuptools():
    import setuptools_install
    ret = setuptools_install.main()
    sys.exit(ret)

def main(argv=None):
    #c = raw_input('Press any key to continue')
    #os.putenv('LAPACK', './')
    #os.putenv('ATLAS', './')
    #os.putenv('BLAS', './')

    #atexit.register(install_modules)

    #install_setuptools()

    install_modules()

def install_modules():
    import easy_install
    easy_install.main(['statsmodels', 'pyparse', 'matplotlib', 'pandas', 'ggplot', 'six', 'Pmw', 'Pillow', 'openpyxl'])
    #raw_input('Press any key to exit')

if __name__ == '__main__':
    main(sys.argv)
