# Contributing
Contributions are welcome. For now there are no strict rules regarding how to write the code, but try to stick to good programming practices.

## How to add a module
To add a module, find a respective directory and create a file to its definition in nixpkgs. For example, to add `programs.vim` option you would create `btop.py` file in the `src/nix_scribe/modules/programs` directory.

In this file you have to write the following:

### A Scanner
**Scanner** is a logical part of your script used to actually fetch the required data and parse it to some kind of Intermediate Representation.
For the aforementioned `programs.vim` option you would check if `btop` is installed on the system, by running `shutil.which("btop")` or directly checking `/bin` for example.

### A Mapper
**Mapper**'s responsibility is to process the Intermediate Representation produced by a **Scanner**, then build and return an **OptionBlock**.

#### Option Block
A logical partition of the configuration, a pythonic representation of Nix configuration set. It has a `name`, `description` and `arguments` fields. Name should reflect our option path with a slash, e.g. `programs/vim`, as this field may be used as a filename and turned into `programs/vim.nix`. Description is just a comment used later by `NixWriter`. Arguments allow you to specify which function arguments you require in your configuration set. For example, if you need `pkgs` set to specify `programs.vim.package = pkgs.vim-full` you have to add those `pkgs` into the arguments set, as it has to be added to the function parameters in the resulting code.
Lastly there's data. You write NixOS options in standard python dictionary. Then it is processed by the NixWriter class and mapped into a respective nixos code. For the most basic modules requiring little to no description `SimpleOptionBlock` is a way to go. It will output the description of your module as a comment, and the data you put in it as nix code.

For example, this option block

```python
SimpleOptionBlock(
    name="networkmanager",
    description="NetworkManager configuration",
    data={
        "networking.networkmanager": {
            "enable": True,
            "plugins": [raw("pkgs.networkmanager-openvpn")],
        }
    },
    arguments=["pkgs"]
)
```

will be mapped to

```nix
# NetworkManager configuration
networking.networkmanager = {
  enable = true;
  plugins = [
    pkgs.networkmanager-openvpn
  ];
};

```

You can see more examples by reading already created modules, other than that you have a freedom of implementation. You can as well create your own option blocks inheriting from `BaseOptionBlock` to define the `render()` function behaviour yourself, but that's most probably an overkill.
