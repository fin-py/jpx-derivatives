from pathlib import Path

base_dir = Path()
config_dir = base_dir / "config"
data_dir = base_dir / "data"
data_dir.mkdir(exist_ok=True)
