import json
from pathlib import Path
from typing import Any


class Response:
    def __init__(
        self,
        fixture: str | None,
        status_code: int = 200,
        ok: bool = True,
        content: Any | None = None,
    ) -> None:
        self.status_code = status_code

        if content:
            self.content = json.dumps(content)
        else:
            self.load_fixture(fixture)

        self.ok = ok

    def load_fixture(self, path: str) -> str:
        f = Path("tests/fixtures") / path
        self.content = f.read_text()

    def json(self) -> Any:
        return json.loads(self.content)
