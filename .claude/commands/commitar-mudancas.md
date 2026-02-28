---
description: Commitar e dar Push nas mudanças feitas do repositório
---

# Commitar Mudanças

Realiza o fluxo completo de commit e push das mudanças locais do repositório FINOVA.

## Pipeline

Execute os seguintes passos em ordem:

1. **Git pull** — sincroniza com o remoto antes de qualquer coisa:
   ```bash
   git pull
   ```
   - Se houver conflitos, pare e informe o usuário detalhando quais arquivos estão em conflito.

2. **Verificar o status** — identifica os arquivos modificados:
   ```bash
   git status
   git diff --stat
   ```

3. **Analisar as mudanças** — leia o diff completo dos arquivos modificados para entender o que foi alterado:
   ```bash
   git diff
   git diff --cached
   ```

4. **Adicionar os arquivos modificados** — adiciona apenas arquivos rastreados (não adiciona `.env` ou arquivos ignorados):
   ```bash
   git add -u
   ```
   - Nunca adicione `.env`, `.venv/`, `*.db`, ou qualquer arquivo listado no `.gitignore`.
   - Se houver arquivos novos não rastreados que devam ser incluídos, adicione-os individualmente.

5. **Criar o commit** — escreva uma mensagem clara e concisa resumindo as mudanças reais encontradas no diff:
   - Use o formato: `tipo: descrição curta`
   - Tipos válidos: `feat`, `fix`, `refactor`, `test`, `chore`, `docs`
   - A mensagem deve refletir o que realmente mudou (não use mensagens genéricas)
   - Inclua co-autoria:
   ```bash
   git commit -m "$(cat <<'EOF'
   tipo: descrição das mudanças

   Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
   EOF
   )"
   ```

6. **Git push** — envia para o remoto:
   ```bash
   git push
   ```
   - Se o push falhar por divergência, informe o usuário e NÃO use `--force`.

## Regras de Segurança

- **Nunca** commite `.env`, credenciais, ou segredos.
- **Nunca** use `git push --force` ou `--no-verify`.
- **Nunca** faça amend em commits já publicados.
- Se o repositório estiver limpo (sem mudanças), informe o usuário e encerre.

## Saída Esperada

Confirmação do commit criado (hash + mensagem) e do push realizado com sucesso.
