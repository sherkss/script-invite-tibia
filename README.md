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

Se o Tibia ou o Cloudflare bloquear a requisicao, abra o site no navegador, faca login novamente, copie um cookie novo e rode de novo.
