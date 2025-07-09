from mpi4py import MPI
from . import args_handler
from .independent_runs import serverless_fio
from .multi_node import server_fio
from .mdtest_wrapper import wrap_mdtest
from .IOR_wrapper import wrap_IOR
from .testIOR_wrapper import test_wrap_IOR
from .test_mdtest_wrapper import test_wrap_mdtest
import socket


def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    hostname = socket.gethostname()
    print(f"Rank {rank} of {size} running on {hostname}")

    args = args_handler.handle_arguments()
    if args["benchmark"] == "fio-server":
        server_fio(args)
    elif args["benchmark"] == "fio-serverless":
        serverless_fio(args)
    elif args["benchmark"] == "mdtest":
        wrap_mdtest(args)
    elif args["benchmark"] == "testmdtest":
        test_wrap_mdtest(args)
    elif args["benchmark"] == "newIORTool":
        wrap_IOR(args)
    elif args["benchmark"] == "testIORTool":
        test_wrap_IOR(args)
