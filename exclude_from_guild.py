import argparse
import html
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote_plus

import requests

from invite_guild import TIBIA_GUILDS_URL, build_session, read_characters, read_cookie


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip().lower()


def guild_page_url(guild_name: str) -> str:
    return f"{TIBIA_GUILDS_URL}&page=view&GuildName={quote_plus(guild_name)}"


def character_is_in_guild(
    session: requests.Session,
    guild_name: str,
    character: str,
    timeout: int,
) -> tuple[bool, str]:
    response = session.get(guild_page_url(guild_name), timeout=timeout)

    if response.status_code != 200:
        return False, f"falhou: HTTP {response.status_code} ao consultar guild"

    body = response.text
    body_lower = body.lower()

    if "cloudflare" in body_lower or "cf-browser-verification" in body_lower:
        return False, "falhou: Cloudflare bloqueou ou pediu verificacao"

    encoded_name = quote_plus(character).lower()
    link_pattern = f"subtopic=characters&name={encoded_name}"
    if link_pattern in body_lower:
        return True, "encontrado na guild"

    normalized_body = normalize_text(re.sub(r"<[^>]+>", " ", body))
    normalized_character = normalize_text(character)
    if normalized_character in normalized_body:
        return True, "encontrado na guild"

    return False, "nao encontrado na guild"


def exclude_character(
    session: requests.Session,
    guild_name: str,
    character: str,
    rank: str,
    timeout: int,
) -> requests.Response:
    payload = {
        "character": character,
        "newrank": rank,
        "newtitle": "",
        "action": "exclude",
        "page": "promote",
        "GuildName": guild_name,
    }
    return session.post(TIBIA_GUILDS_URL, data=payload, timeout=timeout)


def classify_exclude_response(response: requests.Response) -> str:
    body = response.text.lower()

    if response.status_code != 200:
        return f"falhou: HTTP {response.status_code}"

    if "cloudflare" in body or "cf-browser-verification" in body:
        return "falhou: Cloudflare bloqueou ou pediu verificacao"

    if "secure session" in body and "login" in body:
        return "falhou: sessao/cookie expirado"

    if "exclude" in body and ("success" in body or "removed" in body):
        return "possivel sucesso"

    if "not a member" in body or "no member" in body:
        return "nao estava na guild"

    return "resposta recebida; confira no site se foi removido"


def run_excludes(
    characters: list[str],
    guild_name: str,
    cookie: str,
    rank: str,
    delay: float,
    timeout: int,
    dry_run: bool,
    skip_check: bool,
) -> int:
    session = build_session(cookie)
    failures = 0

    for index, character in enumerate(characters, start=1):
        prefix = f"[{index}] {character}"

        try:
            if not skip_check:
                found, check_status = character_is_in_guild(
                    session=session,
                    guild_name=guild_name,
                    character=character,
                    timeout=timeout,
                )
                if not found:
                    print(f"{prefix}: {check_status}; nao excluido")
                    if check_status.startswith("falhou"):
                        failures += 1
                    continue

            if dry_run:
                print(f"{prefix}: encontrado; dry-run, exclusao nao enviada")
                continue

            response = exclude_character(
                session=session,
                guild_name=guild_name,
                character=character,
                rank=rank,
                timeout=timeout,
            )
            status = classify_exclude_response(response)
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
        description="Verifica membros na guild e exclui quem estiver nela."
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
        "--rank",
        default="3",
        help="Valor enviado em newrank. Padrao: 3",
    )
    parser.add_argument(
        "--delay",
        default=2.0,
        type=float,
        help="Pausa em segundos entre personagens. Padrao: 2.0",
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
        help="Consulta a guild, mas nao envia exclusao.",
    )
    parser.add_argument(
        "--skip-check",
        action="store_true",
        help="Nao consulta se esta na guild; tenta excluir direto.",
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

    failures = run_excludes(
        characters=characters,
        guild_name=args.guild,
        cookie=cookie,
        rank=args.rank,
        delay=args.delay,
        timeout=args.timeout,
        dry_run=args.dry_run,
        skip_check=args.skip_check,
    )

    if failures:
        print(f"Finalizado com {failures} falha(s).")
        return 1

    print("Finalizado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
