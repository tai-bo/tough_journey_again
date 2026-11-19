from enum import StrEnum, unique


@unique
class HarmTypeStrEnum(StrEnum):
  SEXUAL = "Sexually suggestive or explicit."
  CSAM = "Exploits, abuses, or endangers children."
  HATE = "Promotes violence against, threatens, or attacks people based on their protected characteristics."
  HARASSMENT = "Harass, intimidate, or bully others."
  DANGEROUS = (
    "Promotes illegal activities, self-harm, or violence towards oneself or others."
  )
  TOXIC = "Rude, disrespectful, or unreasonable."
  VIOLENT = "Depicts violence, gore, or harm against individuals or groups."
  PROFANITY = "Obscene or vulgar language."
  ILLICIT = "Mentions illicit drugs, alcohol, firearms, tobacco, online gambling."
