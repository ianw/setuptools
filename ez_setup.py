#!python
"""Bootstrap distribute installation

If you want to use setuptools in your package's setup.py, just include this
file in the same directory with it, and add this to the top of your setup.py::

    from ez_setup import use_setuptools
    use_setuptools()

If you want to require a specific version of setuptools, set a download
mirror, or use an alternate download directory, you can do so by supplying
the appropriate options to ``use_setuptools()``.

This file can also be run as a script to install or upgrade setuptools.
"""
import sys
import os
import shutil
import time

is_jython = sys.platform.startswith('java')
if is_jython:
    import subprocess

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

DEFAULT_VERSION = "0.6"
#DEFAULT_URL     = "http://pypi.python.org/packages/%s/d/distribute/" % sys.version[:3]
DEFAULT_URL     = "http://bitbucket.org/tarek/distribute/downloads/"

md5_data = {
    'distribute-0.6-py2.3.egg': '2bf26bffe3d8c910de396d45c0f0a24f',
    'distribute-0.6-py2.4.egg': 'c01b1355a5f48344c1c78149f59f68a6',
    'distribute-0.6-py2.5.egg': '2ac319d801bce820a370647916eec84c',
    'distribute-0.6-py2.6.egg': 'fa7906f9caa2c1f0a56daf486bab1583',
}

def _validate_md5(egg_name, data):
    if egg_name in md5_data:
        digest = md5(data).hexdigest()
        if digest != md5_data[egg_name]:
            print >>sys.stderr, (
                "md5 validation of %s failed!  (Possible download problem?)"
                % egg_name
            )
            sys.exit(2)
    return data

def use_setuptools(
    version=DEFAULT_VERSION, download_base=DEFAULT_URL, to_dir=os.curdir,
    download_delay=15
):
    """Automatically find/download setuptools and make it available on sys.path

    `version` should be a valid setuptools version number that is available
    as an egg for download under the `download_base` URL (which should end with
    a '/').  `to_dir` is the directory where setuptools will be downloaded, if
    it is not already available.  If `download_delay` is specified, it should
    be the number of seconds that will be paused before initiating a download,
    should one be required.  If an older version of setuptools is installed,
    this routine will print a message to ``sys.stderr`` and raise SystemExit in
    an attempt to abort the calling script.
    """
    was_imported = 'pkg_resources' in sys.modules or 'setuptools' in sys.modules
    def do_download():
        egg = download_setuptools(version, download_base, to_dir, download_delay)
        sys.path.insert(0, egg)
        import setuptools; setuptools.bootstrap_install_from = egg
    try:
        import pkg_resources
        if not hasattr(pkg_resources, '_distribute'):
            raise ImportError
    except ImportError:
        return do_download()
    try:
        pkg_resources.require("distribute>="+version); return
    except pkg_resources.VersionConflict, e:
        if was_imported:
            print >>sys.stderr, (
            "The required version of distribute (>=%s) is not available, and\n"
            "can't be installed while this script is running. Please install\n"
            " a more recent version first, using 'easy_install -U distribute'."
            "\n\n(Currently using %r)"
            ) % (version, e.args[0])
            sys.exit(2)
        else:
            del pkg_resources, sys.modules['pkg_resources']    # reload ok
            return do_download()
    except pkg_resources.DistributionNotFound:
        return do_download()

def download_setuptools(
    version=DEFAULT_VERSION, download_base=DEFAULT_URL, to_dir=os.curdir,
    delay = 15
):
    """Download distribute from a specified location and return its filename

    `version` should be a valid distribute version number that is available
    as an egg for download under the `download_base` URL (which should end
    with a '/'). `to_dir` is the directory where the egg will be downloaded.
    `delay` is the number of seconds to pause before an actual download attempt.
    """
    import urllib2, shutil
    egg_name = "distribute-%s-py%s.egg" % (version,sys.version[:3])
    url = download_base + egg_name
    saveto = os.path.join(to_dir, egg_name)
    src = dst = None
    if not os.path.exists(saveto):  # Avoid repeated downloads
        try:
            from distutils import log
            if delay:
                log.warn("""
---------------------------------------------------------------------------
This script requires distribute version %s to run (even to display
help).  I will attempt to download it for you (from
%s), but
you may need to enable firewall access for this script first.
I will start the download in %d seconds.

(Note: if this machine does not have network access, please obtain the file

   %s

and place it in this directory before rerunning this script.)
---------------------------------------------------------------------------""",
                    version, download_base, delay, url
                ); from time import sleep; sleep(delay)
            log.warn("Downloading %s", url)
            src = urllib2.urlopen(url)
            # Read/write all in one block, so we don't create a corrupt file
            # if the download is interrupted.
            data = _validate_md5(egg_name, src.read())
            dst = open(saveto,"wb"); dst.write(data)
        finally:
            if src: src.close()
            if dst: dst.close()
    return os.path.realpath(saveto)


