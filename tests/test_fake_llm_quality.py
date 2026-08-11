from app.mock_llm import FakeLLM
from app.mock_rag import retrieve


def answer(question: str) -> str:
    docs = retrieve(question)
    prompt = f"Feature=qa\nDocs={' '.join(docs)}\nQuestion={question}"
    return FakeLLM().generate(prompt).text.lower()


def test_eval_refund_contains_required_facts() -> None:
    out = answer("What is your refund policy?")
    assert "7 days" in out
    assert "proof of purchase" in out


def test_eval_observability_contains_three_signals() -> None:
    out = answer("Explain why metrics traces and logs work together")
    assert "metrics" in out
    assert "traces" in out
    assert "logs" in out


def test_eval_logging_policy_mentions_pii_and_sensitive_data() -> None:
    out = answer("What should not appear in app logs?")
    assert "pii" in out
    assert "sensitive" in out
