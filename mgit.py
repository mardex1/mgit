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
    match args.command:
        case "add": cmd_add()
        case "init": cmd_init()
        case "rcomp": cmd_rcomp(args)
        case "commit": cmd_commit(args)
        case "fgit": cmd_fgit()
        case _: print("Bad command.")


argsp = subparsers.add_parser("add")

def cmd_add():
    commands.git_add()

argsp = subparsers.add_parser("rcomp")
argsp.add_argument("path",
                   nargs="?",
                   default=".")

def cmd_rcomp(args):
    commands.read_hash(args.path)

argsp = subparsers.add_parser("commit")
argsp.add_argument("-m",
                   required=True)

def cmd_commit(args):
    commands.git_commit(args.m)

argsp = subparsers.add_parser("fgit")

def cmd_fgit():
    commands.find_git_dir()

argsp = subparsers.add_parser("init")

def cmd_init():
    commands.git_init()
