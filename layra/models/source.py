from dataclasses import dataclass
from urllib.parse import urljoin

from typing_extensions import Literal


@dataclass(frozen=True)
class Source:
    url: str
    repository: str
    branch: str
    type: Literal["profile", "component"]

    @property
    def https(self) -> str:
        return "https://{}.git".format(urljoin(self.url + "/", self.repository))

    @property
    def ssh(self) -> str:
        return "git@{}:{}.git".format(self.url, self.repository)
