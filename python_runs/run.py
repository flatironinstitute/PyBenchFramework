import os
import sys
import benchmark_tools
import args_handler
import miscellaneous
from independent_runs import serverless_fio
from independent_runs_independent_ranks import independent_ranks
from multi_node import server_fio
from mdtest_wrapper import wrap_mdtest 
from IOR_wrapper import wrap_IOR
from testIOR_wrapper import test_wrap_IOR
from test_mdtest_wrapper import test_wrap_mdtest

var_name = "PyBench_root_dir"

try:
    PyBench_root_dir = os.environ[var_name]
    #print(f"{var_name} = {PyBench_root_dir}")
except KeyError:
    print(f"{var_name} is not set, please set the root directory before running this script.")
    sys.exit(1)

args = args_handler.handle_arguments()

if args['benchmark'] == 'fio-server':
    server_fio(args, PyBench_root_dir)
elif args['benchmark'] == 'fio-serverless':
    serverless_fio(args, PyBench_root_dir)
elif args['benchmark'] == 'fio-independent-ranks':
    independent_ranks(args, PyBench_root_dir)
elif args['benchmark'] == 'mdtest':
    wrap_mdtest(args, PyBench_root_dir)
elif args['benchmark'] == 'testmdtest':
    test_wrap_mdtest(args, PyBench_root_dir)
elif args['benchmark'] == 'newIORTool':
    wrap_IOR(args, PyBench_root_dir)
elif args['benchmark'] =='testIORTool':
    test_wrap_IOR(args, PyBench_root_dir)
