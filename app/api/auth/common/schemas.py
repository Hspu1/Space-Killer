from enum import StrEnum


class AuthProvider(StrEnum):
    GOOGLE = "google"
    GITHUB = "github"
    TELEGRAM = "telegram"
    YANDEX = "yandex"
    STACKOVERFLOW = "stackoverflow"
