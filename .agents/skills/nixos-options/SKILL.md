---
name: nixos-options
description: Skill for evaluating, searching, and inspecting authoritative NixOS options from local nixpkgs using nix eval.
---

# Querying NixOS Options via `nix eval`

When reverse-engineering system settings into NixOS configuration options, query local `nixpkgs` directly to discover precise option names, types, and defaults.

## 1. List Sub-Attributes of an Option Path
```bash
nix eval --json --impure --expr '
  let
    eval = import <nixpkgs/nixos/lib/eval-config.nix> { modules = []; };
  in builtins.attrNames eval.options.<attribute.path>
'
```
*Example*:
```bash
nix eval --json --impure --expr 'let eval = import <nixpkgs/nixos/lib/eval-config.nix> { modules = []; }; in builtins.attrNames eval.options.security.pam'
```

---

## 2. List Sub-Options of Dynamic Sets (e.g. `services.<name>`, `luks.devices.<name>`)
```bash
nix eval --json --impure --expr '
  let
    eval = import <nixpkgs/nixos/lib/eval-config.nix> { modules = []; };
  in builtins.attrNames (eval.options.<attribute.path>.type.getSubOptions [])
'
```

---

## 3. Inspect Full Metadata (Type, Default, Description) for an Option
```bash
nix eval --json --impure --expr '
  let
    eval = import <nixpkgs/nixos/lib/eval-config.nix> { modules = []; };
    opt = eval.options.<attribute.path>.<option_name>;
  in {
    type = opt.type.name;
    description = opt.description or null;
    default = opt.default or null;
  }
'
```
