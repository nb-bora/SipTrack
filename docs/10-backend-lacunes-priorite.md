# Trois trous du backend — Priorité et impact

**Contexte :** Le frontend est maintenant aligné au contrat API exact. Ces trois lacunes du backend rendent le frontend moins confortable, mais la couche applicative a été écrite pour les surmonter. Voici comment les corriger.

---

## 1️⃣ CORS — **Blocage total** 🚨

### Symptôme
Quand tu lances le frontend en dev (localhost:5173) et le backend (localhost:8000), tout appel HTTP rencontre :
```
Access to XMLHttpRequest at 'http://127.0.0.1:8000/api/...' from origin 'http://localhost:5173'
has been blocked by CORS policy
```

### Pourquoi
Le navigateur refuse une requête cross-origin (origines différentes) si le serveur ne l'autorise pas avec l'en-tête `Access-Control-Allow-Origin`.

### Comment corriger

**Paquets :** Ajouter `django-cors-headers` à `Backend/pyproject.toml`
```toml
[project]
dependencies = [
    ...
    "django-cors-headers>=4.3.1",
]
```

**Settings :** Dans `Backend/config/settings/base.py` (ou dev.py) :

```python
# Après MIDDLEWARE = [...]
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # ← Ajouter, AVANT les autres
    "django.middleware.security.SecurityMiddleware",
    ...,
]

# En bas du fichier
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # dev local
    "http://127.0.0.1:5173",  # dev local (alt)
    "https://yourdomain.com",  # prod
]

# Optionnel mais recommandé en prod :
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = ["*"]
```

**Vérifier :** Les appels API doivent passer.

**Criticité :** 🔴 **BLOQUANT** — Rien ne marche sans ça.

---

## 2️⃣ `GET /api/services/?bar_id=...` — Query service

### Symptôme
Le frontend ne peut pas lister tous les services d'un bar, donc si tu changes de téléphone tu perds la trace du service en cours. Il faut copier l'ID manuellement dans les réglages.

### Pourquoi
Le backend expose `POST /api/services/` (ouvrir) et `GET /api/services/{id}/` (lire un), mais pas de liste. C'est une lacune du contrat API, pas une impossibilité technique.

### Comment corriger

C'est une **query service simple** — aucune règle métier. Modèle :

```python
# Backend/contexts/service_ventes/infrastructure/persistence/query_service.py


class DjangoServiceQueryService:
    def par_bar(self, bar_id: str) -> tuple[ServiceDTO, ...]:
        """Liste tous les services d'un bar, triés par date d'ouverture décroissante."""
        services = ServiceModel.objects.filter(bar_id=bar_id).order_by("-ouvert_le")
        return tuple(ServiceDTO.depuis(s) for s in services)
```

Ajouter une vue :

```python
# Backend/contexts/service_ventes/interface/rest/views.py


class ServiceListView(APIView):
    @extend_schema(
        tags=["Service & Ventes"],
        summary="Lister les services d'un bar",
        responses={200: ServiceOutputSerializer(many=True)},
    )
    def get(self, request: Request, bar_id: str) -> Response:
        exiger_lecture(request, bar_id=bar_id, operation="lister les services")
        services = container.services_du_bar(bar_id)
        return Response(ServiceOutputSerializer(services, many=True).data)
```

Enregistrer la route :

```python
# Backend/contexts/service_ventes/interface/rest/urls.py
urlpatterns = [
    path("bars/<str:bar_id>/services/", ServiceListView.as_view(), name="services-bar"),
    ...,
]
```

**Criticité :** 🟡 **Recommandé** — Améliore UX mais pas bloquant (localStorage pallie).

---

## 3️⃣ `GET /api/services/{id}/additions/` — Query service

### Symptôme
Pareil : le frontend ne peut pas lister toutes les additions d'un service, donc il se limite à celles ouvertes sur cet appareil.

### Pourquoi
Le backend expose `POST /api/services/{id}/additions/` (ouvrir) et `GET .../additions/{aid}/` (lire une), mais pas de liste.

### Comment corriger

Query service :

```python
# Backend/contexts/service_ventes/infrastructure/persistence/query_service.py


class DjangoAdditionQueryService:
    def par_service(self, service_id: str) -> tuple[AdditionDTO, ...]:
        """Liste toutes les additions d'un service, triées par table_numero."""
        additions = AdditionModel.objects.filter(service_id=service_id).order_by(
            "table_numero"
        )
        return tuple(AdditionDTO.depuis(a) for a in additions)
```

Vue :

```python
# Backend/contexts/service_ventes/interface/rest/views.py


class AdditionListView(APIView):
    @extend_schema(
        tags=["Service & Ventes"],
        summary="Lister les additions d'un service",
        responses={200: AdditionOutputSerializer(many=True)},
    )
    def get(self, request: Request, service_id: str) -> Response:
        exiger_lecture(
            request,
            bar_id=bar_du_service(service_id),
            operation="lister les additions",
        )
        additions = container.additions_du_service(service_id)
        return Response(AdditionOutputSerializer(additions, many=True).data)
```

Route :

```python
# Backend/contexts/service_ventes/interface/rest/urls.py
urlpatterns = [
    path(
        "services/<str:service_id>/additions/",
        AdditionListView.as_view(),
        name="additions-service",
    ),
    ...,
]
```

**Criticité :** 🟡 **Recommandé** — Même chose.

---

## 4️⃣ (Bonus) Enrichir `/api/auth/jeton/` 

### Contexte actuel
L'endpoint rend seulement `{ "token": "..." }`. Le frontend ne connaît donc pas les capacités de l'utilisatrice, donc affiche tous les boutons et traite les `403` comme normaux.

### Améliorante future
Enrichir pour rendre aussi les capacités :

```python
# Pseudocode : /api/auth/jeton/ → 200 { token, utilisateur_id, capacites }
```

Cela permettrait au frontend de masquer les boutons interdits **avant** le clic, au lieu d'attendre le `403`.

**Criticité :** 🟢 **Nice-to-have** — L'UX fonctionne aujourd'hui sans ça.

---

## 📋 Ordre de correction conseillé

| # | Trou | Effort | Impact | Urgence |
|---|------|--------|--------|---------|
| 1 | CORS | 5 min | Débloque tout | 🔴 FAIRE D'ABORD |
| 2 | `/services/?bar_id=...` | 30 min | UX améliorée | 🟡 Après CORS |
| 3 | `/services/{id}/additions/` | 30 min | UX améliorée | 🟡 Après CORS |
| 4 | Enrichir jeton | 45 min | UX polish | 🟢 Quand tu veux |

---

## ✅ Checklist avant prod

- [ ] CORS configuré pour frontend domain
- [ ] `/services/?bar_id=...` implémentée (optionnel)
- [ ] `/services/{id}/additions/` implémentée (optionnel)
- [ ] Frontend teste avec réel backend
- [ ] Double-clics idempotents (pas de doublon dans le journal)
- [ ] 401 renvoie bien à la connexion et oublie le bar
- [ ] Montants s'affichent en `12 500 FCFA`
- [ ] Langues : français partout, pas d'anglais UI

---

## 💬 Contacts

- **Backend doc :** `Backend/docs/INDEX.md`
- **Frontend doc :** `Frontend/README.md`
- **Contrat API :** Voir le prompt Lovable au début de `HARMONISATION-FRONTEND.md`
