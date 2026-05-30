import argparse
import os
import sys
import time
from pathlib import Path
from typing import Iterable

import requests


TIBIA_GUILDS_URL = "https://www.tibia.com/community/?subtopic=guilds"


def read_characters(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de personagens nao encontrado: {path}")

    characters: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        name = line.strip()
        if not name or name.startswith("#"):
            continue
        characters.append(name)

    if not characters:
        raise ValueError("A lista de personagens esta vazia.")

    return characters


def read_cookie(cookie_file: Path | None) -> str:
    if cookie_file:
        cookie = cookie_file.read_text(encoding="utf-8").strip()
    else:
        cookie = os.environ.get("TIBIA_COOKIE", "").strip()

    if not cookie:
        raise ValueError(
            "Informe o cookie pela variavel TIBIA_COOKIE ou use --cookie-file."
        )

    return cookie


def build_session(cookie: str) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,image/apng,*/*;q=0.8"
            ),
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Cache-Control": "max-age=0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": cookie,
            "Origin": "https://www.tibia.com",
            "Referer": TIBIA_GUILDS_URL,
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/148.0.0.0 Safari/537.36"
            ),
        }
    )
    return session


def invite_character(
    session: requests.Session,
    guild_name: str,
    character: str,
    timeout: int,
) -> requests.Response:
    payload = {
        "character": character,
        "page": "invite",
        "invitation": "yes",
        "GuildName": guild_name,
    }
    return session.post(TIBIA_GUILDS_URL, data=payload, timeout=timeout)


def classify_response(response: requests.Response) -> str:
    body = response.text.lower()

    if response.status_code != 200:
        return f"falhou: HTTP {response.status_code}"

    if "cloudflare" in body or "cf-browser-verification" in body:
        return "falhou: Cloudflare bloqueou ou pediu verificacao"

    if "secure session" in body and "login" in body:
        return "falhou: sessao/cookie expirado"

    if "invitation" in body and ("success" in body or "invited" in body):
        return "possivel sucesso"

    if "already" in body and "guild" in body:
        return "possivel ja convidado ou ja em guild"

    return "resposta recebida; confira o HTML salvo/logado se necessario"


def run_invites(
    characters: Iterable[str],
    guild_name: str,
    cookie: str,
    delay: float,
    timeout: int,
    dry_run: bool,
) -> int:
    session = build_session(cookie)
    failures = 0

    for index, character in enumerate(characters, start=1):
        prefix = f"[{index}] {character}"

        if dry_run:
            print(f"{prefix}: dry-run, nao enviado")
            continue

        try:
            response = invite_character(session, guild_name, character, timeout)
            status = classify_response(response)
            print(f"{prefix}: {status}")
            if "falhou" in status:
                failures += 1
        except requests.RequestException as exc:
            failures += 1
            print(f"{prefix}: falhou: {exc}")

        if delay > 0:
            time.sleep(delay)

    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Envia convites de guild no tibia.com para varios personagens."
    )
    parser.add_argument("--guild", required=True, help="Nome da guild.")
    parser.add_argument(
        "--characters",
        default="characters.txt",
        type=Path,
        help="Arquivo com um personagem por linha. Padrao: characters.txt",
    )
    parser.add_argument(
        "--cookie-file",
        type=Path,
        help="Arquivo contendo o valor completo do header Cookie.",
    )
    parser.add_argument(
        "--delay",
        default=2.0,
        type=float,
        help="Pausa em segundos entre convites. Padrao: 2.0",
    )
    parser.add_argument(
        "--timeout",
        default=30,
        type=int,
        help="Timeout HTTP em segundos. Padrao: 30",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostra o que seria enviado, sem fazer POST.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        characters = read_characters(args.characters)
        cookie = read_cookie(args.cookie_file)
    except (OSError, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    failures = run_invites(
        characters=characters,
        guild_name=args.guild,
        cookie=cookie,
        delay=args.delay,
        timeout=args.timeout,
        dry_run=args.dry_run,
    )

    if failures:
        print(f"Finalizado com {failures} falha(s).")
        return 1

    print("Finalizado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
