from mpi4py import MPI
from pathlib import Path

from . import args_handler
from .independent_runs import serverless_fio
from .independent_runs_independent_ranks import independent_ranks
from .multi_node import server_fio
from .mdtest_wrapper import wrap_mdtest
from .IOR_wrapper import wrap_IOR
from .testIOR_wrapper import test_wrap_IOR
from .test_mdtest_wrapper import test_wrap_mdtest


_benchmark_funcs = {
    "fio-server": server_fio,
    "fio-serverless": serverless_fio,
    "fio-independent-ranks": independent_ranks,
    "mdtest": wrap_mdtest,
    "testmdtest": test_wrap_mdtest,
    "newIORTool": wrap_IOR,
    "testIORTool": test_wrap_IOR,
}
_available_benchmarks = ", ".join(_benchmark_funcs.keys())


def _finalize_and_fail():
    MPI.Finalize()
    return 1


def _prepare_environment(args):
    job_number = str(args["slurm_job_number"])

    if args["benchmark"] in ("newIORTool", "testIORTool"):
        log_dir = Path(
            "results", "iortest", args["io_type"], args["platform_type"], job_number
        )
    elif args["benchmark"] == "testmdtest":
        log_dir = Path(
            "results",
            args["not_taken_into_account"]["io_type"],
            args["not_taken_into_account"]["platform_type"],
            job_number,
        )
    else:
        log_dir = Path("results", args["io_type"], args["platform_type"], job_number)

    log_dir.joinpath("commands").mkdir(parents=True, exist_ok=True)
    log_dir.joinpath("tmp_files").mkdir(parents=True, exist_ok=True)
    Path("network_stats", job_number).mkdir(parents=True, exist_ok=True)
    Path("examples", "test_files").mkdir(parents=True, exist_ok=True)

    try:
        with open(log_dir.joinpath("hostname_mapping.txt"), "x") as _:
            print("Hostname mapping file created.")
    except FileExistsError:
        print("Warning: Hostname mapping file already exists.")


def main():
    args = args_handler.handle_arguments()
    if "benchmark" not in args:
        print("No benchmark specified. Please provide a benchmark name.")
        print(f"Available benchmarks are: {_available_benchmarks}.")
        return _finalize_and_fail()

    if args["benchmark"] not in _benchmark_funcs.keys():
        err_str = (
            f"Invalid benchmark specified: {args['benchmark']}. "
            f"Available benchmarks are: {_available_benchmarks}."
        )
        print(err_str)
        return _finalize_and_fail()

    if MPI.COMM_WORLD.Get_rank() == 0:
        _prepare_environment(args)

    MPI.COMM_WORLD.Barrier()

    try:
        _benchmark_funcs[args["benchmark"]](args)
    except Exception as _:
        import traceback

        print(
            f"An error occurred while running the benchmark:\n{traceback.format_exc()}"
        )
        return _finalize_and_fail()

    MPI.Finalize()
    return 0
