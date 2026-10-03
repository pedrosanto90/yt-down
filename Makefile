.PHONY: run dev

run:
	uv run youtdown-web

dev:
	uv run youtdown-web --reload
