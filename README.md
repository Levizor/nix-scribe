# nix-scribe

A tool that reverse-engineers the current state of a Linux system to generate corresponding NixOS configuration files.

## The problem
NixOS, being a Linux distribution managed declaratively, is a strong fit for developers and system administrators.
However, its fundamentally different approach to system management makes transitioning to NixOS challenging - especially for new users who are just beginning to learn Nix.

This project aims to simplify and automate the transition from traditional (imperative) Linux distributions to declarative NixOS, by creating a tool **nix-scribe** to automate the process of writing NixOS configuration files.

## The Idea
**nix-scribe** is essentially a Python script, that __scans__ your current (or specified) system - including configuration files, users, services, packages - and attempts to __map__ this state to NixOS options and definitions.

## Usage
```
Usage: nix-scribe [OPTIONS] [ROOT_PATH]

Arguments:
  [ROOT_PATH]  Path to the root directory of the system to be scanned [default: /]
```

Run with nix:
```
sudo -E nix --extra-experimental-features "nix-command flakes" run --refresh github:Levizor/nix-scribe
```

It's advised to run the script with sudo to allow scanning as much as possible.
You can specify the path to the root directory of the system to be scanned, in case you mount it to your current one.

## Contributions
Contributions are welcome.
Adding as much modules as possible is the main target of the project.

Read [CONTRIBUTING.md](./CONTRIBUTING.md) to better understand how to do that.

---
<small>The project is developed as a Bachelors Thesis project for the Polish-Japanese Academy of Information Technology</small>
