"""Run inside the simulation environment, separate from the launcher's Qt runtime."""

import sys

kind = sys.argv.pop(1)
if kind == "sim":
    from isaacsim import main
    main()
elif kind == "lab":
    from isaaclab.cli import cli
    cli()
else:
    raise SystemExit(f"Unknown launch kind: {kind}")
