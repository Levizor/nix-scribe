from nix_scribe.lib.option_block import SimpleOptionBlock
from nix_scribe.modules.base import BaseMapper, BaseScanner, Module


class VirtualisationMapper(BaseMapper):
    def map(self, *args, **kwargs):
        return SimpleOptionBlock(
            "virtualisation",
            "virtualisation options for testing the machine",
            {
                "virtualisation.vmVariant": {
                    "virtualisation": {
                        "cores": 4,
                        "memorySize": 8128,
                        "diskSize": 10240,
                    }
                }
            },
        )


module = Module("virtualisation", scanner=BaseScanner(), mapper=VirtualisationMapper())
