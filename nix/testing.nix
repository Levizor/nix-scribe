{ ... }:
{
  perSystem =
    {
      pkgs,
      self',
      ...
    }:
    let
      setupTestUbuntu = pkgs.writeShellApplication {
        name = "setup-test-ubuntu";
        runtimeInputs = with pkgs; [
          coreutils
          gnutar
        ];
        text = ''
          TARGET_DIR="./test-root/ubuntu"
          IMAGE="ubuntu:latest"
          PACKAGES="curl fastfetch"
          CLEAN=0

          while [ "$#" -gt 0 ]; do
            case "$1" in
              -t|--target)
                TARGET_DIR="$2"
                shift 2
                ;;
              -i|--image)
                IMAGE="$2"
                shift 2
                ;;
              -p|--packages)
                PACKAGES="$2"
                shift 2
                ;;
              -c|--clean)
                CLEAN=1
                shift
                ;;
              -h|--help)
                echo "Usage: setup-test-ubuntu [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  -t, --target DIR      Target directory for rootfs export (default: ./test-root/ubuntu)"
                echo "  -i, --image IMAGE     Base container image (default: ubuntu:latest)"
                echo "  -p, --packages PKGS   Space-separated packages to install (default: 'curl fastfetch')"
                echo "  -c, --clean           Remove target directory before exporting"
                echo "  -h, --help            Show this help"
                exit 0
                ;;
              *)
                echo "Unknown option: $1" >&2
                exit 1
                ;;
            esac
          done

          if command -v podman >/dev/null 2>&1; then
            CONTAINER_CLI="podman"
          elif command -v docker >/dev/null 2>&1; then
            CONTAINER_CLI="docker"
          else
            echo "Error: Neither podman nor docker found in PATH." >&2
            exit 1
          fi

          CANONICAL_TARGET="$(realpath -m "$TARGET_DIR")"
          REPO_ROOT="$(pwd)"

          case "$CANONICAL_TARGET" in
            /|/root|/home|/home/*|/etc|/etc/*|/usr|/usr/*|/var|/var/*|/bin|/sbin|/boot|/boot/*|/sys|/proc|/dev|/nix|/nix/*|"$HOME")
              echo "Error: Refusing to use protected directory as target: $CANONICAL_TARGET" >&2
              exit 1
              ;;
          esac

          if [ "$CLEAN" -eq 1 ] && [ -d "$TARGET_DIR" ]; then
            if [ "$CANONICAL_TARGET" = "$REPO_ROOT" ] || [ "$CANONICAL_TARGET" = "$REPO_ROOT/test-root" ]; then
              echo "Error: Safety guard: Refusing to clean top-level directory: $CANONICAL_TARGET" >&2
              exit 1
            fi
            if [ "''${CANONICAL_TARGET#"$REPO_ROOT/test-root/"}" = "$CANONICAL_TARGET" ] && [ "''${CANONICAL_TARGET#/tmp/}" = "$CANONICAL_TARGET" ]; then
              echo "Error: Safety guard: --clean is only permitted for subdirectories inside ./test-root/ or /tmp/" >&2
              echo "Target $CANONICAL_TARGET is outside permitted directories." >&2
              exit 1
            fi
            echo "Cleaning existing target directory: $TARGET_DIR"
            rm -rf "$TARGET_DIR"
          fi

          echo "Using container runtime: $CONTAINER_CLI"
          echo "Target directory: $TARGET_DIR"
          echo "Image: $IMAGE"

          mkdir -p "$TARGET_DIR"

          CONTAINER_NAME="nix-scribe-setup-$$"

          cleanup() {
            echo "Cleaning up container $CONTAINER_NAME..."
            "$CONTAINER_CLI" rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
          }
          trap cleanup EXIT

          echo "Creating and provisioning container from $IMAGE..."
          INSTALL_CMD="DEBIAN_FRONTEND=noninteractive apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y $PACKAGES"

          if [ -n "$PACKAGES" ]; then
            "$CONTAINER_CLI" run --name "$CONTAINER_NAME" "$IMAGE" sh -c "$INSTALL_CMD"
          else
            "$CONTAINER_CLI" create --name "$CONTAINER_NAME" "$IMAGE"
          fi

          echo "Exporting rootfs to $TARGET_DIR..."
          "$CONTAINER_CLI" export "$CONTAINER_NAME" | tar -C "$TARGET_DIR" -xf -

          echo "Done! Target rootfs is ready at: $TARGET_DIR"
          echo "You can now run: nix run . -- $TARGET_DIR -o nix-config"
        '';
      };

      testUbuntu = pkgs.writeShellApplication {
        name = "test-ubuntu";
        runtimeInputs = with pkgs; [
          coreutils
        ];
        text = ''
          TARGET_DIR="./test-root/ubuntu"
          OUTPUT_DIR="./ubuntu-config"

          if [ ! -d "$TARGET_DIR" ] || [ ! -f "$TARGET_DIR/etc/os-release" ]; then
            echo "Target test directory $TARGET_DIR does not exist or is empty. Setting up..."
            ${pkgs.lib.getExe setupTestUbuntu} --target "$TARGET_DIR"
          fi

          echo "Running nix-scribe on $TARGET_DIR..."
          ${pkgs.lib.getExe' self'.packages.default "nix-scribe"} --confirm "$TARGET_DIR" -o "$OUTPUT_DIR" "$@"
        '';
      };
    in
    {
      packages.setup-test-ubuntu = setupTestUbuntu;
      packages.test-ubuntu = testUbuntu;

      apps.setup-test-ubuntu = {
        type = "app";
        program = pkgs.lib.getExe setupTestUbuntu;
      };

      apps.test-ubuntu = {
        type = "app";
        program = pkgs.lib.getExe testUbuntu;
      };
    };
}
