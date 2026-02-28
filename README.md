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
```sh
Usage: nix-scribe [OPTIONS] [ROOT_PATH]

Arguments:
  [ROOT_PATH]  Path to the root directory of the system to be scanned [default: /]

Options:
  -o --output       Output path of the configuration
  -m --mod-level    Level of modularization oft he configuration
  --no-comment      Don't write comments in the output files
  --confirm         Don't ask for confirmation
  -v --verbosity    Set verbosity level (1 - Info, 2 - Debug)
```

Run without arguments:
```sh
nix-scribe
```

nix-scribe will scan your system, map definitions and output the configuration in nix-config/configuration.nix

It's advised to run the script with sudo to allow scanning as much as possible.
But the script generally should work without it as well, asking for sudo permissions if required.

Use -m | --mod-level option to create a divided configuration:
- -m 0 - single file
- -m 1 - top-level modules files (services.nix, programs.nix)
- -m 2 - individual file for each module

```
nix-scribe -m 2 -o output-dir
```
result:
```
output-dir
├── configuration.nix
├── boot
│   ├── boot-loader-grub-background.jpg
│   ├── default.nix
│   └── grub.nix
├── programs
│   ├── bash.nix
│   ├── default.nix
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

You can specify the path to the root directory of the system to be scanned, in case you mount it to your current one.

```
nix-scribe /mnt/mounted_system
```

## Contributions
Contributions are welcome.
Adding as much modules as possible is the main target of the project.

Read [CONTRIBUTING.md](./CONTRIBUTING.md) to better understand how to do that.

---
<small>The project is developed as a Bachelors Thesis project for the Polish-Japanese Academy of Information Technology</small>
