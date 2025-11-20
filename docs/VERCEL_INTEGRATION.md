# Integração Vercel + GitHub Actions

## Situação Atual

O projeto usa a **integração Git nativa da Vercel** com validação de testes via GitHub Actions:

```
Push → GitHub Actions Tests → Vercel Build (aguarda) → Deploy
```

### Como Funciona

1. **GitHub Actions** roda os testes primeiro (workflow `tests.yml`)
2. **Vercel** detecta o push mas aguarda os checks do GitHub
3. Se os **testes passarem** ✅, Vercel inicia o build e deploy
4. Se os **testes falharem** ❌, Vercel cancela o deploy

## Configuração Atual

### ✅ Ativo: Integração Git da Vercel
- **Git Integration**: Conectada ao repositório GitHub
- **Branch de Produção**: `master`
- **Checks Requeridos**: GitHub Actions deve passar antes do deploy
- **Ignore Command**: `bash scripts/vercel-ignore-build.sh` (previne builds duplicados)

### ✅ Ativo: Integração Git da Vercel
- **Git Integration**: Conectada ao repositório GitHub
- **Branch de Produção**: `master`
- **Checks Requeridos**: GitHub Actions deve passar antes do deploy
- **Ignore Command**: `bash scripts/vercel-ignore-build.sh` (previne builds duplicados)

### ❌ Removido: Deploy via GitHub Actions CLI
- O workflow `.github/workflows/deploy-vercel.yml` foi **removido**
- Motivo: Causava **deploys duplicados** (Vercel Git + CLI)
- A integração Git nativa é suficiente e mais simples

## Vantagens da Abordagem Atual

✅ **Simplicidade**: Usa a integração nativa da Vercel  
✅ **Menos Secrets**: Não precisa configurar `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`  
✅ **Deploy Único**: Apenas um deploy por commit  
✅ **Proteção de Testes**: Vercel aguarda checks do GitHub Actions  
✅ **Preview Deployments**: Funcionam automaticamente em PRs  

## Como Verificar o Status

### No GitHub
- Acesse: https://github.com/ideiasfactory/brazillian_cds_datafeeder_v2/actions
- Verifique que apenas o workflow **"Tests"** está rodando

### Na Vercel  
- Acesse: https://vercel.com/flavio-lopes-projects-87104ba4/brazillian-cds-datafeeder-v2
- Verifique que o deploy aguarda o check "Tests" passar

## Se Precisar de Deploy Manual via CLI

Caso queira deploy manual (fora do Git):

```bash
# Instalar Vercel CLI
npm install -g vercel

# Login
vercel login

# Link ao projeto
vercel link

# Deploy para produção
vercel --prod
```

## Configuração de Checks na Vercel (Opcional)

Para garantir que a Vercel aguarde os testes:

## Configuração de Checks na Vercel (Opcional)

Para garantir que a Vercel aguarde os testes:

1. Acesse: https://vercel.com/flavio-lopes-projects-87104ba4/brazillian-cds-datafeeder-v2/settings/git
2. Em **"Deployment Protection"** ou **"Required Checks"**:
   - Marque **"Tests"** como obrigatório
   - Isso força a Vercel a aguardar o workflow de testes

## Fluxo Esperado

✅ **Correto (atual):**
```
Push → GitHub Actions Tests → (Pass) → Vercel Build & Deploy
```

❌ **Incorreto (anterior):**
```
Push → GitHub Actions Tests → (Pass) → GitHub Actions Deploy → Vercel
                                      ↘ Vercel também faz deploy (duplicado)
```

## Arquivos Relacionados

- `.github/workflows/tests.yml` - Workflow de testes (✅ mantido)
- ~~`.github/workflows/deploy-vercel.yml`~~ - Removido (causava duplicação)
- `vercel.json` - Configuração da Vercel
- `scripts/vercel-ignore-build.sh` - Script para ignorar builds em branches específicas

## Links Úteis

- [Vercel Project Settings](https://vercel.com/flavio-lopes-projects-87104ba4/brazillian-cds-datafeeder-v2/settings)
- [GitHub Actions Secrets](https://github.com/ideiasfactory/brazillian_cds_datafeeder_v2/settings/secrets/actions)
- [Vercel Tokens](https://vercel.com/account/tokens)
