from distutils.core import setup
import os, glob

execfile(os.path.join('pyfusion','version.py'))
setup(name='pyfusion',
      version=__version__,
      packages=['pyfusion'],
      package_data={'pyfusion':['pyfusion.cfg',
                                os.path.join('acquisition', 'DSV', '*.dat'),
                                os.path.join('acquisition', 'LHD', '*.npz'),
                                os.path.join('acquisition', 'MDSPlus', '*.cfg'),
                                os.path.join('acquisition', 'MDSPlus', 'test_tree', '*'),
                                os.path.join('conf', '*.cfg'),
                                os.path.join('devices', '*', '*.cfg'),
                                os.path.join('documentation', 'README'),
                                os.path.join('documentation', 'Makefile'),
                                os.path.join('documentation', '*.rst'),
                                os.path.join('documentation', '*', '*.rst'),
                                os.path.join('documentation', '*', '*', '*.rst'),
                                os.path.join('test', '*.cfg')]}
            )
