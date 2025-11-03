import cappa

from arguments import CLIArguments


def main(args: CLIArguments):
    print(args)


if __name__ == "__main__":
    args = cappa.parse(CLIArguments)
    main(args)
