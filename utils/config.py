import dataclasses

import settings_priv


@dataclasses.dataclass()
class Config:
    bot_token: str = settings_priv.TOKEN
    s = settings_priv

    @classmethod
    def load(cls) -> None:
        pass
