# Exact RHCSA v9 Practice Paper

This private build is locked to the supplied 21-question practice paper:

- Node 1: 15 questions
- Node 2: 6 questions
- Duration: 180 minutes
- Default version: EX200 v9
- No randomized upstream questions are selected in Exam Mode

The original source PDF is stored at `docs/RHEL-9-RHCSA-Exam-Paper.pdf` for
private reference. The simulator displays the questions without the answer
section and validates the resulting system configuration using read-only checks.

## Install

Run as root on a disposable RHEL 9-compatible practice machine:

```bash
git clone https://github.com/Krishan195/krishan-rhcsa-v9-simulator.git
cd krishan-rhcsa-v9-simulator
chmod +x install.sh
sudo ./install.sh
```

Use snapshots or disposable VMs. These exercises intentionally modify users,
storage, networking, SELinux, firewall, services, and boot configuration.
