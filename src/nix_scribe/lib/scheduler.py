from nix_scribe.lib.registry import Scanner


class ScannerScheduler:
    @staticmethod
    def schedule(scanners: dict[str, Scanner]) -> dict[str, Scanner]:
        """Orders scanners strictly by execution phase, with deterministic tie-breaking by scanner name."""
        return dict(sorted(scanners.items(), key=lambda item: (item[1].phase, item[0])))
