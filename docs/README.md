# Development


Primero instala las herramientas:

```bash
make bootstrap
gh auth login
```

El siguiente comando construye y publica la release en TestPyPI:

```bash
make test-pypi
```

El siguiente comando construye y publica la release en PyPI y GitHub. 

Primero, valida el tag a crear (si existe, aborta la publicación), para ello debes asegurarte de que no existan cambios sin confirmar y que la versión en `pyproject.toml` sea nueva. Segundo, sube los nuevos cambios y crea el release. 

```bash
make release
```

Ese último comando:

1. Verifica que no existan cambios sin confirmar.
2. Construye y valida el paquete.
3. Crea y sube el tag `v<version>`.
4. Crea la release de GitHub con wheel y source distribution.
5. Publica los archivos en PyPI.

Actualmente hay cambios pendientes:

```text
M  scorpio/cli/main.py
?? Makefile
```

Debes confirmarlos antes:

```bash
git add .
git commit -m "Add release workflow"
git push
```

Luego ejecuta `make release`. Para cada nueva publicación, incrementa primero la versión de `pyproject.toml`; PyPI y GitHub no permiten reutilizar una versión/tag existente.