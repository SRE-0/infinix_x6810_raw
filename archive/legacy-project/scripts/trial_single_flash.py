"""Ten-minute reversible SINGLE trial with explicit device selection."""
import argparse,subprocess
import trial_native_torch as trial
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--serial',required=True)
p.add_argument('--stop',action='store_true')
a=p.parse_args()
trial.OUT=trial.ROOT/'patches/single-flash-trial'
trial.REMOTE='/data/local/tmp/x6810-single-trial'
trial.TARGETS={k:v for k,v in trial.TARGETS.items() if k!='libmtkcam_device3_hal.so'}
trial.adb=lambda *args:subprocess.run(['adb','-s',a.serial,*args],check=True)
if a.stop:trial.adb('shell','su','-c','touch '+trial.REMOTE+'/stop')
else:trial.main()
