# Invite Guild Tibia

Script Python para enviar convites de guild no `tibia.com` para varios personagens.

## Instalar

```powershell
python -m pip install -r requirements.txt
```

## Preparar a lista

Crie um arquivo `characters.txt` com um personagem por linha:

```txt
Jadebra metabatida
Outro Boneco
```

## Informar o cookie

Copie o valor completo do header `Cookie` do navegador enquanto estiver logado no Tibia.

Opcao 1, variavel de ambiente:

```powershell
$env:TIBIA_COOKIE='CookieConsentPreferences=...; SecureSessionID=...; DeviceCookie=...'
```

Opcao 2, arquivo local:

```powershell
notepad cookie.txt
```

Cole o cookie inteiro em uma unica linha.

## Testar sem enviar

```powershell
python .\invite_guild.py --guild "Testebras" --characters .\characters.txt --cookie-file .\cookie.txt --dry-run
```

## Enviar convites

```powershell
python .\invite_guild.py --guild "Testebras" --characters .\characters.txt --cookie-file .\cookie.txt --delay 2
```

## Verificar e excluir membros da guild

Para consultar a guild e ver quem seria excluido, sem enviar o POST:

```powershell
python .\exclude_from_guild.py --guild "Testebras" --characters .\characters.txt --cookie-file .\cookie.txt --dry-run
```

Para excluir de verdade apenas quem for encontrado na guild:

```powershell
python .\exclude_from_guild.py --guild "Testebras" --characters .\characters.txt --cookie-file .\cookie.txt --delay 2
```

Se quiser tentar excluir direto sem consultar a pagina da guild antes:

```powershell
python .\exclude_from_guild.py --guild "Testebras" --characters .\characters.txt --cookie-file .\cookie.txt --skip-check --delay 2
```

## Mover da guild antiga para a nova

Esse fluxo verifica primeiro se o personagem esta na guild antiga. Se estiver, exclui da antiga e depois convida para a nova.

Teste sem excluir nem convidar:

```powershell
python .\move_guild.py --old-guild "GuildAntiga" --new-guild "Testebras" --characters .\characters.txt --cookie-file .\cookie.txt --dry-run
```

Executar de verdade:

```powershell
python .\move_guild.py --old-guild "GuildAntiga" --new-guild "Testebras" --characters .\characters.txt --cookie-file .\cookie.txt --delay 2
```

Por padrao, se o personagem nao for encontrado na guild antiga, ele nao sera convidado para a nova. Para convidar mesmo assim:

```powershell
python .\move_guild.py --old-guild "GuildAntiga" --new-guild "Testebras" --characters .\characters.txt --cookie-file .\cookie.txt --invite-when-not-in-old --delay 2
```

Se o Tibia ou o Cloudflare bloquear a requisicao, abra o site no navegador, faca login novamente, copie um cookie novo e rode de novo.
