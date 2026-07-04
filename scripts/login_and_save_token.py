#!/usr/bin/env python3
"""
login_and_save_token.py — RULEAZA O SINGURA DATA, LOCAL PE CALCULATORUL TAU.
NU rula asta in GitHub Actions.

Se autentifica interactiv la Garmin Connect (rezolvi tu MFA daca e activat),
apoi salveaza tokenstore-ul rezultat intr-un fisier text (base64), pe care
il pui ca GitHub Secret: GARMIN_TOKENSTORE_B64.

Tokenul tine cateva luni fara sa mai fie nevoie de login din nou.
"""
import base64
import getpass
import io
import tarfile
from pathlib import Path

from garminconnect import Garmin

TOKENSTORE_DIR = Path.home() / ".garminconnect"


def main():
    email = input("Email Garmin: ").strip()
    password = getpass.getpass("Parola Garmin: ")

    client = Garmin(email=email, password=password)
    client.login(str(TOKENSTORE_DIR))  # aici iti cere codul MFA daca ai activat

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        tar.add(TOKENSTORE_DIR, arcname=".")
    b64 = base64.b64encode(buf.getvalue()).decode()

    out = Path("tokenstore.b64.txt")
    out.write_text(b64)

    print(f"\nGata. Login reusit.")
    print(f"Continutul din '{out}' il copiezi integral in GitHub Secret: GARMIN_TOKENSTORE_B64")
    print("IMPORTANT: fisierul tokenstore.b64.txt e echivalent cu parola ta de Garmin.")
    print("Nu il urca niciodata pe GitHub, nu il trimite nicaieri — sterge-l dupa ce ai pus secretul.")


if __name__ == "__main__":
    main()
