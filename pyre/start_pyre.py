'''
Created on Sep 12, 2013

@author: u0490822
'''

if __name__ == '__main__':
    print("Starting Pyre")
    import pyre
    import os
    
    profiler = None

    if 'PROFILE' in os.environ:
        profile_val = os.environ['PROFILE'] 
        if len(profile_val) > 0 and profile_val != '0':
            import cProfile
            print("Starting profiler because PROFILE environment variable is defined") 
            profiler = cProfile.Profile()
            profiler.enable()
        
    pyre.Run()
    
    if not profiler is None:
        profiler.dump_stats("C:\Temp\pyre.profile")