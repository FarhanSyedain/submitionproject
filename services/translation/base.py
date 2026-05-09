"""Abstract translator interface."""
from __future__ import annotations


class BaseTranslator:
    provider: str = "base"

    def translate(
        self, text: str, *, target_lang: str = "ks", source_lang: str = "en"
    ) -> str:
        raise NotImplementedError

    def translate_many(
        self,
        texts: list[str],
        *,
        target_lang: str = "ks",
        source_lang: str = "en",
    ) -> list[str]:
        """Default: translate items one by one. Subclasses can batch."""
        return [
            self.translate(t, target_lang=target_lang, source_lang=source_lang)
            for t in texts
        ]


# ISO codes / display names / script hint for languages we expose in the UI.
# `script_instruction` is appended to the system prompt so the model picks
# the right writing system (otherwise it tends to romanise low-resource
# languages like Kashmiri).
LANGUAGES: dict[str, dict[str, str]] = {
    "en": {
        "name": "English",
        "native": "English",
        "script_instruction": "",
    },
    "ks": {
        "name": "Kashmiri",
        "native": "کٲشُر",
        "script_instruction": (
            "Write the output in the official Kashmiri Perso-Arabic script "
            "(کٲشُر). Do NOT use Roman/Latin transliteration."
        ),
    },
}
