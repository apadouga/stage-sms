# stage-sms
Projet de stage 2° année BUT R&amp;T, envoie de sms sim868


# API `/receive`

**Méthode :** `POST`  
**Chemin :** `/receive`  
**Authentification :** Requise via en-tête `X-API-KEY`  
**Type de contenu requis :** `application/json`

---

## 1. Valeurs en entrée

### En-têtes HTTP requis

| Clé           | Valeur                  |
|---------------|--------------------------|
| Content-Type  | `application/json`       |
| X-API-KEY     | Votre clé API            |

---

### Corps JSON attendu

Deux types de requêtes sont possibles : avec un code (`type = "code"`) ou un message libre (`type = "msg"`).

#### Exemple 1 : type = "code"
```json
{
  "type": "code",
  "num": "0601020304",
  "confirmation_code": "123456"
}
```

#### Exemple 2 : type = "msg"
```json
{
  "type": "msg",
  "num": "0601020304",
  "message": "Votre message ici"
}
```

---

### Détail des champs

| Champ               | Type     | Obligatoire | Description                                          |
|---------------------|----------|-------------|------------------------------------------------------|
| `type`              | string   | Oui         | `"code"` ou `"msg"`                                  |
| `num`               | string   | Oui         | Numéro français, 10 chiffres commençant par `0`      |
| `confirmation_code` | string   | Oui si `type = "code"` | Code de 6 chiffres                        |
| `message`           | string   | Oui si `type = "msg"`  | Message texte libre                            |

---

## 2. Valeurs renvoyées

### Réponse en cas de succès – HTTP `200 OK`

```json
{
  "status": "success",
  "type": "code",
  "num": "0601020304",
  "message": "Code d'authentification :\n123456"
}
```

*Ou bien :*

```json
{
  "status": "success",
  "type": "msg",
  "num": "0601020304",
  "message": "Votre message ici"
}
```

---

### Réponses en cas d’erreur – HTTP `400 Bad Request`

| Cas d'erreur                                  | Exemple de message renvoyé                                                                 |
|-----------------------------------------------|---------------------------------------------------------------------------------------------|
| Mauvais type de contenu                       | `{"status":"error","errorType":"Invalid content type. JSON expected."}`                     |
| Champ `type` manquant ou invalide             | `{"status":"error","errorType":"Missing or invalid type field. Must be \"code\" or \"msg\"."}` |
| Champ `num` manquant ou invalide              | `{"status":"error","errorType":"Missing or invalid num field. Must be French format like 06XXXXXXXX."}` |
| Champ `confirmation_code` manquant ou invalide| `{"status":"error","errorType":"Missing or invalid confirmation_code format. Must be exactly 6 digits."}` |
| Champ `message` manquant                      | `{"status":"error","errorType":"Missing message field"}`                                     |
| Erreur technique                              | `{"status":"error","errorType":"Erreur technique ou message invalide"}`                     |

---

## 3. Exemples de requêtes `curl`

### Envoi d’un code
```bash
curl -X POST https://sms.ville-latronche.fr/receive 
-H "Content-Type: application/json" 
-H "X-API-KEY: table" 
-d "{\"type\": \"code\", \"confirmation_code\": \"123456\", \"num\": \"0783074093\"}"

```

### Envoi d’un message libre
```bash
curl -X POST https://sms.ville-latronche.fr/receive 
-H "Content-Type: application/json" 
-H "X-API-KEY: table" 
-d "{\"type\": \"msg\", \"message\": \"msg api\", \"num\": \"0783074093\"}"
```
