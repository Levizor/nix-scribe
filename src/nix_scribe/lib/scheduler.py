from nix_scribe.lib.registry import Scanner


class ModuleScheduler:
    @staticmethod
    def schedule(modules: dict[str, Scanner]) -> dict[str, Scanner]:
        """Orders scanners strictly by execution phase, with deterministic tie-breaking by scanner name."""
        return dict(sorted(modules.items(), key=lambda item: (item[1].phase, item[0])))
