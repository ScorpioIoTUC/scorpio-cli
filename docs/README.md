# Development


Primero instala las herramientas:

```bash
make bootstrap
gh auth login
```

Para probar en TestPyPI:

```bash
make test-pypi
```

Para publicar solamente en PyPI:

```bash
make publish-pypi
```

Para crear solamente el tag y release de GitHub:

```bash
make tag
make github-release
```

Para realizar todo el release:

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