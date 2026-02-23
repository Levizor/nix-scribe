from nix_scribe.modules.base import BaseMapper, BaseScanner, Module


class TestScanner(BaseScanner):
    def scan(self, context):
        return {}


class TestMapper(BaseMapper):
    def map(self, ir):
        return None


module = Module("dummy", TestScanner(), TestMapper())
