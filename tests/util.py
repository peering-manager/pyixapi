import json
from pathlib import Path
from typing import Any


class Response(object):
    def __init__(
        self,
        fixture: str | None,
        status_code: int = 200,
        ok: bool = True,
        content: Any = None,
    ) -> None:
        self.status_code = status_code

        if content:
            self.content = json.dumps(content)
        elif fixture:
            self.content = self.load_fixture(fixture)
        else:
            self.content = ""

        self.ok = ok

    def load_fixture(self, path: str) -> str:
        f = Path("tests/fixtures") / path
        return f.read_text()

    def json(self) -> Any:
        return json.loads(self.content)
