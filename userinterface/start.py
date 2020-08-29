import os
import sys

package_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(package_path, ".."))

import argparse
from controller.manager import *

parser = argparse.ArgumentParser()

parser.add_argument("-s", "--setting", type=str, dest="setting",
                    help="The Base Test Setting Path", required=True)
parser.add_argument("-t", "--testlist", type=str, dest="testlist",
                    help="Test list file", required=True)
parser.add_argument("-r", "--resource", type=str, dest="resource",
                    help="Test Resource file", required=True)
parser.add_argument("-u", "--user", type=str, dest="user",
                    help="User Name", required=True)

args = parser.parse_args()

load_settings(args.setting)
init_engine()
load_resource(args.resource, args.user)
load_test_list(args.testlist)


if __name__ == '__main__':
    run_test()
