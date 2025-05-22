import commands
import argparse  # parse command-line arguments
import sys

argparser = argparse.ArgumentParser(prog="mgit",
                                    description="Git implementation made by me",
                                    epilog="The same git commands but using my_git")
# This tells the parser to store the commands in a commands
# variable.
subparsers = argparser.add_subparsers(dest="command")
subparsers.required = True


def main(argv=sys.argv[1:]):
    args = argparser.parse_args(argv)
    print(args.command)
    match args.command:
        case "add": cmd_add(args)
        case _: print("Bad command.")


argsp = subparsers.add_parser("add")
argsp.add_argument("path",
                   nargs="?",
                   default=".")

def cmd_add(args):
    commands.git_add(args.path)
