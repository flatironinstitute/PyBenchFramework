from . import handler_class
import sys
import yaml
from . import benchmark_tools
from . import miscellaneous
import re


def test_wrap_IOR(args):
    job_number = args["slurm_job_number"]

    log_dir = f"results/iortest/{args['io_type']}/{args['platform_type']}/{job_number}"
    command_log_dir = f"{log_dir}/commands"

    required_args = [
        "config",
        "mpi_ranks",
        "node_count",
        "blockSize",
        "filename",
        "transferSize",
        "segmentCount",
    ]
    for i in required_args:
        if i not in args:
            arg_string = i.replace("_", "-")
            print(
                f"Missing option --{arg_string}. Please look at IOR and/or MPI documentation and fix this error."
            )
            sys.exit()
        elif not args[i]:
            arg_string = i.replace("_", "-")
            print(
                f"Incorrect --{arg_string} usage. Please look at IOR and/or MPI documentation and fix this error."
            )
            sys.exit()

    print("Required arguments seem valid...")

    config_file = args["config"]
    print(config_file)

    if config_file:
        try:
            with open(config_file, "r") as opts_file:
                config = yaml.safe_load(opts_file)
        except Exception as e:
            print(f'Exception while processing config file\n {e}')
            sys.exit(1)
    else:
        raise ValueError("Configuration file must be specified. IOR...")

    for key, value in config.items():
        if key != "config_options" and key != "command_extensions":
            print(f"{key}: {value}")
        if key == "config_options":
            print("Configuration options:")
            for key, value in config["config_options"].items():
                print(f"{key}: {value}")
        if key == "command_extensions":
            print("Command extensions:")
            for i in config["command_extensions"]:
                print(f"{i}")

    if "job_note" in args.keys():
        with open(f"{log_dir}/job_note.txt", "w") as file:
            file.write(args["job_note"])

    mpi_ranks = list(
        benchmark_tools.split_arg_sequence(args["mpi_ranks"], "--mpi-ranks")
    )
    filename = args["filename"]
    node_count = list(
        benchmark_tools.split_arg_sequence(args["node_count"], "--node-count")
    )
    ior_obj_dict = {}

    print(f"SEQUENCES ARE {mpi_ranks} and nodes {node_count}")
    for nodes in node_count:
        for ranks in mpi_ranks:
            print(
                f"BEGINNING OF LOOPS ---------------------- ranks per node: {ranks} and nodes: {nodes}"
            )

            if "unit_restart" in args:
                if args["unit_restart"] == 1:
                    pattern = "/"
                    split_dir = re.split(pattern, filename)
                    cephtest_root = "/" + split_dir[1] + "/" + split_dir[2]
                    miscellaneous.restart_ceph_unit(cephtest_root)

            total_ranks = ranks * nodes
            print(f"TOTAL RANKS ARE {total_ranks}")
            output_file = f"{log_dir}/ranks_per_node_{ranks}_node_count_{nodes}"

            ior_obj_dict[f"{ranks}_{nodes}"] = handler_class.test_ior_tool()
            ior_obj_dict[f"{ranks}_{nodes}"].setup_command(
                config=config,
                mpi_ranks=total_ranks,
                ranks_per_node=ranks,
                output_file=output_file,
            )

            with open(f"{command_log_dir}/command_ior_{ranks}_{nodes}", "w") as file:
                tmp_cmd_string = ""
                for cmd_el in ior_obj_dict[f"{ranks}_{nodes}"].command:
                    tmp_cmd_string += f" {cmd_el}"
                file.write(tmp_cmd_string)

            ior_obj_dict[f"{ranks}_{nodes}"].run()
