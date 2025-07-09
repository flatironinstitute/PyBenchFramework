from pathlib import Path

from BenchmarkToolkit.args_handler import handle_arguments


def main():
    args = handle_arguments()
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
