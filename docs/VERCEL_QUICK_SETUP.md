# Guia Rápido: Deploy Vercel com CI/CD

## ⚡ Setup em 5 Minutos

### 1. Obter Secrets da Vercel

```bash
# Instalar Vercel CLI
npm install -g vercel

# Login e link do projeto
vercel login
vercel link

# Ver os IDs (copie estes valores)
cat .vercel/project.json
```

### 2. Criar Token da Vercel

1. Acesse: https://vercel.com/account/tokens
2. Crie um novo token
3. Copie o token

### 3. Adicionar Secrets no GitHub

Vá em: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Adicione estes 3 secrets:
- `VERCEL_TOKEN` → Token que você copiou
- `VERCEL_ORG_ID` → Do arquivo `.vercel/project.json`
- `VERCEL_PROJECT_ID` → Do arquivo `.vercel/project.json`

### 4. Desabilitar Deploy Automático da Vercel

**✅ Já configurado!** O arquivo `vercel.json` já contém:

```json
{
  "github": {
    "deploymentEnabled": {
      "master": false,
      "main": false
    }
  }
}
```

Isso desabilita o deploy automático da Vercel para os branches master/main, permitindo que apenas o GitHub Actions faça o deploy.

### 5. Commit e Push

```bash
git add .github/workflows/deploy-vercel.yml
git commit -m "ci: add Vercel deploy workflow with CI/CD"
git push origin master
```

## 🎯 Como Funciona

1. **Push** → Dispara workflow `Tests`
2. **Tests passa** → Dispara workflow `Deploy to Vercel` automaticamente
3. **Tests falha** → Deploy é bloqueado ❌

## ✅ Verificar Funcionamento

1. Acesse `Actions` no GitHub
2. Faça um push no master
3. Você deve ver dois workflows executando em sequência:
   - ✅ Tests (primeiro)
   - ✅ Deploy to Vercel (depois, só se Tests passar)

## 📚 Documentação Completa

Veja `docs/VERCEL_CI_CD.md` para mais detalhes e troubleshooting.
