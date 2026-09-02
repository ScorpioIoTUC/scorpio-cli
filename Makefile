PYTHON ?= python3
VERSION := $(shell sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml)
TAG ?= v$(VERSION)

.PHONY: help bootstrap clean build check check-clean check-gh test-pypi \
	publish-pypi tag github-release release

help:
	@echo "Scorpio CLI release commands"
	@echo ""
	@echo "  make bootstrap       Install build and upload tools"
	@echo "  make build           Build wheel and source distribution"
	@echo "  make check           Validate generated distributions"
	@echo "  make test-pypi       Upload the current version to TestPyPI"
	@echo "  make publish-pypi    Upload the current version to PyPI"
	@echo "  make tag             Create and push tag $(TAG)"
	@echo "  make github-release  Create GitHub release $(TAG)"
	@echo "  make release         Publish tag, GitHub release and PyPI package"

bootstrap:
	$(PYTHON) -m pip install --upgrade build twine

clean:
	rm -rf build dist scorpio_cli.egg-info

build: clean
	$(PYTHON) -m build

check:
	$(PYTHON) -m twine check dist/*

check-clean:
	@test -z "$$(git status --porcelain)" || \
		(echo "Error: commit or discard the pending changes first."; exit 1)

check-gh:
	@command -v gh >/dev/null || \
		(echo "Error: GitHub CLI is not installed."; exit 1)
	@gh api user >/dev/null || \
		(echo "Error: the active GitHub CLI account is not authenticated."; exit 1)
	@gh repo view ScorpioIoTUC/scorpio-cli >/dev/null || \
		(echo "Error: the active GitHub account cannot access ScorpioIoTUC/scorpio-cli."; exit 1)

test-pypi: build check
	$(PYTHON) -m twine upload --repository testpypi dist/*

publish-pypi: check-clean build check
	$(PYTHON) -m twine upload dist/*

tag: check-clean
	@! git rev-parse "$(TAG)" >/dev/null 2>&1 || \
		(echo "Error: tag $(TAG) already exists."; exit 1)
	git tag -a "$(TAG)" -m "Release $(TAG)"
	git push origin "$(TAG)"

github-release: check-clean check-gh build check
	@git rev-parse "$(TAG)" >/dev/null 2>&1 || \
		(echo "Error: create and push $(TAG) first with 'make tag'."; exit 1)
	@! gh release view "$(TAG)" >/dev/null 2>&1 || \
		(echo "Error: GitHub release $(TAG) already exists."; exit 1)
	gh release create "$(TAG)" dist/* \
		--verify-tag \
		--title "Scorpio CLI $(TAG)" \
		--generate-notes

release: check-clean check-gh build check
	@! git rev-parse "$(TAG)" >/dev/null 2>&1 || \
		(echo "Error: tag $(TAG) already exists. Increment the version first."; exit 1)
	git tag -a "$(TAG)" -m "Release $(TAG)"
	git push origin "$(TAG)"
	gh release create "$(TAG)" dist/* \
		--verify-tag \
		--title "Scorpio CLI $(TAG)" \
		--generate-notes
	$(PYTHON) -m twine upload dist/*

tailscale: 
	@echo "Starting Tailscale..."
	sudo tailscale up