"""CLI alias bridging app.cli.main to app.pipeline.cli for backward compatibility."""

import sys
from app.pipeline.cli import main as pipeline_cli_main


def main():
    # If invoked with 'run-pipeline', map to 'complete'
    args = sys.argv[1:]
    new_args = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "run-pipeline":
            new_args.append("complete")
        elif arg == "refresh-measurements":
            new_args.append("refresh")
        elif arg == "--target-url":
            # map --target-url to --target-audit-url
            new_args.append("--target-audit-url")
            if i + 1 < len(args):
                i += 1
                new_args.append(args[i])
        else:
            new_args.append(arg)
        i += 1

    sys.argv = [sys.argv[0]] + new_args
    return pipeline_cli_main()


if __name__ == "__main__":
    main()
