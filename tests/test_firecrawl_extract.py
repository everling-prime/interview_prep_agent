from tools.firecrawl import FirecrawlTool


class DummyExec:
    async def execute(self, *args, **kwargs):
        return {}


def test_extract_markdown_variants():
    fc = FirecrawlTool(DummyExec())

    # Direct string
    assert fc._extract_markdown("hello") == "hello"

    # Direct dict field
    assert fc._extract_markdown({"markdown": "md"}) == "md"

    # Nested dict
    assert fc._extract_markdown({"data": {"markdown": "md2"}}) == "md2"

    # List of items
    assert fc._extract_markdown({"data": [{"markdown": "md3"}]}) == "md3"

    # Fallback to content/text
    assert fc._extract_markdown({"content": "text"}) == "text"

