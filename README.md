# nix-scribe

A tool that reverse-engineers the current state of a Linux system to generate corresponding NixOS configuration files.

## The problem
NixOS, being a Linux distribution managed declaratively, is a strong fit for developers and system administrators.
However, its fundamentally different approach to system management makes transitioning to NixOS challenging - especially for new users who are just beginning to learn Nix.

This project aims to simplify and automate the transition from traditional (imperative) Linux distributions to declarative NixOS, by creating a tool **nix-scribe** to automate the process of writing NixOS configuration files.

## The Idea
**nix-scribe** is essentially a Python script, that __scans__ your current (or specified) system - including configuration files, users, services, packages - and attempts to __map__ this state to NixOS options and definitions.

---
<small>The project is developed as a Bachelors Thesis project for the Polish-Japanese Academy of Information Technology</small>
