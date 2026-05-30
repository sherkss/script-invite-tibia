import argparse
import sys
import time
from pathlib import Path

import requests

from exclude_from_guild import (
    character_is_in_guild,
    classify_exclude_response,
    exclude_character,
)
from invite_guild import (
    build_session,
    classify_response,
    invite_character,
    read_characters,
    read_cookie,
)


def move_characters(
    characters: list[str],
    old_guild: str,
    new_guild: str,
    old_cookie: str,
    new_cookie: str,
    rank: str,
    delay: float,
    timeout: int,
    dry_run: bool,
    invite_when_not_in_old: bool,
) -> int:
    old_session = build_session(old_cookie)
    new_session = build_session(new_cookie)
    failures = 0

    for index, character in enumerate(characters, start=1):
        prefix = f"[{index}] {character}"

        try:
            found, check_status = character_is_in_guild(
                session=old_session,
                guild_name=old_guild,
                character=character,
                timeout=timeout,
            )

            if check_status.startswith("falhou"):
                print(f"{prefix}: {check_status}; convite nao enviado")
                failures += 1
                continue

            if found:
                if dry_run:
                    print(
                        f"{prefix}: encontrado em {old_guild}; "
                        f"dry-run, excluiria e depois convidaria em {new_guild}"
                    )
                    continue

                exclude_response = exclude_character(
                    session=old_session,
                    guild_name=old_guild,
                    character=character,
                    rank=rank,
                    timeout=timeout,
                )
                exclude_status = classify_exclude_response(exclude_response)
                print(f"{prefix}: exclusao em {old_guild}: {exclude_status}")

                if "falhou" in exclude_status:
                    failures += 1
                    continue

                if delay > 0:
                    time.sleep(delay)
            elif not invite_when_not_in_old:
                print(
                    f"{prefix}: nao encontrado em {old_guild}; "
                    "convite nao enviado"
                )
                continue
            elif dry_run:
                print(
                    f"{prefix}: nao encontrado em {old_guild}; "
                    f"dry-run, convidaria em {new_guild}"
                )
                continue

            invite_response = invite_character(
                session=new_session,
                guild_name=new_guild,
                character=character,
                timeout=timeout,
            )
            invite_status = classify_response(invite_response)
            print(f"{prefix}: convite em {new_guild}: {invite_status}")

            if "falhou" in invite_status:
                failures += 1
        except requests.RequestException as exc:
            failures += 1
            print(f"{prefix}: falhou: {exc}")

        if delay > 0:
            time.sleep(delay)

    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verifica personagens na guild antiga, exclui se estiverem nela "
            "e depois convida para a guild nova."
        )
    )
    parser.add_argument("--old-guild", required=True, help="Nome da guild antiga.")
    parser.add_argument("--new-guild", required=True, help="Nome da guild nova.")
    parser.add_argument(
        "--characters",
        default="characters.txt",
        type=Path,
        help="Arquivo com um personagem por linha. Padrao: characters.txt",
    )
    parser.add_argument(
        "--cookie-file",
        type=Path,
        help=(
            "Arquivo contendo o valor completo do header Cookie. "
            "Usado nos dois passos se --old-cookie-file/--new-cookie-file "
            "nao forem informados."
        ),
    )
    parser.add_argument(
        "--old-cookie-file",
        type=Path,
        help="Cookie da conta/sessao que remove da guild antiga.",
    )
    parser.add_argument(
        "--new-cookie-file",
        type=Path,
        help="Cookie da conta/sessao que invita na guild nova.",
    )
    parser.add_argument(
        "--rank",
        default="3",
        help="Valor enviado em newrank ao excluir da guild antiga. Padrao: 3",
    )
    parser.add_argument(
        "--delay",
        default=2.0,
        type=float,
        help="Pausa em segundos entre acoes. Padrao: 2.0",
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
        help="Mostra o que faria, sem excluir nem convidar.",
    )
    parser.add_argument(
        "--invite-when-not-in-old",
        action="store_true",
        help="Convida para a nova guild mesmo se nao encontrar na antiga.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        characters = read_characters(args.characters)
        old_cookie_file = args.old_cookie_file or args.cookie_file
        new_cookie_file = args.new_cookie_file or args.cookie_file

        if not old_cookie_file or not new_cookie_file:
            raise ValueError(
                "Informe --old-cookie-file e --new-cookie-file, "
                "ou use --cookie-file para os dois passos."
            )

        old_cookie = read_cookie(old_cookie_file)
        new_cookie = read_cookie(new_cookie_file)
    except (OSError, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    failures = move_characters(
        characters=characters,
        old_guild=args.old_guild,
        new_guild=args.new_guild,
        old_cookie=old_cookie,
        new_cookie=new_cookie,
        rank=args.rank,
        delay=args.delay,
        timeout=args.timeout,
        dry_run=args.dry_run,
        invite_when_not_in_old=args.invite_when_not_in_old,
    )

    if failures:
        print(f"Finalizado com {failures} falha(s).")
        return 1

    print("Finalizado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
