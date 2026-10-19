# Changelog

## [0.1.0](https://github.com/Levizor/nix-scribe/compare/v0.1.0...v0.1.0) (2026-10-19)


### Features

* add module blacklist/whitelist filtering and singleton ModuleRegistry ([#85](https://github.com/Levizor/nix-scribe/issues/85)) ([21a0cb6](https://github.com/Levizor/nix-scribe/commit/21a0cb6761598b805f4d6f894cc67f4e0ad13858))
* **asset:** add in-memory content support to Asset ([#115](https://github.com/Levizor/nix-scribe/issues/115)) ([dd4dd7b](https://github.com/Levizor/nix-scribe/commit/dd4dd7bd77b0cc938a6b786488a03cb8a89107c9))
* **core:** add declarative package claims to ConfigFragment and NixScribe mapper ([#106](https://github.com/Levizor/nix-scribe/issues/106)) ([617e22e](https://github.com/Levizor/nix-scribe/commit/617e22eba875c6001f5e8e04f0eaa0b910eadb49))
* **core:** implement ModulePhase and ModuleScheduler for execution ordering ([#99](https://github.com/Levizor/nix-scribe/issues/99)) ([#102](https://github.com/Levizor/nix-scribe/issues/102)) ([d468eae](https://github.com/Levizor/nix-scribe/commit/d468eaeed6a201bbfc8083c0ad0bcc455fd28ed6))
* **environment:** implement environment.systemPackages module ([#92](https://github.com/Levizor/nix-scribe/issues/92)) ([#104](https://github.com/Levizor/nix-scribe/issues/104)) ([dbd9f97](https://github.com/Levizor/nix-scribe/commit/dbd9f97d5dc215f378341049bd255ca1429d5313))
* **flake:** add container rootfs test helpers ([#113](https://github.com/Levizor/nix-scribe/issues/113)) ([75a2792](https://github.com/Levizor/nix-scribe/commit/75a279231b34b15ef2a80f1ca7249bb07ba17e65))
* implement boot.kernel module ([#76](https://github.com/Levizor/nix-scribe/issues/76)) ([#83](https://github.com/Levizor/nix-scribe/issues/83)) ([85a24d3](https://github.com/Levizor/nix-scribe/commit/85a24d30b36ce8e81e8489f2d3ddf4932ad18529))
* implement PAM security module ([#16](https://github.com/Levizor/nix-scribe/issues/16)) ([f354375](https://github.com/Levizor/nix-scribe/commit/f3543756564d739bca94e52d88d6a7c326f218ba))
* implement PAM security module ([#16](https://github.com/Levizor/nix-scribe/issues/16)) ([c0393d2](https://github.com/Levizor/nix-scribe/commit/c0393d2ece9da9d94d0f6aaa66ef74789769aff0))
* implement systemd-boot loader module ([#75](https://github.com/Levizor/nix-scribe/issues/75)) ([#80](https://github.com/Levizor/nix-scribe/issues/80)) ([dc241d5](https://github.com/Levizor/nix-scribe/commit/dc241d54f45a50ab9f9ee4ac5ecdad1417dc575a))
* **loader:** add plugin loading support for custom module locations ([#86](https://github.com/Levizor/nix-scribe/issues/86)) ([#87](https://github.com/Levizor/nix-scribe/issues/87)) ([b73f81d](https://github.com/Levizor/nix-scribe/commit/b73f81d03d3adec4fd1a3aa82c23c2895327f372))
* **packages:** define PackageResolver interface and mock provider ([#91](https://github.com/Levizor/nix-scribe/issues/91)) ([#101](https://github.com/Levizor/nix-scribe/issues/101)) ([e86c78c](https://github.com/Levizor/nix-scribe/commit/e86c78c6c66539322f86229db109c6a2475c76f7))
* **packages:** implement Debian/Ubuntu AptManager and parser ([#94](https://github.com/Levizor/nix-scribe/issues/94)) ([#105](https://github.com/Levizor/nix-scribe/issues/105)) ([ad36bec](https://github.com/Levizor/nix-scribe/commit/ad36bec0d24b468f92abffb8475530591f20d657))
* **packages:** implement PackageManager and DummyPackageResolver ([#100](https://github.com/Levizor/nix-scribe/issues/100)) ([#103](https://github.com/Levizor/nix-scribe/issues/103)) ([1a5ee20](https://github.com/Levizor/nix-scribe/commit/1a5ee20343d9c291d6d6fe51aab39f0be953ed38))
* **packages:** implement packages.log audit report and claim attribution ([#117](https://github.com/Levizor/nix-scribe/issues/117)) ([c3b1858](https://github.com/Levizor/nix-scribe/commit/c3b18589ba98bdf46d8dc4d9589a658f650882e7))
* **packages:** implement PkgmapPackageResolver using pkgmap library ([#109](https://github.com/Levizor/nix-scribe/issues/109)) ([3d3ccc0](https://github.com/Levizor/nix-scribe/commit/3d3ccc098f3b57cc3882dc6c99f54852921cb1ec))
* **packages:** preserve DiscoveredPackage for unmapped packages with provenance comments ([#107](https://github.com/Levizor/nix-scribe/issues/107)) ([cc77986](https://github.com/Levizor/nix-scribe/commit/cc77986ec497428641684de5ca92256dc43332dc))
* **packages:** wire up PkgmapPackageResolver as default resolver ([#111](https://github.com/Levizor/nix-scribe/issues/111)) ([f206f11](https://github.com/Levizor/nix-scribe/commit/f206f11e6909fee054c685d0991bf2cc432b8a6f))
* **pkgmap:** choose "core" database variant in PkgmapPackageResolver ([#119](https://github.com/Levizor/nix-scribe/issues/119)) ([dd8bc39](https://github.com/Levizor/nix-scribe/commit/dd8bc39f83734d4035951435597e8ddc73deec3a))


### Bug Fixes

* add quotes ([#50](https://github.com/Levizor/nix-scribe/issues/50)) ([ec17de0](https://github.com/Levizor/nix-scribe/commit/ec17de0a39f83d2856f56ce44000011171dbab69))
* **ci:** restrict setup-uv cache glob to pyproject.toml to avoid scanning mock test root ([1f0e226](https://github.com/Levizor/nix-scribe/commit/1f0e226cb8f09b845d37e9a0b68943c3c1648252))
* escape $ characters ([a51ed66](https://github.com/Levizor/nix-scribe/commit/a51ed667634637938888e1a481f6b64ebe163edf))
* fix string value escaping in multiline strings ([#60](https://github.com/Levizor/nix-scribe/issues/60)) ([ff69073](https://github.com/Levizor/nix-scribe/commit/ff6907312cb8e1aa7c1f432991038129e500a17a))
* general fixes ([a13d73b](https://github.com/Levizor/nix-scribe/commit/a13d73bd96ada79ce214731c8f71fbcaac685e57))
* general fixes ([1343af1](https://github.com/Levizor/nix-scribe/commit/1343af1e4d7eb1516878bf0dc7ab6a679a9fb80a))
* general fixes ([1670aa6](https://github.com/Levizor/nix-scribe/commit/1670aa6a2e299a81b8c72bbf6cad5d755b01180a))
* **grub:** purge run_command mount in favor of fstab and proc mounts inspection ([5aba33f](https://github.com/Levizor/nix-scribe/commit/5aba33fb4b72359e8240e19b1713a3837a359b6e))
* **grub:** purge run_command mount in favor of fstab and proc mounts inspection ([ed7d1ac](https://github.com/Levizor/nix-scribe/commit/ed7d1acef145bbf8633ee7d80e1b393be2cf774a))
* mod 2 doesn't catch arguments ([#37](https://github.com/Levizor/nix-scribe/issues/37)) ([c73a15c](https://github.com/Levizor/nix-scribe/commit/c73a15c29b1f1b1ad9ccdce2bf69dc21d05f6051))
* **networking:** use lowercase networkmanager attribute ([#112](https://github.com/Levizor/nix-scribe/issues/112)) ([029f72d](https://github.com/Levizor/nix-scribe/commit/029f72df3c60a0d2c4492f6592dd8a8a8561e1f3))
* nix option accepts only boolean ([f3e0476](https://github.com/Levizor/nix-scribe/commit/f3e0476ae84520364bd67db699d60b288ecf3783))
* nix option accepts only boolean ([#61](https://github.com/Levizor/nix-scribe/issues/61)) ([f60129d](https://github.com/Levizor/nix-scribe/commit/f60129d0cbad9dd8d16e07dcdeffa0ad46a97f8c))
* **packages:** classify apt history.log packages as explicit ([#114](https://github.com/Levizor/nix-scribe/issues/114)) ([b3bc518](https://github.com/Levizor/nix-scribe/commit/b3bc518610b704bd14687d20a3d87ba28ccbb591))
* quote keys with dots to not break ini file type ([f13668b](https://github.com/Levizor/nix-scribe/commit/f13668b1203d83e706ef98bf7eac1cb8e2137e3b))
* refactor sudo module to pure python parser ([#35](https://github.com/Levizor/nix-scribe/issues/35)) ([f298873](https://github.com/Levizor/nix-scribe/commit/f298873d8f4b077516806ef1a8a2dc002cc9de91))
* refactor sudo module to pure python parser ([#35](https://github.com/Levizor/nix-scribe/issues/35)) ([5f73fc4](https://github.com/Levizor/nix-scribe/commit/5f73fc4394e8e3c54f9f138608aa2d517c88e635))
* remove . (test ci) ([079a4b0](https://github.com/Levizor/nix-scribe/commit/079a4b0b4da11d8e859746f54a2306fa32808af7))
* remove print from tests ([dce30fa](https://github.com/Levizor/nix-scribe/commit/dce30fa43bed6bbde0b2937437feaa0ef48a4225))
* remove unused tests ([f76dfec](https://github.com/Levizor/nix-scribe/commit/f76dfec22d294c62299d6612c79b4fcd2fb0317a))
* replace runtime proc ipv6 check with persistent sysctl config ([#68](https://github.com/Levizor/nix-scribe/issues/68)) ([a31eda5](https://github.com/Levizor/nix-scribe/commit/a31eda57719ba03e458b61370de0935718455f58))
* replace runtime proc ipv6 check with persistent sysctl config ([#68](https://github.com/Levizor/nix-scribe/issues/68)) ([e4d15ed](https://github.com/Levizor/nix-scribe/commit/e4d15ed9bb088c635f073f7411f62841b9748bba))
* **tests:** remove problematic /usr/lib symlink in mock system root ([1fbeb63](https://github.com/Levizor/nix-scribe/commit/1fbeb63c2a55231e4c9492b8fc1cd1104ab90106))
* use set ([#51](https://github.com/Levizor/nix-scribe/issues/51)) ([ed08003](https://github.com/Levizor/nix-scribe/commit/ed08003c0dce90fe25b150335cfbd7a6428e89f5))
* use set for arguments field in optino block, then just sort it in the nixfile writing ([#49](https://github.com/Levizor/nix-scribe/issues/49)) ([279cc41](https://github.com/Levizor/nix-scribe/commit/279cc41d965ce9a5c61d875176d8c5d06012ded7))


### Documentation

* add development skills ([1b7f79f](https://github.com/Levizor/nix-scribe/commit/1b7f79fc08b112739ba1c494a24421d67f5ecb7e))
* add GEMINI.md project standards and agent instructions ([#82](https://github.com/Levizor/nix-scribe/issues/82)) ([8612752](https://github.com/Levizor/nix-scribe/commit/8612752b8e3bdef3f35ed36cabdaf8daf20f6fa2))
* add nix-scribe development skills ([bdd49cc](https://github.com/Levizor/nix-scribe/commit/bdd49cc3ad8c5475848bf31ad05b19b091b8d70f))
* update documentation for scanner/mapper architecture and cli options ([#108](https://github.com/Levizor/nix-scribe/issues/108)) ([241dcab](https://github.com/Levizor/nix-scribe/commit/241dcabad047225b1524fc4b61d444264f2bc00f))
* update GEMINI.md with comprehensive user preferences and standards ([#84](https://github.com/Levizor/nix-scribe/issues/84)) ([f1c2a3f](https://github.com/Levizor/nix-scribe/commit/f1c2a3fbeb685eae65aca91fba98e7c720d27d55))


### Miscellaneous Chores

* force release version to 0.1.0 ([#124](https://github.com/Levizor/nix-scribe/issues/124)) ([7e2c130](https://github.com/Levizor/nix-scribe/commit/7e2c130fd5ac6c01a3f60dcd781fc407aab864a3))

## 0.1.0 (2026-10-19)


### Features

* add module blacklist/whitelist filtering and singleton ModuleRegistry ([#85](https://github.com/Levizor/nix-scribe/issues/85)) ([21a0cb6](https://github.com/Levizor/nix-scribe/commit/21a0cb6761598b805f4d6f894cc67f4e0ad13858))
* **asset:** add in-memory content support to Asset ([#115](https://github.com/Levizor/nix-scribe/issues/115)) ([dd4dd7b](https://github.com/Levizor/nix-scribe/commit/dd4dd7bd77b0cc938a6b786488a03cb8a89107c9))
* **core:** add declarative package claims to ConfigFragment and NixScribe mapper ([#106](https://github.com/Levizor/nix-scribe/issues/106)) ([617e22e](https://github.com/Levizor/nix-scribe/commit/617e22eba875c6001f5e8e04f0eaa0b910eadb49))
* **core:** implement ModulePhase and ModuleScheduler for execution ordering ([#99](https://github.com/Levizor/nix-scribe/issues/99)) ([#102](https://github.com/Levizor/nix-scribe/issues/102)) ([d468eae](https://github.com/Levizor/nix-scribe/commit/d468eaeed6a201bbfc8083c0ad0bcc455fd28ed6))
* **environment:** implement environment.systemPackages module ([#92](https://github.com/Levizor/nix-scribe/issues/92)) ([#104](https://github.com/Levizor/nix-scribe/issues/104)) ([dbd9f97](https://github.com/Levizor/nix-scribe/commit/dbd9f97d5dc215f378341049bd255ca1429d5313))
* **flake:** add container rootfs test helpers ([#113](https://github.com/Levizor/nix-scribe/issues/113)) ([75a2792](https://github.com/Levizor/nix-scribe/commit/75a279231b34b15ef2a80f1ca7249bb07ba17e65))
* implement boot.kernel module ([#76](https://github.com/Levizor/nix-scribe/issues/76)) ([#83](https://github.com/Levizor/nix-scribe/issues/83)) ([85a24d3](https://github.com/Levizor/nix-scribe/commit/85a24d30b36ce8e81e8489f2d3ddf4932ad18529))
* implement PAM security module ([#16](https://github.com/Levizor/nix-scribe/issues/16)) ([f354375](https://github.com/Levizor/nix-scribe/commit/f3543756564d739bca94e52d88d6a7c326f218ba))
* implement PAM security module ([#16](https://github.com/Levizor/nix-scribe/issues/16)) ([c0393d2](https://github.com/Levizor/nix-scribe/commit/c0393d2ece9da9d94d0f6aaa66ef74789769aff0))
* implement systemd-boot loader module ([#75](https://github.com/Levizor/nix-scribe/issues/75)) ([#80](https://github.com/Levizor/nix-scribe/issues/80)) ([dc241d5](https://github.com/Levizor/nix-scribe/commit/dc241d54f45a50ab9f9ee4ac5ecdad1417dc575a))
* **loader:** add plugin loading support for custom module locations ([#86](https://github.com/Levizor/nix-scribe/issues/86)) ([#87](https://github.com/Levizor/nix-scribe/issues/87)) ([b73f81d](https://github.com/Levizor/nix-scribe/commit/b73f81d03d3adec4fd1a3aa82c23c2895327f372))
* **packages:** define PackageResolver interface and mock provider ([#91](https://github.com/Levizor/nix-scribe/issues/91)) ([#101](https://github.com/Levizor/nix-scribe/issues/101)) ([e86c78c](https://github.com/Levizor/nix-scribe/commit/e86c78c6c66539322f86229db109c6a2475c76f7))
* **packages:** implement Debian/Ubuntu AptManager and parser ([#94](https://github.com/Levizor/nix-scribe/issues/94)) ([#105](https://github.com/Levizor/nix-scribe/issues/105)) ([ad36bec](https://github.com/Levizor/nix-scribe/commit/ad36bec0d24b468f92abffb8475530591f20d657))
* **packages:** implement PackageManager and DummyPackageResolver ([#100](https://github.com/Levizor/nix-scribe/issues/100)) ([#103](https://github.com/Levizor/nix-scribe/issues/103)) ([1a5ee20](https://github.com/Levizor/nix-scribe/commit/1a5ee20343d9c291d6d6fe51aab39f0be953ed38))
* **packages:** implement packages.log audit report and claim attribution ([#117](https://github.com/Levizor/nix-scribe/issues/117)) ([c3b1858](https://github.com/Levizor/nix-scribe/commit/c3b18589ba98bdf46d8dc4d9589a658f650882e7))
* **packages:** implement PkgmapPackageResolver using pkgmap library ([#109](https://github.com/Levizor/nix-scribe/issues/109)) ([3d3ccc0](https://github.com/Levizor/nix-scribe/commit/3d3ccc098f3b57cc3882dc6c99f54852921cb1ec))
* **packages:** preserve DiscoveredPackage for unmapped packages with provenance comments ([#107](https://github.com/Levizor/nix-scribe/issues/107)) ([cc77986](https://github.com/Levizor/nix-scribe/commit/cc77986ec497428641684de5ca92256dc43332dc))
* **packages:** wire up PkgmapPackageResolver as default resolver ([#111](https://github.com/Levizor/nix-scribe/issues/111)) ([f206f11](https://github.com/Levizor/nix-scribe/commit/f206f11e6909fee054c685d0991bf2cc432b8a6f))
* **pkgmap:** choose "core" database variant in PkgmapPackageResolver ([#119](https://github.com/Levizor/nix-scribe/issues/119)) ([dd8bc39](https://github.com/Levizor/nix-scribe/commit/dd8bc39f83734d4035951435597e8ddc73deec3a))


### Bug Fixes

* add quotes ([#50](https://github.com/Levizor/nix-scribe/issues/50)) ([ec17de0](https://github.com/Levizor/nix-scribe/commit/ec17de0a39f83d2856f56ce44000011171dbab69))
* **ci:** restrict setup-uv cache glob to pyproject.toml to avoid scanning mock test root ([1f0e226](https://github.com/Levizor/nix-scribe/commit/1f0e226cb8f09b845d37e9a0b68943c3c1648252))
* escape $ characters ([a51ed66](https://github.com/Levizor/nix-scribe/commit/a51ed667634637938888e1a481f6b64ebe163edf))
* fix string value escaping in multiline strings ([#60](https://github.com/Levizor/nix-scribe/issues/60)) ([ff69073](https://github.com/Levizor/nix-scribe/commit/ff6907312cb8e1aa7c1f432991038129e500a17a))
* general fixes ([a13d73b](https://github.com/Levizor/nix-scribe/commit/a13d73bd96ada79ce214731c8f71fbcaac685e57))
* general fixes ([1343af1](https://github.com/Levizor/nix-scribe/commit/1343af1e4d7eb1516878bf0dc7ab6a679a9fb80a))
* general fixes ([1670aa6](https://github.com/Levizor/nix-scribe/commit/1670aa6a2e299a81b8c72bbf6cad5d755b01180a))
* **grub:** purge run_command mount in favor of fstab and proc mounts inspection ([5aba33f](https://github.com/Levizor/nix-scribe/commit/5aba33fb4b72359e8240e19b1713a3837a359b6e))
* **grub:** purge run_command mount in favor of fstab and proc mounts inspection ([ed7d1ac](https://github.com/Levizor/nix-scribe/commit/ed7d1acef145bbf8633ee7d80e1b393be2cf774a))
* mod 2 doesn't catch arguments ([#37](https://github.com/Levizor/nix-scribe/issues/37)) ([c73a15c](https://github.com/Levizor/nix-scribe/commit/c73a15c29b1f1b1ad9ccdce2bf69dc21d05f6051))
* **networking:** use lowercase networkmanager attribute ([#112](https://github.com/Levizor/nix-scribe/issues/112)) ([029f72d](https://github.com/Levizor/nix-scribe/commit/029f72df3c60a0d2c4492f6592dd8a8a8561e1f3))
* nix option accepts only boolean ([f3e0476](https://github.com/Levizor/nix-scribe/commit/f3e0476ae84520364bd67db699d60b288ecf3783))
* nix option accepts only boolean ([#61](https://github.com/Levizor/nix-scribe/issues/61)) ([f60129d](https://github.com/Levizor/nix-scribe/commit/f60129d0cbad9dd8d16e07dcdeffa0ad46a97f8c))
* **packages:** classify apt history.log packages as explicit ([#114](https://github.com/Levizor/nix-scribe/issues/114)) ([b3bc518](https://github.com/Levizor/nix-scribe/commit/b3bc518610b704bd14687d20a3d87ba28ccbb591))
* quote keys with dots to not break ini file type ([f13668b](https://github.com/Levizor/nix-scribe/commit/f13668b1203d83e706ef98bf7eac1cb8e2137e3b))
* refactor sudo module to pure python parser ([#35](https://github.com/Levizor/nix-scribe/issues/35)) ([f298873](https://github.com/Levizor/nix-scribe/commit/f298873d8f4b077516806ef1a8a2dc002cc9de91))
* refactor sudo module to pure python parser ([#35](https://github.com/Levizor/nix-scribe/issues/35)) ([5f73fc4](https://github.com/Levizor/nix-scribe/commit/5f73fc4394e8e3c54f9f138608aa2d517c88e635))
* remove . (test ci) ([079a4b0](https://github.com/Levizor/nix-scribe/commit/079a4b0b4da11d8e859746f54a2306fa32808af7))
* remove print from tests ([dce30fa](https://github.com/Levizor/nix-scribe/commit/dce30fa43bed6bbde0b2937437feaa0ef48a4225))
* remove unused tests ([f76dfec](https://github.com/Levizor/nix-scribe/commit/f76dfec22d294c62299d6612c79b4fcd2fb0317a))
* replace runtime proc ipv6 check with persistent sysctl config ([#68](https://github.com/Levizor/nix-scribe/issues/68)) ([a31eda5](https://github.com/Levizor/nix-scribe/commit/a31eda57719ba03e458b61370de0935718455f58))
* replace runtime proc ipv6 check with persistent sysctl config ([#68](https://github.com/Levizor/nix-scribe/issues/68)) ([e4d15ed](https://github.com/Levizor/nix-scribe/commit/e4d15ed9bb088c635f073f7411f62841b9748bba))
* **tests:** remove problematic /usr/lib symlink in mock system root ([1fbeb63](https://github.com/Levizor/nix-scribe/commit/1fbeb63c2a55231e4c9492b8fc1cd1104ab90106))
* use set ([#51](https://github.com/Levizor/nix-scribe/issues/51)) ([ed08003](https://github.com/Levizor/nix-scribe/commit/ed08003c0dce90fe25b150335cfbd7a6428e89f5))
* use set for arguments field in optino block, then just sort it in the nixfile writing ([#49](https://github.com/Levizor/nix-scribe/issues/49)) ([279cc41](https://github.com/Levizor/nix-scribe/commit/279cc41d965ce9a5c61d875176d8c5d06012ded7))


### Documentation

* add development skills ([1b7f79f](https://github.com/Levizor/nix-scribe/commit/1b7f79fc08b112739ba1c494a24421d67f5ecb7e))
* add GEMINI.md project standards and agent instructions ([#82](https://github.com/Levizor/nix-scribe/issues/82)) ([8612752](https://github.com/Levizor/nix-scribe/commit/8612752b8e3bdef3f35ed36cabdaf8daf20f6fa2))
* add nix-scribe development skills ([bdd49cc](https://github.com/Levizor/nix-scribe/commit/bdd49cc3ad8c5475848bf31ad05b19b091b8d70f))
* update documentation for scanner/mapper architecture and cli options ([#108](https://github.com/Levizor/nix-scribe/issues/108)) ([241dcab](https://github.com/Levizor/nix-scribe/commit/241dcabad047225b1524fc4b61d444264f2bc00f))
* update GEMINI.md with comprehensive user preferences and standards ([#84](https://github.com/Levizor/nix-scribe/issues/84)) ([f1c2a3f](https://github.com/Levizor/nix-scribe/commit/f1c2a3fbeb685eae65aca91fba98e7c720d27d55))
