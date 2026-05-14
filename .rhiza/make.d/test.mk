.PHONY: test

test:: install-uv ## run the repository tests
	@${UV_BIN} run --with pytest pytest tests
