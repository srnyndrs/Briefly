PYTHON ?= python
CONTEXT ?= briefly

.PHONY: secrets-check secrets status

secrets-check:
	$(PYTHON) scripts/set_secrets.py --context $(CONTEXT) --validate-only

secrets:
	$(PYTHON) scripts/set_secrets.py --context $(CONTEXT)

status:
	kubectl --context $(CONTEXT) -n briefly get pods,deployments,statefulsets,pvc
