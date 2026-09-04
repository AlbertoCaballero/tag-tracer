from importlib import metadata
from pathlib import Path
import re

PACKAGE_NAME = "tag-tracer"

logo = """
                             -
                          ########
                        ###########.
                      ###############
                    ###################
                   ######################
                 ##########################                 #-                                           ##
               ##############  ##############               ##                                           ##
             ##################################           #######   ########     ###########           #######   ###### #########     #########   #########    ######
           #####################################            ##             ##   ###      ###             ##      ###            ##   ###         ##       ##   ###
          ########################################          ##       ########   ##        ##   ######    ##      ##       ########  ###         #############  ##
         ##########################################         ##     -##     ##   ##        ##             ##      ##     ###     ##  ###         ###            ##
         ###########  ################  ##########-         ##     ##      ##    ###     ###             ##      ##     ##     ###   ###     -#  ###           ##
          ########  #################### .########          ######  #########      ###### ##             ######  ##      #########     ########    ########    ##
                  #######################+                                                ##
                 ##########################                                      ##########
                 ###########   ############                                         ####
                  ########       #########
                    ####           +####
"""


def get_version() -> str:
    """
    Returns the project version from the installed package metadata,
    falling back to pyproject.toml when running from a source checkout
    (e.g. in tests before the package is installed).
    """
    try:
        return metadata.version(PACKAGE_NAME)
    except metadata.PackageNotFoundError:
        pyproject = Path(__file__).resolve().parents[3] / "pyproject.toml"
        match = re.search(
            r'^version\s*=\s*["\']([^"\']+)["\']', pyproject.read_text(), re.M
        )
        return match.group(1) if match else "unknown"


def version():
    print(logo)
    print(f"TagTracer version {get_version()} (development preview)")
