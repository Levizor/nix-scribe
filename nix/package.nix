{ ... }:
{
  perSystem =
    {
      pkgs,
      pythonSet,
      workspace,
      ...
    }:
    rec {
      packages.nix-scribe =
        (pythonSet.mkVirtualEnv "nix-scribe-env" workspace.deps.default).overrideAttrs
          (old: {
            meta = (old.meta or { }) // {
              mainProgram = "nix-scribe";
            };
          });
      packages.default = packages.nix-scribe;

      apps.nix-scribe = {
        type = "app";
        program = pkgs.lib.getExe' packages.default "nix-scribe";
      };
      apps.default = apps.nix-scribe;
    };
}
