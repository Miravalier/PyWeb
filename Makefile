.PHONY: dev
dev:
	npm run dev


.PHONY: build
build:
	npm run build


.PHONY: clean
clean:
	@rm -rf dist
	@rm -f public/*.tgz
