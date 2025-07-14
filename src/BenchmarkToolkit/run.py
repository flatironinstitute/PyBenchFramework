from . import args_handler
from .independent_runs import serverless_fio
from .independent_runs_independent_ranks import independent_ranks
from .multi_node import server_fio
from .mdtest_wrapper import wrap_mdtest
from .IOR_wrapper import wrap_IOR
from .testIOR_wrapper import test_wrap_IOR
from .test_mdtest_wrapper import test_wrap_mdtest
from mpi4py import MPI

benchmark_funcs = {
    "fio-server": server_fio,
    "fio-serverless": serverless_fio,
    "fio-independent-ranks": independent_ranks,
    "mdtest": wrap_mdtest,
    "testmdtest": test_wrap_mdtest,
    "newIORTool": wrap_IOR,
    "testIORTool": test_wrap_IOR,
}
available_benchmarks = ", ".join(benchmark_funcs.keys())


def _finalize_and_fail():
    MPI.Finalize()
    return 1


def main():
    args = args_handler.handle_arguments()
    if "benchmark" not in args:
        print("No benchmark specified. Please provide a benchmark name.")
        print(f"Available benchmarks are: {available_benchmarks}.")
        return _finalize_and_fail()

    try:
        benchmark_funcs[args["benchmark"]](args)
    except KeyError:
        err_str = (
            f"Invalid benchmark specified: {args['benchmark']}. "
            f"Available benchmarks are: {available_benchmarks}."
        )
        print(err_str)
        return _finalize_and_fail()
    except Exception as _:
        import traceback
        print(f"An error occurred while running the benchmark:\n{traceback.format_exc()}")
        return _finalize_and_fail()

    return 0
