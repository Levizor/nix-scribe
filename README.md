# nix-scribe

A tool that reverse-engineers the current state of a Linux system to generate corresponding NixOS configuration files.

## The problem
NixOS, being a Linux distribution managed declaratively, is a strong fit for developers and system administrators.
However, its fundamentally different approach to system management makes transitioning to NixOS challenging - especially for new users who are just beginning to learn Nix.

This project aims to simplify and automate the transition from traditional (imperative) Linux distributions to declarative NixOS, by creating a tool **nix-scribe** to automate the process of writing NixOS configuration files.

## The Idea
**nix-scribe** is essentially a Python script, that __scans__ your current (or specified) system - including configuration files, users, services, packages - and attempts to __map__ this state to NixOS options and definitions.

## Installation
You don't have to install the script to run it with nix run. In that case though, you have to specify full command:
```sh
nix --extra-experimental-features "nix-command flakes" run --refresh github:Levizor/nix-scribe -- <command line options and arguments>
```

To install the tool you can use nix profile

```sh
nix --extra-experimental-features "nix-command flakes" profile add github:Levizor/nix-scribe
```

or on NixOS you can add it as a flake:
```nix
# flake.nix
inputs = {
  nix-scribe.url = "github:Levizor/nix-scribe";
};

```

```nix
# configuration.nix
environment.systemPackages = [
  inputs.nix-scribe.packages.${system}.nix-scribe
];
```

## Usage
It's advised to run the script with sudo to allow scanning as much as possible.
But the script generally should work without it as well, asking for sudo permissions if required.

```sh
Usage: nix-scribe [OPTIONS] [ROOT_PATH]

Arguments:
  [ROOT_PATH]  Path to the root directory of the system to be scanned [default: /]

Options:
  -o, --output PATH           Output path for configuration [default: ./nix-config]
  -m, --mod-level INTEGER     Modularity level: 0 - single file, 1 - category files, 2 - per-module files [default: 0]
  -e, --enable-module TEXT    Enable module(s) (comma-separated or repeated)
  -d, --disable-module TEXT   Disable module(s) (comma-separated or repeated)
  --only TEXT                 Run only specified module(s) (comma-separated or repeated)
  -p, --plugin TEXT           Load external plugin file, directory, or python package
  --list-modules              List available modules and default status, then exit
  --list-modules-tree         List available modules in a hierarchical tree, then exit
  -v, --verbosity INTEGER     Verbosity: 0 - silent, 1 - INFO, 2 - DEBUG [default: 1]
  --mod-verbosity INTEGER     Module log verbosity: 0 - silent, 1 - INFO, 2 - DEBUG
  --no-comment                Don't write comments in output files
  --confirm                   Don't ask for confirmation
```

Run against the current running system:
```sh
nix-scribe
```

Scan a mounted offline root:
```sh
nix-scribe /mnt/target-root
```

Run only specific modules:
```sh
nix-scribe --only networking,programs.git,security.sudo
```

Modularize output into subdirectories:
- `-m 0` - Single file (`configuration.nix`)
- `-m 1` - Top-level category files (`services.nix`, `programs.nix`)
- `-m 2` - Individual file for each module (`programs/git.nix`, `services/sddm.nix`)

```sh
nix-scribe -m 2 -o output-dir
```

Output tree with `-m 2`:
```
output-dir
├── configuration.nix
├── boot
│   ├── boot-loader-grub-background.jpg
│   ├── default.nix
│   └── grub.nix
├── environment
│   ├── default.nix
│   └── system_packages.nix
├── programs
│   ├── bash.nix
│   ├── default.nix
│   ├── git.nix
│   └── hyprland.nix
├── security
│   ├── default.nix
│   └── sudo.nix
├── services
│   ├── cosmic.nix
│   ├── default.nix
│   ├── gnome.nix
│   ├── plasma6.nix
│   └── sddm.nix
├── users
│   ├── default.nix
│   ├── groups.nix
│   └── users.nix
└── virtualisation
    ├── default.nix
    └── virtualisation.nix
```

## Contributions
Contributions are welcome.
Adding as much modules as possible is the main target of the project.

Read [CONTRIBUTING.md](./CONTRIBUTING.md) to better understand how to do that.

---
<small>The project is developed as a Bachelors Thesis project for the Polish-Japanese Academy of Information Technology</small>
