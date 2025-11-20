# Como Desabilitar o Deploy Automático da Vercel

## Problema
A Vercel continua fazendo deploy automático mesmo com `vercel.json` configurado, porque a **integração Git precisa ser desabilitada no dashboard**.

## Solução

### 1. Desabilitar Auto-Deploy na Vercel Dashboard

1. Acesse: https://vercel.com/flavio-lopes-projects-87104ba4/brazillian-cds-datafeeder-v2/settings/git

2. Na seção **"Git Integration"**:
   - Clique em **"Disconnect"** ou **"Remove Git Integration"**
   - Ou vá em **"Deployment Protection"** → Desabilite "Automatically deploy all branches"

3. Ou na seção **"Production Branch"**:
   - Desmarque **"Automatically build and deploy the latest commit"**

### 2. Configurar GitHub Secrets

Se ainda não configurou, adicione os secrets no GitHub:

1. Acesse: https://github.com/ideiasfactory/brazillian_cds_datafeeder_v2/settings/secrets/actions

2. Adicione os seguintes secrets (clique em "New repository secret"):

   - **VERCEL_TOKEN**
     - Obtenha em: https://vercel.com/account/tokens
     - Crie um novo token com acesso ao projeto
   
   - **VERCEL_ORG_ID**
     - Execute localmente: `vercel link`
     - Ou encontre em: `.vercel/project.json` após rodar `vercel link`
     - Ou na URL da Vercel: `https://vercel.com/TEAM_ID/...`
   
   - **VERCEL_PROJECT_ID**
     - Execute localmente: `vercel link`
     - Ou encontre em: `.vercel/project.json`
     - Ou em: https://vercel.com/flavio-lopes-projects-87104ba4/brazillian-cds-datafeeder-v2/settings

### 3. Verificar Workflow GitHub Actions

O workflow `.github/workflows/deploy-vercel.yml` já está configurado para:
- Rodar APENAS após os testes passarem com sucesso
- Fazer deploy via CLI da Vercel (não via Git)

### 4. Testar o Fluxo

Após desabilitar na Vercel:

1. Faça um push para `master`
2. Verifique que:
   - ✅ GitHub Actions roda os testes
   - ✅ Se testes passarem, GitHub Actions faz deploy via CLI
   - ❌ Vercel NÃO inicia deploy automático via Git

## Alternativa: Manter Git Integration mas com Regras

Se quiser manter a integração Git (para preview deployments em PRs):

1. Na Vercel Dashboard → Settings → Git
2. Em **"Ignored Build Step"**: já está configurado via `ignoreCommand` no `vercel.json`
3. O script `scripts/vercel-ignore-build.sh` ignora builds em `master`/`main`

**Mas a melhor prática é**: 
- **Desconectar Git Integration** para branches de produção
- **Usar GitHub Actions** para controlar deploys de produção
- **Manter Vercel** para preview deployments (se necessário)

## Comandos Úteis

```bash
# Obter IDs do projeto
vercel link

# Ver arquivo com IDs
cat .vercel/project.json

# Fazer deploy manual de teste
vercel --prod

# Ver logs de deployment
vercel logs
```

## Status Esperado

✅ **Correto:**
```
Push → GitHub Actions Tests → (Pass) → GitHub Actions Deploy → Vercel Production
```

❌ **Incorreto (situação atual):**
```
Push → GitHub Actions Tests (paralelo com) Vercel Auto-Deploy
```

## Links Úteis

- [Vercel Project Settings](https://vercel.com/flavio-lopes-projects-87104ba4/brazillian-cds-datafeeder-v2/settings)
- [GitHub Actions Secrets](https://github.com/ideiasfactory/brazillian_cds_datafeeder_v2/settings/secrets/actions)
- [Vercel Tokens](https://vercel.com/account/tokens)
