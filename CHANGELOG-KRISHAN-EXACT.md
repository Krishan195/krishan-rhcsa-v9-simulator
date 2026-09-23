# Krishan Exact Paper Changes

Modified files:

- `tasks/krishan_paper.py`
  - Replaced the previous original/generic mock tasks with the exact 21-paper task set.
  - Added validators for the exact hostnames, repo URLs, users, paths, ports, autofs target, Podman image/container, Node2 LVM/swap/mount/tuned tasks.

- `core/krishan_setup.py`
  - Updated lab preparation to support the exact paper: `aletha` source files, `/usr/share/dict/words`, local Containerfile, `/home/remoteuser20` NFS export on node2, and loop-backed existing LV `data`.

- `EXACT_EXAM.md`
  - Rewritten to show the exact Node1/Node2 task list.

- `docs/EXACT-PAPER-COMMAND-GUIDE.md`
  - Added a private study guide with command examples for all 21 questions.

- `README.md`
  - Updated install/run notes and coverage to match the exact paper.
