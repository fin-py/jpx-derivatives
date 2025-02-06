import logging
import logging.config
from pathlib import Path

# パッケージのルートディレクトリを取得
base_dir = Path(__file__).resolve().parent.parent.parent

# データディレクトリ
data_dir = base_dir / "data"
data_dir.mkdir(exist_ok=True)


def setup_logging(file_name: str):
    # ロギング設定辞書
    logger_name = Path(file_name).stem
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard",
            },
            # "file": {
            #     "class": "logging.FileHandler",
            #     "level": "INFO",
            #     "formatter": "standard",
            #     "filename": f"{logger_name}.log",
            # },
        },
        "loggers": {
            logger_name: {
                # "handlers": ["console", "file"],
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }

    # 設定の適用
    logging.config.dictConfig(log_config)
    return logger_name
