import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class FileService:
    logger = logging.getLogger(__name__)

    def read_json_payload(self, path: Path) -> list[dict[str, Any]]:
        try:
            with path.open("r") as file:
                data: list[dict[str, Any]] = json.load(file)
        except Exception as err:
            self.logger.error(f"Couldn't read from file {path.resolve().as_posix()}. Error: {str(err)}")
            raise
        return data

    def write_to_file(self, data: str, path: Path):
        self.logger.info(f"Writing data to file {path.resolve().as_posix()}...")
        try:
            with path.resolve().open("w") as file:
                file.write(data)
        except Exception as err:
            self.logger.error(f"Couldn't write to file {path.resolve().as_posix()}. Error: {str(err)}")
            raise

    def json_serialize(self, data: BaseModel) -> str:
        self.logger.info(f"Serializing model {data.__class__.__name__}...")
        return data.model_dump_json(indent=2)

    def append_timestamp(self, path: Path) -> Path:
        now = datetime.now()
        timestamp = now.strftime("_%Y%m%d-%H%M%S")
        self.logger.info(f"Appending current timestamp to path: {timestamp}...")
        return path.with_stem(path.stem + timestamp)