SETUPTOOLS_PKG_INFO  = """\
Metadata-Version: 1.0
Name: setuptools
Version: 0.6c9
Summary: xxxx
Home-page: xxx
Author: xxx
Author-email: xxx
License: xxx
Description: xxx
"""

def fake_setuptools():
    try:
        import pkg_resources
    except ImportError:
        # we're cool
        return
    ws  = pkg_resources.working_set
    setuptools_dist = ws.find(pkg_resources.Requirement.parse('setuptools'))
    if setuptools_dist is None:
        return
    # detecting if it was already faked
    setuptools_location = setuptools_dist.location
    pkg_info = os.path.join(setuptools_location, 'EGG-INFO', 'PKG-INFO')
    if os.path.exists(pkg_info):
        content = open(pkg_info).read()
        if SETUPTOOLS_PKG_INFO == content:
            # already patched
            return

    # let's create a fake egg replacing setuptools one
    os.rename(setuptools_location, setuptools_location+'.OLD.%s' % time.time())
    os.mkdir(setuptools_location)
    os.mkdir(os.path.join(setuptools_location, 'EGG-INFO'))
    pkg_info = os.path.join(setuptools_location, 'EGG-INFO', 'PKG-INFO')
    f = open(pkg_info, 'w')
    try:
        f.write(SETUPTOOLS_PKG_INFO)
    finally:
        f.close()

    # we have to relaunch the process
    args = [sys.executable]  + sys.argv
    if is_jython:
        sys.exit(subprocess.Popen([sys.executable] + args).wait())
    else:
        sys.exit(os.spawnv(os.P_WAIT, sys.executable, args))

def main(argv, version=DEFAULT_VERSION):
    """Install or upgrade setuptools and EasyInstall"""

    # let's deactivate any existing setuptools installation first
    fake_setuptools()

    try:
        import setuptools
        # we need to check if the installed setuptools
        # is from Distribute or from setuptools
        if not hasattr(setuptools, '_distribute'):
            # now we are ready to install distribute
            raise ImportError
    except ImportError:
        egg = None
        try:
            egg = download_setuptools(version, delay=0)
            sys.path.insert(0, egg)
            from setuptools.command import easy_install
            return easy_install.main(list(argv)+['-v']+[egg])
        finally:
            if egg and os.path.exists(egg):
                os.unlink(egg)
    else:
        if setuptools.__version__ == '0.0.1':
            print >>sys.stderr, (
            "You have an obsolete version of setuptools installed.  Please\n"
            "remove it from your system entirely before rerunning this script."
            )
            sys.exit(2)

    req = "distribute>="+version
    import pkg_resources
    try:
        pkg_resources.require(req)
    except pkg_resources.VersionConflict:
        try:
            from setuptools.command.easy_install import main
        except ImportError:
            from easy_install import main
        main(list(argv)+[download_setuptools(delay=0)])
        sys.exit(0) # try to force an exit
    else:
        if argv:
            from setuptools.command.easy_install import main
            main(argv)
        else:
            print "distribute version",version,"or greater has been installed."
            print '(Run "ez_setup.py -U distribute" to reinstall or upgrade.)'

def update_md5(filenames):
    """Update our built-in md5 registry"""

    import re

    for name in filenames:
        base = os.path.basename(name)
        f = open(name,'rb')
        md5_data[base] = md5(f.read()).hexdigest()
        f.close()

    data = ["    %r: %r,\n" % it for it in md5_data.items()]
    data.sort()
    repl = "".join(data)

    import inspect
    srcfile = inspect.getsourcefile(sys.modules[__name__])
    f = open(srcfile, 'rb'); src = f.read(); f.close()

    match = re.search("\nmd5_data = {\n([^}]+)}", src)
    if not match:
        print >>sys.stderr, "Internal error!"
        sys.exit(2)

    src = src[:match.start(1)] + repl + src[match.end(1):]
    f = open(srcfile,'w')
    f.write(src)
    f.close()


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--md5update':
        update_md5(sys.argv[2:])
    else:
        main(sys.argv[1:])

