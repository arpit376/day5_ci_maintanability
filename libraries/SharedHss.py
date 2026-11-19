"""SharedHss: a deliberately SHARED resource, to show why parallel runs fail (module 5.2).

In a real lab the shared thing is the subscriber database, an eNodeB port, or the core.
Here a claim file per IMSI in the system temp folder stands for "this subscriber is in use".
Two workers claiming the same IMSI at the same time collide, exactly like two tests
attaching the same SIM.
"""
import os
import tempfile

from robot.api.deco import keyword, library

ROOT = os.path.join(tempfile.gettempdir(), "lte_lab_shared_hss")


def _alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


@library(scope="GLOBAL", auto_keywords=False)
class SharedHss:

    @keyword("Claim Subscriber")
    def claim_subscriber(self, imsi):
        """Mark the IMSI as in use. Fails if another running process already holds it."""
        os.makedirs(ROOT, exist_ok=True)
        path = os.path.join(ROOT, imsi)
        for _ in range(2):
            try:
                fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                return
            except FileExistsError:
                try:
                    owner = int(open(path).read() or 0)
                except (OSError, ValueError):
                    owner = 0
                if owner and owner != os.getpid() and _alive(owner):
                    raise AssertionError(
                        f"IMSI {imsi} is already in use by process {owner}. "
                        "Parallel tests share one subscriber: give each worker its own IMSI range.")
                try:
                    os.remove(path)            # stale claim of a dead process
                except OSError:
                    pass
        raise AssertionError(f"Could not claim IMSI {imsi}")

    @keyword("Release Subscriber")
    def release_subscriber(self, imsi):
        path = os.path.join(ROOT, imsi)
        try:
            if int(open(path).read() or 0) == os.getpid():   # only the owner releases
                os.remove(path)
        except (OSError, ValueError):
            pass
