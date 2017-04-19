'''
Created on Sep 12, 2013

@author: u0490822
'''

import sys

if not hasattr(sys, 'frozen'):
    import wxversion
    wxversion.select('2.8')

from pyre import state
import launcher

if __name__ == '__main__':
    state.init()
    launcher.Run()