import sys
sys.path.insert(0, ".")

from scripts.reloader import *

if on_mac():
    if addon.exists(): addon.unlink()
    subprocess.run(["ln", "-s", reloader, addon])
    sys.stdout.write(str(blender_executable))