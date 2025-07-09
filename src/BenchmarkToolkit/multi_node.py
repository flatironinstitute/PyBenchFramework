import sys
from pathlib import Path

from . import benchmark_tools
from . import handler_class


def server_fio(args):
    job_number = args["slurm_job_number"]

    fio_ob_dict = {}

    proc = benchmark_tools.split_arg_sequence(args["job_number"], "--job-number")
    nodes = benchmark_tools.split_arg_sequence(str(args["node_count"]), "--node-count")

    set_noscrub = args["no_scrub"]

    if args["split_hosts_file"]:
        benchmark_tools.create_node_list_file(
            args["node_count"], args["hosts_file"], job_number
        )

    config_template_path = args["template_path"]

    with open(config_template_path, "r") as file:
        original_file_contents = file.read()

    fio_scrub = handler_class.FIOTool()

    if set_noscrub == 1:
        fio_scrub.set_noscrub()

    log_dir = Path("results", args["io_type"], args["platform_type"], job_number)
    command_log_dir = log_dir.joinpath("commands")

    log_dir.mkdir(parents=True, exist_ok=True)
    command_log_dir.mkdir(parents=True, exist_ok=True)
    for node_count in nodes:
        for job_count in proc:
            file_count = job_count

            # Reset file_contents to the original template for each iteration
            file_contents = original_file_contents
            file_contents = file_contents.replace("__block_size__", args["block_size"])
            file_contents = file_contents.replace("__number_of_jobs__", f"{job_count}")
            file_contents = file_contents.replace("__dir_var__", args["directory"])
            file_contents = file_contents.replace("__io_type_var__", args["io_type"])
            file_contents = file_contents.replace("__time_var__", f"{args['time']}")

            fio_path = Path(
                "examples",
                "test_files",
                f"multinode_{job_count}p_{file_count}f_{args['block_size']}_{args['io_type']}.fio",
            )
            with open(
                fio_path,
                "w",
            ) as file:
                file.write(file_contents)

            fio_ob_key = f"{node_count}n_{job_count}p_{file_count}f_{args['io_type']}"
            fio_ob = fio_ob_dict[fio_ob_key] = handler_class.FIOTool()

            fio_ob.setup_command(
                config_file=fio_path,
                output_format="json",
                output_file=f"{log_dir}/{node_count}n_{job_count}p_{file_count}f_{args['block_size']}.json",
                host_file=f"host_files/{job_number}_{node_count}_hosts.file",
            )

            command_file_path = Path(
                command_log_dir,
                f"{job_number}_{node_count}n_{job_count}p_{file_count}f_{args['platform_type']}_command",
            )
            with open(
                command_file_path,
                "a",
            ) as file:
                file.write(f"num nodes is {node_count}, job number is {job_count}")
                tmp_cmd_string = ""
                for cmd_el in fio_ob.command:
                    tmp_cmd_string += f" {cmd_el}"
                file.write(tmp_cmd_string)

            fio_ob.run()

            print(
                f"Job num: {job_count}, node count: {node_count}. Iteration is finished."
            )
            sys.stdout.flush()

    if set_noscrub == 1:
        fio_scrub.set_scrub()
