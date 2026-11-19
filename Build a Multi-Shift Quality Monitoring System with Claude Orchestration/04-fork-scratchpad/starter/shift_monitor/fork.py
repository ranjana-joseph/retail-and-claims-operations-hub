from pathlib import Path
import shutil
from collections.abc import Iterable

from .scratchpad import Scratchpad


def fork_for_hypothesis(base_hot_state_path: Path, hypothesis_id: str, forks_root: Path) -> Path:
    fork_dir = forks_root / hypothesis_id
    fork_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(base_hot_state_path, fork_dir / "hot_state.json")
    return fork_dir


def merge_findings(scratchpad_paths: Iterable[Path], main_scratchpad: Path) -> None:
    main = Scratchpad(main_scratchpad)
    for path in scratchpad_paths:
        if not path.exists():
            continue
        for entry in Scratchpad(path).read():
            main.append(entry)