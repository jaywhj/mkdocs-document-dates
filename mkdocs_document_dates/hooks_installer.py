import os
import sys
import subprocess
from pathlib import Path

DEFAULT_HOOKS_DIRNAME = ".githooks"


class HookInstallError(Exception):
    pass


def get_repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise HookInstallError("This command must be run inside a Git repo. Please cd into your project directory and try again.")
    return Path(result.stdout.strip())


def ensure_hooks_dir(repo_root: Path) -> Path:
    hooks_dir = repo_root / DEFAULT_HOOKS_DIRNAME
    try:
        hooks_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(hooks_dir, 0o755)
    except Exception as e:
        raise HookInstallError(f"Failed to create hooks directory: {hooks_dir} ({e})")
    return hooks_dir


def write_hooks(source_dir: Path, target_dir: Path):
    if not source_dir.exists():
        raise HookInstallError(f"Hooks source directory not found: {source_dir}")

    shebang = f"#!{sys.executable}"

    try:
        for file in source_dir.iterdir():
            if file.name.startswith(".") or not file.is_file():
                continue

            content = file.read_text(encoding="utf-8")

            if content.startswith("#!"):
                os.linesep
                content = shebang + "\n" + content.split("\n", 1)[1]
            else:
                content = shebang + "\n" + content

            target = target_dir / file.name
            target.write_text(content, encoding="utf-8")
            os.chmod(target, 0o755)

    except Exception as e:
        raise HookInstallError(f"Failed to write hook files: {e}")


def set_hooks_path(repo_root: Path, hooks_dir: Path):
    rel_path = hooks_dir.relative_to(repo_root).as_posix()

    # # 配置自定义合并驱动
    # script_path = hooks_dir / 'json_merge_driver.py'
    # subprocess.run(['git', 'config', 'merge.custom_json_merge.name', 'Custom JSON merge driver'], check=True)
    # subprocess.run(['git', 'config', 'merge.custom_json_merge.driver', f'"{sys.executable}" "{script_path}" %O %A %B'], check=True)

    result = subprocess.run(
        ["git", "config", "core.hooksPath", rel_path],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise HookInstallError(result.stderr.strip() or "Failed to set hooksPath")


def install():
    try:
        repo_root = get_repo_root()
        hooks_dir = ensure_hooks_dir(repo_root)

        source_dir = Path(__file__).parent / "hooks"

        write_hooks(source_dir, hooks_dir)
        set_hooks_path(repo_root, hooks_dir)

        print(f"✔ Hooks installed successfully: {hooks_dir}")

    except HookInstallError as e:
        print(f"✖ Installation failed: {e}", file=sys.stderr)
    except Exception as e:
        print(f"✖ Unexpected error: {e}", file=sys.stderr)


if __name__ == "__main__":
    install()