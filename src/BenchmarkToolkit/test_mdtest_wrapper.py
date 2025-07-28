import os
from . import handler_class
from datetime import datetime
import sys
from . import benchmark_tools
from . import miscellaneous
import re
import subprocess


def test_wrap_mdtest(args):
    job_number = args["slurm_job_number"]

    mdtest_obj_dict = {}

    log_dir = f"results/{args['not_taken_into_account']['io_type']}/{args['not_taken_into_account']['platform_type']}/{job_number}"
    command_log_dir = f"{log_dir}/commands"
    directory = args["mdtest_opts"]["directory"]

    if args["not_taken_into_account"]["timed"]:
        times = sorted(
            benchmark_tools.split_arg_sequence(
                args["not_taken_into_account"]["timed"], "--timed"
            )
        )
        if len(times) != 2:
            print(
                f"{datetime.now().strftime('%b %d %H:%M:%S')} When using the 'timed' option, please ensure to specify two comma-delimited integer values indicating a lower threshold and upper threshold of time in seconds that the test should run for. Values as interpreted are: {times}"
            )
            sys.exit()

    if "job_note" in args["not_taken_into_account"].keys():
        job_note = f"{args['not_taken_into_account']['job_note']}"
        with open(f"{log_dir}/job_note.txt", "w") as file:
            file.write(job_note)
    else:
        print(
            "{datetime.now().strftime('%b %d %H:%M:%S')} Job note required for job tracking. Please include an argument under the \"not_taken_into_account\" YAML dict"
        )
        sys.exit()

    # If the "--in-parts" argument is used, we will break out into a separate a logical branch. This new branch may become the main branch and the old logic may take the place of the current logic. Whatever parts of the old code that can be recycled, should be?
    if "not_taken_into_account" in args.keys():
        print("in not_taken_into_account")
        if "in_parts" in args["not_taken_into_account"].keys():
            if args["not_taken_into_account"]["in_parts"]:
                print("in in_parts")
                # for each iteratable element in  general_opts and mdtest_opts I want a counter, a way to iterate over it (so maybe a key), and the sub-elements. EXCEPT command-extensions:
                result_dict = {}
                combined_opts = {**args["general_opts"], **args["mdtest_opts"]}

                for key, value in combined_opts.items():
                    if (
                        isinstance(value, str) and "," in value
                    ):  # Handle comma-separated strings
                        value_list = list(value.split(","))
                    else:  # Handle single values or non-comma-separated strings
                        value_list = [value]
                    if key == "command_extensions":
                        pass

                    result_dict[key] = {
                        key: value_list,
                        "counter": len(value_list) - 1,
                        "tmp_counter": len(value_list) - 1,
                    }

                for node in result_dict["node_count"]["node_count"]:
                    for rank in result_dict["mpi_ranks"]["mpi_ranks"]:
                        tmp_rank = int(rank)
                        tmp_node = int(node)
                        tmp_rank = tmp_node * tmp_rank
                        ranks_per_node = int(tmp_rank / tmp_node)

                        universal_key_counter = 1
                        for key, value in result_dict.items():
                            value["tmp_counter"] = value["counter"]

                        files_per_rank = int(
                            int(
                                result_dict["files_per_rank"]["files_per_rank"][
                                    result_dict["files_per_rank"]["tmp_counter"]
                                ]
                            )
                            / int(tmp_rank)
                        )

                        while universal_key_counter != 0:
                            universal_key_counter = 0
                            tmp_result_dict = {}
                            for command_extent_element in reversed(
                                result_dict["command_extensions"]["command_extensions"]
                            ):
                                if (
                                    "unit_restart"
                                    in args["not_taken_into_account"].keys()
                                ):
                                    if (
                                        args["not_taken_into_account"]["unit_restart"]
                                        == 1
                                    ):
                                        pattern = "/"
                                        split_dir = re.split(pattern, directory)
                                        FS_root = (
                                            "/" + split_dir[1] + "/" + split_dir[2]
                                        )
                                        miscellaneous.restart_ceph_unit(FS_root)

                                # Set temporary values for the current loop and the output file
                                for key2, value2 in result_dict.items():
                                    if key2 == "command_extensions":
                                        tmp_result_dict["command_extensions"] = (
                                            command_extent_element
                                        )
                                    else:
                                        tmp_result_dict[f"{key2}"] = value2[f"{key2}"][
                                            value2["tmp_counter"]
                                        ]

                                config = {
                                    **tmp_result_dict,
                                    **args["not_taken_into_account"],
                                }

                                out_file = f"{log_dir}/mdtest_output_{command_extent_element}_{tmp_node}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank"
                                # Print statistics
                                print(
                                    f"{datetime.now().strftime('%b %d %H:%M:%S')} ranks per node are {ranks_per_node}, nodes are {tmp_node}, and mdtest job type is {command_extent_element}"
                                )
                                # ---------

                                # Create mdtest object
                                mdtest_obj_dict[
                                    f"{command_extent_element}_{tmp_node}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank"
                                ] = handler_class.mdtestTool()
                                mdtest_obj_dict[
                                    f"{command_extent_element}_{tmp_node}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank"
                                ].setup_command(
                                    config=config,
                                    config_file=f"{args['config']}",
                                    mpi_ranks=f"{tmp_rank}",
                                    files_per_rank=f"{files_per_rank}",
                                    directory=f"{directory}",
                                    output_file=out_file,
                                    ranks_per_node=f"{ranks_per_node}",
                                    write_output=args["mdtest_opts"]["write_output"],
                                )

                                # Write command into command output file
                                with open(
                                    f"{command_log_dir}/mdtest_{command_extent_element}_{tmp_node}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank",
                                    "a",
                                ) as file:
                                    file.write("The following is the mdtest command")
                                    tmp_cmd_string = ""
                                    for cmd_el in mdtest_obj_dict[
                                        f"{command_extent_element}_{tmp_node}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank"
                                    ].command:
                                        tmp_cmd_string += f" {cmd_el}"
                                    file.write(tmp_cmd_string)
                                # ---------

                                # Run mdtest through object and enter optimizer as necessary
                                mdtest_obj_dict[
                                    f"{command_extent_element}_{tmp_node}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank"
                                ].run()
                                print(
                                    "Does this object exist?, ",
                                    mdtest_obj_dict[
                                        f"{command_extent_element}_{tmp_node}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank"
                                    ].elapsed_time,
                                )

                                if (
                                    int(
                                        mdtest_obj_dict[
                                            f"{command_extent_element}_{tmp_node}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank"
                                        ].elapsed_time
                                    )
                                    <= 10
                                ):
                                    print(
                                        "Warning!!! This run took less than 10 seconds!, not sleeping for now..."
                                    )
                                    # time.sleep(10)

                                # create/delete snapshots SECTION

                                if command_extent_element == "YuC":
                                    if not os.path.exists(
                                        f"{directory}/.snap/test_snapshots"
                                    ):
                                        _ = subprocess.run(
                                            f"mkdir {directory}/.snap/test_snapshots",
                                            shell=True,
                                            capture_output=False,
                                            text=True,
                                            check=True,
                                        )
                                        print(
                                            "{datetime.now().strftime('%b %d %H:%M:%S')} Creating snapshot after running creation mdtest..."
                                        )
                                    else:
                                        print(
                                            "{datetime.now().strftime('%b %d %H:%M:%S')} snapshot already exists, something went wrong"
                                        )

                                if command_extent_element == "Yur":
                                    if os.path.exists(
                                        f"{directory}/.snap/test_snapshots"
                                    ):
                                        print(
                                            "{datetime.now().strftime('%b %d %H:%M:%S')} Deleting snapshot after running deletion mdtest..."
                                        )
                                        _ = subprocess.run(
                                            f"rmdir {directory}/.snap/test_snapshots",
                                            shell=True,
                                            capture_output=False,
                                            text=True,
                                            check=True,
                                        )
                                    else:
                                        print(
                                            "{datetime.now().strftime('%b %d %H:%M:%S')} snapshot doesn't exist, something went wrong."
                                        )

                                # -------- snapshots SECTION ends here

                            # Iterate through arguments that have still not been used, decrement temporary counters
                            for key, value in result_dict.items():
                                if (
                                    key != "mpi_ranks"
                                    and key != "node_count"
                                    and key != "write_output"
                                    and key != "command_extensions"
                                ):
                                    if value["tmp_counter"] == 0:
                                        pass
                                    else:
                                        value["tmp_counter"] = value["tmp_counter"] - 1
                                        universal_key_counter = 1
                            # ----------
            else:
                print("not in_parts")
                sys.exit()
    else:
        print("General ops which are not yet taken into account are required.")
        sys.exit()
