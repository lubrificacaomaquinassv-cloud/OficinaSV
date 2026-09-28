# Oficina SV — novo app no Streamlit Cloud

## Numeração das OS (importante)

As OS ficam na tabela **ordem_servico** do Supabase — **não** no app.
Recriar o app **não apaga** OS antigas. O próximo número é lido do banco automaticamente.

## 1. Criar app novo no Streamlit Cloud

1. Acesse https://share.streamlit.io/
2. **Create app** → repositório `lubrificacaomaquinassv-cloud/oficina-sv-novo`
3. Branch: **main** | Main file: **app.py**
4. **Advanced settings** → Python **3.11**

## 2. Copiar Secrets do app antigo

Settings → Secrets → cole (mesmo conteúdo do OficinaSV antigo):

```toml
SUPABASE_URL = "https://azhpxhrwhegfysoeqmft.supabase.co"
SUPABASE_KEY = "sua-anon-key-aqui"
APP_PIN = ""
```

## 3. Deploy

Salve os Secrets → aguarde 1–2 min → abra a URL nova.

## 4. App antigo

O app `oficinasv-dytza2mqqtujkytuj7jgfm` pode ser **deletado** no Cloud depois que o novo funcionar.
