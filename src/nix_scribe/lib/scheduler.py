from nix_scribe.lib.registry import Module


class ModuleScheduler:
    @staticmethod
    def schedule(modules: dict[str, Module]) -> dict[str, Module]:
        """Orders modules strictly by execution phase, with deterministic tie-breaking by module name."""
        return dict(sorted(modules.items(), key=lambda item: (item[1].phase, item[0])))
