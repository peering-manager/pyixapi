import json
from pathlib import Path
from typing import Any, Optional


class Response(object):
    def __init__(
        self,
        fixture: Optional[str],
        status_code: int = 200,
        ok: bool = True,
        content: Optional[Any] = None,
    ) -> None:
        self.status_code = status_code
        self.content = json.dumps(content) if content else self.load_fixture(fixture)
        self.ok = ok

    def load_fixture(self, path: str) -> str:
        f = Path("tests/fixtures") / path
        return f.read_text()

    def json(self) -> Any:
        return json.loads(self.content)
