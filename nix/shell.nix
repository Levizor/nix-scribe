{ inputs, ... }:
{
  perSystem =
    {
      config,
      pkgs,
      pythonSet,
      workspace,
      ...
    }:
    let
      editableOverlay = workspace.mkEditablePyprojectOverlay {
        root = "$REPO_ROOT";
      };

      editablePythonSet = pythonSet.overrideScope editableOverlay;
      virtualenv = editablePythonSet.mkVirtualEnv "nix-scribe-dev-env" workspace.deps.all;
    in
    {
      devShells.default = pkgs.mkShell {
        packages = with pkgs; [
          virtualenv
          uv
          act
          nixfmt-rfc-style
          pre-commit
        ];

        env = {
          UV_NO_SYNC = "1";
          UV_PYTHON = pythonSet.python.interpreter;
          UV_PYTHON_DOWNLOADS = "never";
        };

        shellHook = ''
          unset PYTHONPATH
          export REPO_ROOT=$(git rev-parse --show-toplevel)
          if [ -d .git ]; then
            pre-commit install > /dev/null
            echo "Pre-commit hooks installed 🪝"
          fi
          echo "Shell Ready ✅"
        '';
      };
    };
}
